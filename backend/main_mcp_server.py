import os,sys
import logging
from mcp.server.fastmcp import FastMCP
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# project_root = Path("D:/anushka/Atlan_Project").resolve()
# if str(project_root) not in sys.path:
#     sys.path.insert(0, str(project_root))
_project_root_env = os.getenv("PROJECT_ROOT")
if _project_root_env:
    project_root = Path(_project_root_env).resolve()
else:
    project_root = Path(__file__).resolve().parent  # contains 'sagents'

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sagents.classification_agent import classify_ticket
from sagents.rag_qna_agent import generate_answer
from sagents.routing_agent import route_ticket
from sagents.STT import transcribe_audio
from sagents.live_converse import TicketExtractionAgent
import asyncio
import json     
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="customer_support_server")

@mcp.tool()
async def classification_tool(ticket_text: str) -> dict:
    """Classify a support ticket into a topic (How-to, Product, API, etc.)."""
    ticket = {
        "id": "TICKET-001",
        "subject": ticket_text,
        "body": ticket_text
    }
    result = await asyncio.to_thread(classify_ticket, ticket)
    return result


@mcp.tool()
async def rag_tool(ticket_id: str, topic: str, query: str) -> dict:
    """Retrieve knowledge base info and generate an answer with RAG."""
    result = await asyncio.to_thread(generate_answer, ticket_id, topic, query)
    return result


@mcp.tool()
async def routing_tool(ticket_id: str, topic: str) -> dict:
    """Route tickets outside RAG scope (e.g., Connector, Sensitive Data)."""
    result = await asyncio.to_thread(route_ticket, ticket_id, topic)
    return result

@mcp.tool()
async def stt_tool(audio_path: str) -> str:
    """Transcribe an audio file into text using Whisper."""
    result = await asyncio.to_thread(transcribe_audio, audio_path)
    return result

# -------------------------------
# New Live QnA tool (single)
# -------------------------------
ticket_agents = {}  # track per-session agents

@mcp.tool()
async def live_qna_tool(session_id: str, user_input: str) -> dict:
    """
    Converse with the Live QnA agent to gather ticket details.
    - If user_input is a description, returns assistant reply.
    - If user_input is 'done'/'exit'/'quit', returns ticket JSON.
    """
    if session_id not in ticket_agents:
        ticket_agents[session_id] = TicketExtractionAgent()

    agent = ticket_agents[session_id]

    if user_input.lower() in ["done", "exit", "quit"]:
        ticket = await asyncio.to_thread(agent.extract_ticket)
        # cleanup session
        del ticket_agents[session_id]
        return {"status": "completed", "ticket": ticket}

    reply = await asyncio.to_thread(agent.converse, user_input)
    return {"status": "in_progress", "reply": reply}


# 5. Run server
# Change the host to listen on all interfaces
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(mcp.sse_app, host="0.0.0.0", port=port)