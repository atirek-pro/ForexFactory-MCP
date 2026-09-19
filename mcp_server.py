import os
from fastmcp import FastMCP
# from fastmcp_tasks import TasksExtension
from typing import Any, Dict, List
from phase_1 import fetch_official_json, normalize_events
from phase_2 import ( 
    load_phase1_data, 
    fetch_calendar_html, 
    parse_calendar_html, 
    save_data 
)
import psycopg
from dotenv import load_dotenv

load_dotenv

NEON_DATABASE_URL = os.environ["NEON_DATABASE_URL"]

# Create the MCP server
mcp = FastMCP("Forex Factory MCP")

# DATABASE
def get_db_connection():
    """
    Create a connection to the Neon PostgreSQL database.
    """
    return psycopg.connect(NEON_DATABASE_URL)

def initialize_database():
    """
    Create the required database tables if they do not exist.
    """

    print("[DB] Connecting to Neon PostgreSQL...")

    with get_db_connection() as conn:
        with conn.cursor() as cur:

            # ------------------------------------------------
            # Phase 1 events
            # ------------------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS forex_calendar_events (
                    id SERIAL PRIMARY KEY,

                    event_date TEXT,
                    event_time TEXT,
                    currency TEXT,
                    impact TEXT,
                    event TEXT,

                    actual TEXT,
                    forecast TEXT,
                    previous TEXT,

                    event_id TEXT,
                    event_url TEXT,

                    source TEXT NOT NULL DEFAULT 'phase_1',

                    fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # ------------------------------------------------
            # Phase 2 events
            # ------------------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS forex_event_details (
                    id SERIAL PRIMARY KEY,

                    event_date TEXT,
                    event_time TEXT,
                    currency TEXT,
                    impact TEXT,
                    event TEXT,

                    actual TEXT,
                    forecast TEXT,
                    previous TEXT,

                    event_id TEXT,
                    event_url TEXT,

                    source TEXT NOT NULL DEFAULT 'phase_2',

                    fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        conn.commit()

    print("[DB] Neon database initialized successfully.")

# DATABASE INSERT HELPERS
def save_phase1_events(events: List[Dict[str, Any]]):
    """
    Persist Phase 1 calendar events into Neon.
    """

    if not events:
        print("[DB] No Phase 1 events to store.")
        return

    print(f"[DB] Persisting {len(events)} Phase 1 events...")

    with get_db_connection() as conn:
        with conn.cursor() as cur:

            for event in events:

                cur.execute(
                    """
                    INSERT INTO forex_calendar_events (
                        event_date,
                        event_time,
                        currency,
                        impact,
                        event,
                        actual,
                        forecast,
                        previous,
                        event_id,
                        event_url
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    );
                    """,
                    (
                        event.get("date"),
                        event.get("time"),
                        event.get("currency"),
                        event.get("impact"),
                        event.get("event"),
                        event.get("actual"),
                        event.get("forecast"),
                        event.get("previous"),
                        event.get("event_id"),
                        event.get("event_url"),
                    ),
                )

        conn.commit()

    print(
        f"[DB] Successfully stored "
        f"{len(events)} Phase 1 events."
    )


def save_phase2_events(events: List[Dict[str, Any]]):
    """
    Persist Phase 2 detailed events into Neon.
    """

    if not events:
        print("[DB] No Phase 2 events to store.")
        return

    print(f"[DB] Persisting {len(events)} Phase 2 events...")

    with get_db_connection() as conn:
        with conn.cursor() as cur:

            for event in events:

                cur.execute(
                    """
                    INSERT INTO forex_event_details (
                        event_date,
                        event_time,
                        currency,
                        impact,
                        event,
                        actual,
                        forecast,
                        previous,
                        event_id,
                        event_url
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    );
                    """,
                    (
                        event.get("date"),
                        event.get("time"),
                        event.get("currency"),
                        event.get("impact"),
                        event.get("event"),
                        event.get("actual"),
                        event.get("forecast"),
                        event.get("previous"),
                        event.get("event_id"),
                        event.get("event_url"),
                    ),
                )

        conn.commit()

    print(
        f"[DB] Successfully stored "
        f"{len(events)} Phase 2 events."
    )

# Enable MCP background task support 
# mcp.add_extension(TasksExtension())

@mcp.tool()
def get_forex_calendar() -> List[Dict[str, Any]]:
    """
    Fetch the current weekly Forex Factory economic calendar
    and return normalized event data.
    """

    # 1. Fetch raw data from the official JSON feed
    raw_events = fetch_official_json()

    # 2. Normalize the raw events into our standard structure
    normalized_events = normalize_events(raw_events)

    # 3. Return the formatted data through MCP
    return normalized_events

# PHASE 2 TOOL
@mcp.tool()
async def get_forex_event_details() -> List[Dict[str, Any]]:
    """ Run Phase 2 of the Forex Factory scraper. 
    This is a long-running background operation that fetches the Forex Factory calendar HTML and extracts detailed 
    event information including: 
        - Date 
        - Time 
        - Currency 
        - Impact 
        - Event name 
        - Actual value 
        - Forecast value 
        - Previous value 
        - Event ID 
        - Event URL 
    Use this tool when detailed Forex Factory event information is required beyond the basic Phase 1 calendar data. 
    
    This operation can take approximately 1-2 minutes. 
    """ 
    print("\n" + "=" * 70) 
    print("FOREX FACTORY MCP - PHASE 2 STARTED") 
    print("=" * 70) 

    # Step 1: Load Phase 1 data
    phase1_events = load_phase1_data()
    print( f"[PHASE 2 MCP] Loaded " f"{len(phase1_events)} Phase 1 events" )

    # Step 2: Fetch Forex Factory HTML
    html = fetch_calendar_html()

    if not html: 
        raise RuntimeError( "Could not fetch Forex Factory calendar HTML." )

    # Step 3: Parse detailed event information
    html_events = parse_calendar_html(html)

    # Step 4: Return detailed events to the MCP client
    return html_events

# SERVER
if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("STARTING FOREX FACTORY MCP SERVER")
    print("=" * 70)

    print("[SERVER] Initializing Neon database...")

    initialize_database()

    print("[SERVER] MCP tools:")
    print("  - get_forex_calendar")
    print("  - get_forex_event_details")

    print("[SERVER] Transport: HTTP")
    print("[SERVER] Host: 127.0.0.1")
    print("[SERVER] Port: 8001")

    print("=" * 70)
    print("🔥 MCP SERVER READY")
    print("=" * 70 + "\n")

    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8001,
    )