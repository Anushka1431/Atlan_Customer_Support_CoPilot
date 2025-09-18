import asyncio,os,sys
import json
import uuid
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Load env variables
load_dotenv()
from common.mcp_client import SupportMCPClient

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/sse")
#correct one
# -----------------------------
# Async helper wrapper (unchanged)
# -----------------------------
async def process_ticket(ticket_id, ticket_text):
    client = SupportMCPClient(server_url=BACKEND_URL)
    await client.connect()

    # Step 1: Classification
    result = await client.run_tool("classification_tool", {"ticket_text": ticket_text})
    raw_output = result.content[0].text if getattr(result, "content", None) else ""
    try:
        classification = json.loads(raw_output)
    except Exception:
        classification = {"error": f"Parse error: {raw_output}"}

    category_json = classification.get("category", {})
    topic_tags = category_json.get("topic_tags", [])
    topic = topic_tags[0] if topic_tags else ""

    # Step 2: RAG or Routing
    if topic in ["How-to", "Product", "Best practices", "API/SDK", "SSO"]:
        result2 = await client.run_tool(
            "rag_tool", {"ticket_id": ticket_id, "topic": topic, "query": ticket_text}
        )
        raw_text2 = result2.content[0].text if getattr(result2, "content", None) else ""
        try:
            rag_answer = json.loads(raw_text2)
            final_response = {
                "type": "rag",
                "response": rag_answer.get("response", ""),
                "sources": rag_answer.get("sources", []),
                "raw": raw_text2
            }
        except Exception:
            final_response = {"type": "rag", "error": f"Parse error: {raw_text2}"}
    else:
        result3 = await client.run_tool(
            "routing_tool", {"ticket_id": ticket_id, "topic": topic}
        )
        raw_text3 = result3.content[0].text if getattr(result3, "content", None) else ""
        try:
            routing = json.loads(raw_text3)
            final_response = {
                "type": "routing",
                "message": routing.get("routing_message", ""),
                "raw": raw_text3
            }
        except Exception:
            final_response = {"type": "routing", "error": f"Parse error: {raw_text3}"}

    await client.cleanup()
    return classification, final_response


# -----------------------------
# Streamlit UI (full file)
# -----------------------------
st.set_page_config(page_title="Ticket Dashboard", layout="wide")
st.title("Ticket Classification Dashboard")

mode = st.sidebar.radio("Select Mode", ["Bulk Tickets", "Single Ticket", "Live Chat"])

# -----------------------------
# Bulk Tickets
# -----------------------------
if mode == "Bulk Tickets":
    st.header("📂 Bulk Ticket Classification")
    uploaded_file = st.file_uploader("Upload a JSON file of tickets", type=["json"])

    if uploaded_file is not None:
        try:
            tickets = json.load(uploaded_file)
            for t in tickets:
                ticket_id, ticket_text = t["id"], t["subject"] + " " + t["body"]
                with st.expander(f"{ticket_id} - {t['subject']}"):
                    classification, final_response = asyncio.run(process_ticket(ticket_id, ticket_text))

                    st.subheader("🔍 Internal Analysis")
                    st.json(classification)

                    st.subheader("✅ Final Response")
                    if final_response["type"] == "rag":
                        st.write(final_response.get("response", ""))
                        st.write("📚 Sources:", final_response.get("sources", []))
                    elif final_response["type"] == "routing":
                        st.write(final_response.get("message", ""))

                    # st.caption("Raw outputs for debugging")
                    # st.code(final_response.get("raw", ""), language="json")
        except Exception as e:
            st.error(f"Failed to parse JSON file: {e}")
    else:
        st.info("Please upload a JSON file to process tickets.")

# -----------------------------
# Single Ticket
# -----------------------------
elif mode == "Single Ticket":
    st.header("✍️ Classify a New Ticket")
    subject = st.text_input("Ticket Subject")
    body = st.text_area("Ticket Body")

    if st.button("Submit Ticket"):
        ticket_text = subject + " " + body
        classification, final_response = asyncio.run(process_ticket("USER-TICKET", ticket_text))

        st.subheader("🔍 Internal Analysis")
        st.json(classification)

        st.subheader("✅ Final Response")
        if final_response["type"] == "rag":
            st.write(final_response.get("response", ""))
            st.write("📚 Sources:", final_response.get("sources", []))
        elif final_response["type"] == "routing":
            st.write(final_response.get("message", ""))

        # st.caption("Raw outputs for debugging")
        # st.code(final_response.get("raw", ""), language="json")


# ...existing code...
elif mode == "Live Chat":
    st.header("💬 Live Chat with Ticket Extraction")

    # initialize session-state helpers
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_analysis" not in st.session_state:
        st.session_state.last_analysis = None
    if "last_final_response" not in st.session_state:
        st.session_state.last_final_response = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"CHAT-{uuid.uuid4().hex[:8]}"
    if "complete_chat" not in st.session_state:
        st.session_state.complete_chat = False
    if "chat_text" not in st.session_state:
        st.session_state.chat_text = ""

    user_msg = st.chat_input("Describe your issue... (type 'done' to finish)")

    def normalize_tool_response(result):
        """
        Normalize various MCP response shapes into a python dict.
        Accepts:
          - dict (returned directly by server)
          - object with .content (list-like with .text)
          - raw string or other object
        Returns a dict with expected keys like 'status', 'reply', 'ticket' etc.
        """
        # already a dict
        if isinstance(result, dict):
            return result

        # object with .content
        if hasattr(result, "content") and result.content:
            # try to extract the first chunk's text
            text = ""
            try:
                text = result.content[0].text
            except Exception:
                # fallback: stringify content
                text = str(result.content)

            # try to parse JSON text
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
                # if parsed is some other JSON type, wrap it
                return {"status": "in_progress", "reply": parsed}
            except Exception:
                # not JSON -> return as reply string
                return {"status": "in_progress", "reply": text}

        # last fallback -> stringified result
        return {"status": "error", "reply": str(result)}

    if user_msg:
        # Check if user typed 'done' to complete the ticket
        if user_msg.lower().strip() == "done":
            st.session_state.chat_history.append({"role": "user", "content": "done"})
            st.session_state.chat_history.append({"role": "assistant", "content": "Processing your ticket now..."})
            st.session_state.complete_chat = True
        else:
            # Add message to history and accumulated chat text
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            st.session_state.chat_text += f"\n{user_msg}"

            async def call_live_qna(msg, session_id):
                client = SupportMCPClient(server_url=BACKEND_URL)
                await client.connect()
                try:
                    result = await client.run_tool(
                        "live_qna_tool",
                        {"session_id": session_id, "user_input": msg}
                    )
                    return result
                finally:
                    await client.cleanup()

            # call the MCP tool and normalize result
            raw_result = asyncio.run(call_live_qna(user_msg, st.session_state.session_id))
            result_dict = normalize_tool_response(raw_result)

            status = result_dict.get("status", "error")

            if status == "in_progress":
                ai_reply = result_dict.get("reply", "")
                st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})

            elif status == "completed":
                ticket = result_dict.get("ticket", {})
                # guard: sometimes ticket may be a JSON string
                if isinstance(ticket, str):
                    try:
                        ticket = json.loads(ticket)
                    except Exception:
                        ticket = {"subject": "", "body": ticket}

                st.session_state.complete_chat = True
                st.session_state.ticket = ticket

    # Process the completed chat if needed
    if st.session_state.complete_chat:
        # Create a ticket from accumulated chat or use the one from the tool
        if hasattr(st.session_state, "ticket"):
            ticket = st.session_state.ticket
        else:
            # Create a basic ticket from chat history
            all_user_msgs = [msg["content"] for msg in st.session_state.chat_history if msg["role"] == "user" and msg["content"].lower() != "done"]
            ticket_text = " ".join(all_user_msgs)
            
            # Simple heuristic: first message is subject, rest is body
            subject = all_user_msgs[0] if all_user_msgs else ""
            body = " ".join(all_user_msgs[1:]) if len(all_user_msgs) > 1 else ""
            ticket = {"subject": subject, "body": body}
            
        ticket_text = ticket.get("subject", "") + " " + ticket.get("body", "")
        
        # Run the ticket classification process
        classification, final_response = asyncio.run(
            process_ticket("CHAT-TICKET", ticket_text)
        )
        st.session_state.last_analysis = classification
        st.session_state.last_final_response = final_response
        
        # Mark as processed to avoid repeated processing
        st.session_state.complete_chat = False
        
        # Add results to chat
        if not any(msg.get("content", "").startswith("✅ I've prepared your ticket") for msg in st.session_state.chat_history):
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "✅ I've prepared your ticket. Here's what I found:"
            })
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"**Subject:** {ticket.get('subject', '')}\n\n**Body:** {ticket.get('body', '')}"
            })

            if final_response.get("type") == "rag":
                rag_msg = (
                    f"**RAG Response:**\n{final_response.get('response', '')}\n\n"
                    f"**Sources:** {', '.join(final_response.get('sources', []))}"
                )
                st.session_state.chat_history.append({"role": "assistant", "content": rag_msg})

            elif final_response.get("type") == "routing":
                routing_msg = f"**Routing Message:**\n{final_response.get('message', '')}"
                st.session_state.chat_history.append({"role": "assistant", "content": routing_msg})

    # Render conversation (use markdown for formatting)
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Debug panel for last ticket
    if st.session_state.last_analysis and st.session_state.last_final_response:
        st.subheader("🔍 Last Ticket Analysis")
        st.json(st.session_state.last_analysis)
        st.subheader("✅ Last Final Response")
        st.json(st.session_state.last_final_response)
