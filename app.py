import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from fastapi.middleware.cors import CORSMiddleware

# Environment

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MCP_SERVER_URL = "https://c0b0-223-185-55-44.ngrok-free.app/mcp"


# Gemini Client
client = genai.Client(
    api_key=GEMINI_API_KEY
)


# FastAPI Application
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


# Request Model
class ForexSummaryRequest(BaseModel): 
    query: str = (
        "Analyze the current week's Forex Factory economic " 
        "calendar and provide a useful summary of the " 
        "important forex events."
    ) 
    detailed: bool = False


# Health Endpoint
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "forex-factory-strategy-analyzer",
    }


# Forex Summary Endpoint
@app.post("/summarize-forex-data")
async def summarize_forex_data( request: ForexSummaryRequest):
    try:
        # Build Gemini Instruction
        detail_instruction = ""
        if request.detailed:
            detail_instruction = """The user explicitly requested detailed Forex Factory data.
            You SHOULD use the `get_forex_event_details` MCP tool. 
            This is a long-running operation and may take approximately 1-2 minutes. 
            Do not avoid calling it merely because it is long-running. 
            After the tool returns, analyze the detailed data.
            """

        prompt = f""" You are a professional forex market analysis assistant.
        Your job is to analyze Forex Factory economic calendar data using the available MCP tools.
        
        User request:
        {request.query}

        AVAILABLE MCP TOOLS:
        1. get_forex_calendar - Use this tool when the user needs the current/basic Forex Factory economic calendar.
        It provides normalized calendar information such as:
        - Date 
        - Time 
        - Currency 
        - Impact 
        - Event 
        - Actual 
        - Forecast 
        - Previous
        This is the faster tool and should be preferred when detailed HTML/event information is not required.

        2. get_forex_event_details - Use this tool when the user explicitly asks for detailed event information or when additional event metadata is required.
        This tool performs Phase 2 of the Forex Factory scraper and may take approximately 1-2 minutes
        It provides additional information such as:
        - Date 
        - Time 
        - Currency 
        - Impact 
        - Event 
        - Actual 
        - Forecast 
        - Previous 
        - Event ID 
        - Event URL
        Do NOT call the Phase 2 tool unnecessarily because it is a long-running operation.
        {detail_instruction}

        ANALYSIS REQUIREMENTS:

        1. Determine which MCP tool is appropriate for the user's request.
        2. Retrieve the relevant Forex Factory data using the MCP tool.
        3. Analyze the retrieved data rather than simply returning raw JSON.
        4. Identify important upcoming economic events.
        5. Pay particular attention to:
            - High-impact events 
            - Currency affected 
            - Event date 
            - Event time 
            - Actual value 
            - Forecast value 
            - Previous value
        6. Explain the potential market significance of the events.
        7. Explain which currencies or forex pairs could potentially be affected.
        8. Highlight important relationships between: 
            - Actual vs Forecast 
            - Forecast vs Previous 
            - Event impact 
            - Currency
        9. If detailed event data is available, include the event URL where useful.
        10. Do not invent economic data.
        11. Use only information retrieved from the MCP tools for Forex Factory-specific facts.
        12. If the available data is insufficient, explicitly state that.
        13. Clearly distinguish factual calendar information from your analysis or interpretation.
        14. Keep the final answer structured and easy to read.
        15. Do not return raw tool-call information unless it is useful to the user.

        Provide a concise but meaningful Forex calendar analysis.
        """

        # Call Gemini + Remote MCP Server
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt,
            tools=[
                {
                    "type": "mcp_server",
                    "name": "forex_factory",
                    "url": MCP_SERVER_URL,
                }
            ],
            background=True,
        )

        return {
            "status": interaction.status,
            "interaction_id": interaction.id,
        }
    except Exception as exc: 
        raise HTTPException(
            status_code=500, 
            detail=f"Forex analysis failed: {str(exc)}"
        )

@app.get("/interaction/{interaction_id}") 
async def get_interaction( interaction_id: str, ): 
    try: 
        interaction = client.interactions.get( id=interaction_id ) 

        # Completed 
        if interaction.status == "completed": 
            return { "status": "completed", "interaction_id": interaction.id, "analysis": interaction.output_text, } 

        # Failed 
        if interaction.status == "failed": 
            return { "status": "failed", "interaction_id": interaction.id, "error": str(interaction.error), } 

        # Cancelled 
        if interaction.status == "cancelled": 
            return { "status": "cancelled", "interaction_id": interaction.id, } 

        # Requires action 
        if interaction.status == "requires_action":
            return { "status": "requires_action", "interaction_id": interaction.id, "steps": interaction.steps, } 

        # Still running 
        return { "status": interaction.status, "interaction_id": interaction.id, } 

    except Exception as exc: 
        raise HTTPException( status_code=500, detail=f"Failed to retrieve interaction: {str(exc)}", )