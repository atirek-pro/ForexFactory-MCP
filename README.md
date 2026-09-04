# 📊 Forex Factory Calendar MCP

> A Python-based Forex Factory economic calendar collector and **MCP server** that transforms Forex Factory's weekly calendar data into structured, enriched event data for AI agents.

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-4.0.2-purple)](https://gofastmcp.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-HTTP%20API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/Protocol-MCP-orange)](https://modelcontextprotocol.io/)

---

## 🚀 Overview

**Forex Factory Calendar MCP** collects economic calendar data from Forex Factory, enriches events with detailed information, stores the resulting dataset as JSON, and exposes the data through the **Model Context Protocol (MCP)**.

The project combines:

- 📥 Forex Factory weekly JSON data
- 🌐 Forex Factory calendar HTML
- 🔎 Event ID extraction
- 🧩 Event matching and enrichment
- 📰 Event detail information
- 💾 Structured JSON output
- 🔌 MCP tools
- 📚 MCP resources
- ⚡ FastAPI HTTP transport

The goal is to make Forex Factory economic-calendar data easily consumable by **AI agents and MCP-compatible applications**.

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │    Forex Factory     │
                         └──────────┬───────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
                   ▼                                 ▼
        Weekly Calendar JSON                 Calendar HTML
                   │                                 │
                   ▼                                 ▼
           Basic Events                     Event IDs / Metadata
                   │                                 │
                   └────────────────┬────────────────┘
                                    ▼
                           Event Matching
                                    │
                                    ▼
                         Event Detail Endpoint
                                    │
                                    ▼
                          Enriched Event Dataset
                                    │
                                    ▼
                         ┌────────────────────┐
                         │     JSON Store     │
                         │      /data         │
                         └─────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
              FastMCP Tools                 MCP Resource
                    │                             │
                    │                             │
                    ▼                             ▼
          get_forex_calendar()             events://all
          get_calendar_stats()
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                              MCP Client
                                   │
                                   ▼
                              AI Agent
```

---

# ✨ Features

| Feature            | Description                                         |
| ------------------ | --------------------------------------------------- |
| 📅 Weekly Calendar | Fetches Forex Factory's current-week calendar       |
| 🌐 HTML Parsing    | Extracts event IDs and additional metadata          |
| 🔗 Event Matching  | Matches JSON events with HTML calendar rows         |
| 📰 Event Details   | Fetches detailed information for identified events  |
| 💾 JSON Storage    | Saves the enriched calendar locally                 |
| 🔧 Configurable    | Supports detail-impact filtering and request delays |
| 🔌 MCP Tools       | Exposes calendar operations as MCP tools            |
| 📚 MCP Resource    | Exposes calendar data through `events://all`        |
| ⚡ FastAPI         | Makes the MCP server available over HTTP            |
| 🧪 Inspectable     | Supports FastMCP inspection and CLI testing         |

---

# 🔄 Data Collection Pipeline

The collector currently follows this pipeline:

```text
1. Fetch Weekly JSON
        │
        ▼
2. Normalize Calendar Events
        │
        ▼
3. Fetch Calendar HTML
        │
        ▼
4. Parse Calendar Rows
        │
        ▼
5. Extract Event IDs
        │
        ▼
6. Match HTML ↔ JSON Events
        │
        ▼
7. Fetch Event Details
        │
        ▼
8. Enrich Events
        │
        ▼
9. Save JSON Dataset
```

---

# 📡 Data Sources

## 1. Forex Factory Weekly JSON

The initial calendar data is fetched from:

```text
https://nfs.faireconomy.media/ff_calendar_thisweek.json
```

The feed provides fields such as:

- Date / time
- Currency
- Impact
- Event title
- Actual
- Forecast
- Previous

---

## 2. Forex Factory Calendar HTML

The collector also requests:

```text
https://www.forexfactory.com/calendar
```

The HTML is required because the weekly JSON feed does not currently provide the Forex Factory `event_id`.

The parser looks for calendar rows containing:

```html
<tr class="calendar__row" data-event-id="..."></tr>
```

The extracted event ID is then associated with the normalized calendar event.

---

## 3. Event Details

Once an event ID has been identified, the collector requests:

```text
https://www.forexfactory.com/calendar/details/1-{event_id}
```

The response can contain information such as:

- Event specifications
- Description
- Source
- Speaker
- Usual Effect
- FF Notes
- Why Traders Care
- Historical information
- Linked discussion threads

The current implementation stores the raw detail response under the event's `news` field.

---

# 📦 Output

Generated calendar files are stored inside:

```text
data/
```

The current tool generates files using:

```text
forex_calendar_YYYY-MM-DD.json
```

Example:

```text
data/
└── forex_calendar_2026-09-04.json
```

A typical top-level response looks like:

```json
{
  "source": "Forex Factory",
  "fetched_at": "...",
  "total_events": 0,
  "events_with_event_id": 0,
  "events_with_news": 0,
  "events": []
}
```

### Event Structure

```json
{
  "event_id": "146911",
  "datetime": "2026-09-04T12:30:00-04:00",
  "timestamp": "2026-09-04T16:30:00+00:00",
  "currency": "USD",
  "impact": "High",
  "event": "Non-Farm Employment Change",
  "actual": null,
  "forecast": "75K",
  "previous": "73K",
  "event_url": null,
  "graph_url": null,
  "news": {}
}
```

---

# 🔌 MCP Integration

The project now exposes the collector through **FastMCP**.

The MCP layer currently provides:

### 🛠️ Tools

#### `get_forex_calendar`

Fetches the complete current-week Forex Factory calendar.

Parameters:

```text
save_to_file: bool = True
output_filename: str | None = None
```

Example:

```text
get_forex_calendar(save_to_file=true)
```

---

#### `get_calendar_stats`

Returns summary statistics for the current calendar.

Example response:

```json
{
  "total_events": 113,
  "high_impact": 25,
  "medium_impact": 41,
  "low_impact": 47,
  "events_with_news": 45,
  "fetched_at": "..."
}
```

---

# 📚 MCP Resources

The server currently exposes one MCP resource:

```text
events://all
```

This resource provides the calendar dataset as JSON.

Conceptually:

```text
MCP Client
     │
     │ resources/list
     ▼
events://all
     │
     │ resources/read
     ▼
Calendar JSON
```

The resource is declared using:

```python
@mcp.resource(
    "events://all",
    name="Forex Factory Events",
    description="Forex Factory economic calendar events for the current week",
    mime_type="application/json",
)
def get_events() -> str:
    ...
```

> **Note:** The current test implementation reads `data/test_output.json`, while `get_forex_calendar()` currently generates `forex_calendar_YYYY-MM-DD.json`. These should be unified so `events://all` always exposes the latest generated dataset.

---

# ⚡ FastAPI Integration

FastMCP is exposed through FastAPI using Streamable HTTP.

The architecture is:

```text
                    FastAPI
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
       /health                     /mcp
                                    │
                                    ▼
                                 FastMCP
                              ┌─────┴─────┐
                              │           │
                              ▼           ▼
                            Tools      Resources
```

The MCP HTTP application is mounted under:

```text
/mcp
```

Resulting endpoint:

```text
http://127.0.0.1:8000/mcp
```

---

# 🧰 Installation

Clone the project and create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install requests beautifulsoup4 tqdm fastmcp fastapi uvicorn
```

---

# ▶️ Running the Server

## Run FastAPI + MCP

Start the HTTP server with:

```bash
uvicorn server:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

> `/mcp` is an MCP protocol endpoint and should be accessed by an MCP client rather than treated as a normal browser page.

---

# 🧪 Testing

## Inspect the local MCP server

```bash
fastmcp inspect server.py
```

For the complete FastMCP representation:

```bash
fastmcp inspect server.py --format fastmcp
```

---

## List MCP tools

```bash
fastmcp list http://127.0.0.1:8000/mcp
```

Expected:

```text
Tools (2)

  get_forex_calendar(...)
  get_calendar_stats()
```

---

## List tools + resources

Use:

```bash
fastmcp list http://127.0.0.1:8000/mcp --resources
```

Expected resources include:

```text
events://all
```

For machine-readable output:

```bash
fastmcp list http://127.0.0.1:8000/mcp --resources --json
```

---

# 📁 Project Structure

```text
Forex-Factory-MCP/
│
├── server.py
│   ├── FastMCP server
│   ├── MCP tools
│   ├── MCP resources
│   └── FastAPI application
│
├── scrapper.py
│   ├── Calendar JSON collection
│   ├── Calendar HTML parsing
│   ├── Event matching
│   └── Event detail enrichment
│
├── config.py
│   ├── URLs
│   ├── Request delay
│   ├── Detail impact configuration
│   ├── HTTP headers
│   └── Output directory
│
├── data/
│   └── Generated calendar JSON files
│
├── README.md
│
└── .venv/
```

---

# ⚙️ Configuration

Configuration is centralized in `config.py`.

### Request Delay

```python
REQUEST_DELAY = 1.5
```

This introduces a delay between requests to avoid making requests too aggressively.

### Detail Impact Filter

```python
DETAIL_IMPACTS = None
```

Current behavior:

```text
None
 ↓
Fetch details for every event with an event_id
```

You can restrict detail fetching:

```python
DETAIL_IMPACTS = {"High"}
```

or:

```python
DETAIL_IMPACTS = {"High", "Medium"}
```

---

# ⚠️ Current Limitations

## Event ID Matching

The biggest current limitation is matching the weekly JSON events against the HTML calendar.

The pipeline currently relies on:

```text
Weekly JSON
     ↕
Calendar HTML
```

A typical run can produce:

```text
Fetched 113 events from JSON feed
Found 121 calendar HTML rows
Extracted 45 events with event IDs

Matched:   45
Unmatched: 68
```

Events without an `event_id` cannot currently receive detailed event information.

Improving event-ID resolution is therefore a major priority.

---

## Fixed Weekly Source

The current JSON source is:

```text
ff_calendar_thisweek.json
```

Therefore, the collector currently relies on Forex Factory's definition of **"this week"** rather than accepting arbitrary date ranges.

---

## Calendar URL

The HTML collector currently uses:

```text
https://www.forexfactory.com/calendar
```

A future implementation should use an explicit date-range URL.

---

## Timezone Handling

Timezone handling is not yet exposed as an input to the MCP tools.

Future versions are expected to support IANA timezone names such as:

```text
Asia/Kolkata
America/New_York
Europe/London
Asia/Tokyo
UTC
```

---

## Resource/Data Synchronization

The current MCP resource reads:

```text
data/test_output.json
```

while the calendar tool generates:

```text
data/forex_calendar_YYYY-MM-DD.json
```

This is temporary and should be changed so the resource always points to the latest generated weekly dataset.

---

# 🗺️ Roadmap

## 🔴 High Priority

- [ ] Improve JSON ↔ HTML event matching
- [ ] Make event IDs the primary downstream identifier
- [ ] Use explicit Forex Factory date-range URLs
- [ ] Unify MCP resource with the latest generated JSON
- [ ] Improve timezone-aware date handling
- [ ] Improve HTTP error handling
- [ ] Add retry/backoff behavior
- [ ] Handle malformed Forex Factory responses gracefully

## 🟡 MCP Layer

- [x] Implement FastMCP
- [x] Add `get_forex_calendar`
- [x] Add `get_calendar_stats`
- [x] Add `events://all` resource
- [x] Expose MCP through FastAPI
- [ ] Improve resource/data synchronization
- [ ] Add timezone-aware inputs
- [ ] Add date-range support
- [ ] Improve LLM-friendly response structures

## 🟢 Data Layer

- [x] Weekly JSON collection
- [x] Calendar HTML collection
- [x] Event ID extraction
- [x] Event matching
- [x] Event detail collection
- [x] JSON persistence
- [ ] Cleaner normalized event-detail schema

---

# 🧠 Design Principles

The long-term architecture separates the system into three layers:

```text
┌─────────────────────────────────────────┐
│               MCP Layer                 │
│                                         │
│  Tools                                  │
│  Resources                              │
│  Input validation                       │
│  Agent-facing responses                 │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│          Domain / Collector Layer       │
│                                         │
│  Date handling                           │
│  Timezone handling                       │
│  Calendar collection                     │
│  Event matching                          │
│  Event enrichment                        │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│           Forex Factory                 │
│                                         │
│  Weekly JSON                            │
│  Calendar HTML                          │
│  Event detail endpoint                  │
└─────────────────────────────────────────┘
```

This keeps the scraping and data-collection logic independent from the MCP protocol.

The collector should remain reusable even when the data is consumed outside an AI-agent environment.

---

# 🔐 Responsible Usage

This project relies on publicly accessible Forex Factory pages/endpoints and scraping behavior rather than an official Forex Factory developer API.

The collector should therefore:

- Respect Forex Factory's terms and policies.
- Use reasonable request rates.
- Avoid unnecessary repeated requests.
- Handle changes to the site's HTML structure gracefully.
- Avoid excessive requests to the service.

HTML selectors and endpoint behavior may change over time.

---

# 🎯 Project Goal

The long-term goal is to build a reliable, timezone-aware Forex Factory economic-calendar service that provides high-quality structured data to AI agents through MCP.

The project is evolving toward:

```text
Forex Factory
      │
      ▼
Data Collection
      │
      ▼
Event Enrichment
      │
      ▼
Structured Dataset
      │
      ▼
FastMCP
      │
      ├───────────────┐
      ▼               ▼
   Tools          Resources
      │               │
      └───────┬───────┘
              ▼
          AI Agents
```

The current focus is improving **data quality, event-ID resolution, MCP resource consistency, and timezone-aware calendar handling**.
