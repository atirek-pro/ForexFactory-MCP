import json
import requests
from datetime import datetime
from typing import Any, Dict, List


# CONFIGURATION

FOREX_FACTORY_JSON_URL = (
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
)

OUTPUT_FILE = "phase_1_data.json"
REQUEST_TIMEOUT = 30


# SESSION
session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
})


# FETCH OFFICIAL JSON
def fetch_official_json() -> List[Dict[str, Any]]:
    """Fetch the official Forex Factory weekly JSON feed."""

    print("\n[PHASE 1] Fetching official Forex Factory JSON...")

    try:
        response = session.get(
            FOREX_FACTORY_JSON_URL,
            timeout=REQUEST_TIMEOUT,
        )

        print(f"[PHASE 1] HTTP status: {response.status_code}")

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise ValueError("Unexpected JSON structure")

        print(f"[PHASE 1] Received {len(data)} events")

        return data

    except Exception as exc:
        print(f"[PHASE 1] Failed: {exc}")
        return []


# NORMALIZE EVENTS
def normalize_events(
    events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Normalize events from the official JSON feed."""

    normalized = []

    for event in events:
        raw_date = event.get("date")

        if not raw_date:
            continue

        try:
            dt = datetime.fromisoformat(raw_date)

            date = dt.strftime("%Y-%m-%d")
            time_value = dt.strftime("%H:%M")

        except ValueError:
            date = raw_date
            time_value = None

        normalized.append({
            "date": date,
            "time": time_value,
            "currency": event.get("country"),
            "impact": event.get("impact"),
            "event": (
                event.get("title")
                or event.get("event")
                or event.get("name")
            ),
            "actual": event.get("actual"),
            "forecast": event.get("forecast"),
            "previous": event.get("previous"),
        })

    return normalized


# SAVE
def save_data(events: List[Dict[str, Any]]) -> None:
    """Save Phase 1 data."""

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            events,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(f"\n[PHASE 1] Saved {len(events)} events")
    print(f"[PHASE 1] Output: {OUTPUT_FILE}")


# MAIN
def main() -> None:
    print("=" * 70)
    print("FOREX FACTORY SCRAPER - PHASE 1")
    print("=" * 70)

    raw_data = fetch_official_json()

    if not raw_data:
        raise RuntimeError(
            "Could not fetch official Forex Factory JSON."
        )

    normalized_data = normalize_events(raw_data)

    save_data(normalized_data)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nStopped by user.")

    except Exception as exc:
        print(f"\n[FATAL] {exc}")
