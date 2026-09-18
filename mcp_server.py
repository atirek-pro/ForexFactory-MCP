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

# Create the MCP server
mcp = FastMCP("Forex Factory MCP")

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
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8001,
    )