import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from fastapi.middleware.cors import CORSMiddleware


# --------------------------------------------------
# Environment
# --------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MCP_SERVER_URL = "https://8282-223-185-54-112.ngrok-free.app/mcp"


# --------------------------------------------------
# Gemini Client
# --------------------------------------------------

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Forex Factory Strategy Analyzer",
    description="API for analyzing Forex Factory economic calendar data using Gemini and MCP.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Request Model
# --------------------------------------------------

class ForexSummaryRequest(BaseModel):
    query: str = (
        "Analyze the current week's Forex Factory economic calendar "
        "and provide a useful summary of the important forex events."
    )


# --------------------------------------------------
# Health Endpoint
# --------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "forex-factory-strategy-analyzer",
    }


# --------------------------------------------------
# Forex Summary Endpoint
# --------------------------------------------------

@app.post("/summarize-forex-data")
async def summarize_forex_data(request: ForexSummaryRequest):

    prompt = f"""
You are a professional forex market analysis assistant.

The user wants an analysis of the current Forex Factory economic
calendar data.

User request:
{request.query}

Your task:

1. Retrieve the relevant Forex Factory economic calendar data using
   the available MCP server/tool.

2. Analyze the events rather than simply returning the raw data.

3. Identify the most important upcoming economic events.

4. Pay particular attention to:
   - High-impact events
   - Currency affected
   - Event date and time
   - Previous value
   - Forecast value
   - Actual value, when available
   - Potential market significance

5. Explain which currencies or forex pairs could potentially be
   affected by these events.

6. Highlight the events that traders should pay the most attention to.

7. Keep the response structured and easy to read.

8. Do not invent economic data. Use only information obtained from
   the available MCP data.

9. If the available data is insufficient to make a conclusion,
   explicitly state that.

Provide a concise but meaningful forex calendar analysis.
"""

    response = client.interactions.create(
        model="gemini-2.5-flash",
        input=prompt,
        tools=[
            {
                "type": "mcp_server",
                "name": "forex_factory",
                "url": MCP_SERVER_URL,
            }
        ],
    )

    return {
        "status": "success",
        "analysis": response.output_text,
    }