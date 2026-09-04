"""FastMCP + FastAPI server for Forex Factory."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastmcp import FastMCP

from config import OUTPUT_DIR
from scrapper import get_complete_calendar


# ============================================================
# FastMCP Server
# ============================================================

mcp = FastMCP("Forex Factory Calendar")

BASE_DIR = Path(__file__).parent
THIS_WEEK_JSON = BASE_DIR / "data" / "test_output.json"


def load_events_json() -> list[dict]:
    with open(THIS_WEEK_JSON, "r", encoding="utf-8") as file:
        return json.load(file)


@mcp.resource(
    "events://all",
    name="Forex Factory Events",
    description="Forex Factory economic calendar events for the current week",
    mime_type="application/json",
)
def get_events() -> str:
    """Return the Forex Factory events as JSON."""

    events = load_events_json()

    return json.dumps(
        events,
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
async def get_forex_calendar(
    save_to_file: bool = True,
    output_filename: Optional[str] = None,
) -> str:
    """
    Get Forex Factory economic calendar for current week with full details.
    """

    try:
        data = await asyncio.to_thread(get_complete_calendar)

        if save_to_file:
            filename = (
                output_filename
                or f"forex_calendar_{datetime.now().strftime('%Y-%m-%d')}.json"
            )

            filepath = OUTPUT_DIR / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            data["saved_to"] = str(filepath.absolute())

        return json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_calendar_stats() -> str:
    """
    Get statistics about the current calendar data.
    """

    try:
        data = await asyncio.to_thread(get_complete_calendar)

        total = data["total_events"]

        high_impact = sum(
            1
            for e in data["events"]
            if e.get("impact") == "High"
        )

        medium_impact = sum(
            1
            for e in data["events"]
            if e.get("impact") == "Medium"
        )

        low_impact = sum(
            1
            for e in data["events"]
            if e.get("impact") == "Low"
        )

        stats = {
            "total_events": total,
            "high_impact": high_impact,
            "medium_impact": medium_impact,
            "low_impact": low_impact,
            "events_with_news": data["events_with_news"],
            "fetched_at": data["fetched_at"],
        }

        return json.dumps(stats, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================
# FastAPI
# ============================================================

mcp_app = mcp.http_app(path="/")

app = FastAPI(
    title="Forex Factory MCP API",
    description="Forex Factory calendar exposed through FastAPI and MCP",
    version="1.0.0",
    lifespan=mcp_app.lifespan,
)


@app.get("/")
async def root():
    return {
        "name": "Forex Factory MCP API",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


# Mount MCP
app.mount("/mcp", mcp_app)