"""Configuration for Forex Factory FastMCP."""

from pathlib import Path

# URLs
CALENDAR_JSON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_HTML_URL = "https://www.forexfactory.com/calendar"
DETAIL_URL = "https://www.forexfactory.com/calendar/details/1-{}"

# Paths
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

# Rate limiting
REQUEST_DELAY = 1.5

# Which events to fetch news for (None = all)
DETAIL_IMPACTS = None

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}