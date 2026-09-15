from fastmcp import FastMCP
from typing import Any, Dict, List
from phase_1 import fetch_official_json, normalize_events


# Create the MCP server
mcp = FastMCP("Forex Factory MCP")


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


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8001,
    )