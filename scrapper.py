"""All scraping and data fetching logic."""

import json
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from config import (
    CALENDAR_JSON_URL,
    CALENDAR_HTML_URL,
    DETAIL_URL,
    DETAIL_IMPACTS,
    HEADERS,
    REQUEST_DELAY,
)

# Create session once and reuse
session = requests.Session()
session.headers.update(HEADERS)


def fetch_calendar_json():
    """Fetch calendar data from Forex Factory JSON API."""
    response = session.get(CALENDAR_JSON_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_calendar_html():
    """Fetch calendar HTML from Forex Factory."""
    response = session.get(CALENDAR_HTML_URL, timeout=30)
    response.raise_for_status()
    return response.text


def clean_text(element):
    """Extract clean text from BeautifulSoup element."""
    if not element:
        return None
    text = element.get_text(" ", strip=True)
    return text or None


def normalize_text(value):
    """Normalize text for comparison."""
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def parse_impact(row):
    """Parse impact level from HTML row."""
    impact_element = row.select_one("td.calendar__impact")
    if not impact_element:
        return None

    # Check title attributes first
    for element in [impact_element, *impact_element.select("[title]")]:
        title = element.get("title")
        if not title:
            continue
        title_lower = title.lower()
        if "high" in title_lower:
            return "High"
        if "medium" in title_lower:
            return "Medium"
        if "low" in title_lower:
            return "Low"
        if "holiday" in title_lower:
            return "Holiday"
        if "non-economic" in title_lower:
            return "Non-Economic"

    # Fallback to classes
    classes = " ".join(impact_element.get("class", [])).lower()
    if "high" in classes:
        return "High"
    if "medium" in classes:
        return "Medium"
    if "low" in classes:
        return "Low"
    return None


def extract_absolute_url(element):
    """Extract absolute URL from element."""
    if not element:
        return None
    link = element.find("a", href=True)
    if not link:
        return None
    href = link.get("href")
    if not href:
        return None
    if href.startswith("/"):
        return "https://www.forexfactory.com" + href
    return href


def parse_calendar_html(html):
    """Parse calendar HTML to extract event IDs."""
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.calendar__row")

    scraped_events = []
    current_date = None

    for row in rows:
        # Skip grey/historical rows
        if "calendar__row--grey" in row.get("class", []):
            continue

        event_id = row.get("data-event-id") or row.get("data-eventid")
        if not event_id:
            continue
        event_id = str(event_id)

        # Date (carry forward if not present)
        date_element = row.select_one("td.calendar__date")
        date = clean_text(date_element)
        if date:
            current_date = date

        # Extract all fields
        time_element = row.select_one("td.calendar__time")
        event_time = clean_text(time_element)

        currency_element = row.select_one("td.calendar__currency")
        currency = clean_text(currency_element)

        impact = parse_impact(row)

        event_element = row.select_one(".calendar__event-title") or row.select_one(".calendar__event")
        event_title = clean_text(event_element)
        event_url = extract_absolute_url(event_element)

        actual_element = row.select_one("td.calendar__actual")
        actual = clean_text(actual_element)

        forecast_element = row.select_one("td.calendar__forecast")
        forecast = clean_text(forecast_element)

        previous_element = row.select_one("td.calendar__previous")
        previous = clean_text(previous_element)

        graph_url = None
        graph_element = row.select_one(".calendar__graph")
        if graph_element:
            graph_url = extract_absolute_url(graph_element)

        scraped_events.append({
            "event_id": event_id,
            "date": date or current_date,
            "time": event_time,
            "currency": currency,
            "impact": impact,
            "event": event_title,
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
            "event_url": event_url,
            "graph_url": graph_url,
        })

    return scraped_events


def match_events(json_events, html_events):
    """Match JSON events with HTML events to get event IDs."""
    # Build lookup by (currency, event_name)
    html_lookup = {}
    for html_event in html_events:
        key = (
            normalize_text(html_event.get("currency")),
            normalize_text(html_event.get("event"))
        )
        html_lookup.setdefault(key, []).append(html_event)

    for event in json_events:
        key = (
            normalize_text(event.get("currency")),
            normalize_text(event.get("event"))
        )
        candidates = html_lookup.get(key, [])

        if not candidates:
            continue

        # Use exact match or fallback to first
        if len(candidates) == 1:
            html_event = candidates[0]
        else:
            # Try to match by forecast + previous
            selected = None
            json_forecast = normalize_text(event.get("forecast"))
            json_previous = normalize_text(event.get("previous"))

            for candidate in candidates:
                if (normalize_text(candidate.get("forecast")) == json_forecast and
                    normalize_text(candidate.get("previous")) == json_previous):
                    selected = candidate
                    break

            html_event = selected if selected else candidates[0]

        # Merge data
        event["event_id"] = html_event.get("event_id")
        if html_event.get("actual"):
            event["actual"] = html_event.get("actual")
        event["event_url"] = html_event.get("event_url")
        event["graph_url"] = html_event.get("graph_url")

    return json_events


def fetch_event_news(event_id):
    """Fetch detailed news for a single event."""
    if not event_id:
        return None

    url = DETAIL_URL.format(event_id)
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"News request failed: {e}"}


def fetch_news_for_events(events):
    """Fetch news for all eligible events."""
    # Filter events that need news
    events_to_fetch = []
    for event in events:
        if DETAIL_IMPACTS is not None and event.get("impact") not in DETAIL_IMPACTS:
            continue
        if not event.get("event_id"):
            continue
        events_to_fetch.append(event)

    news_count = 0
    for event in tqdm(events_to_fetch, desc="Fetching news", unit="event"):
        news = fetch_event_news(event.get("event_id"))
        if news and "error" not in news:
            event["news"] = news
            news_count += 1
        else:
            event["news"] = None
        time.sleep(REQUEST_DELAY)

    return news_count


def get_complete_calendar():
    """Main function - fetches and combines all data."""
    # 1. Get JSON data
    raw_events = fetch_calendar_json()

    # 2. Normalize JSON events
    events = []
    for raw in raw_events:
        events.append({
            "event_id": None,
            "datetime": raw.get("date"),
            "timestamp": raw.get("timestamp"),
            "currency": raw.get("country"),
            "impact": raw.get("impact"),
            "event": raw.get("title"),
            "actual": raw.get("actual") or None,
            "forecast": raw.get("forecast") or None,
            "previous": raw.get("previous") or None,
            "event_url": None,
            "graph_url": None,
            "news": None
        })

    # 3. Get HTML data (for event IDs)
    html = fetch_calendar_html()
    html_events = parse_calendar_html(html)

    # 4. Match and merge
    events = match_events(events, html_events)

    # 5. Fetch news
    news_count = fetch_news_for_events(events)

    # 6. Build output
    return {
        "source": "Forex Factory",
        "fetched_at": datetime.now().astimezone().isoformat(),
        "total_events": len(events),
        "events_with_event_id": sum(1 for e in events if e.get("event_id")),
        "events_with_news": news_count,
        "events": events
    }