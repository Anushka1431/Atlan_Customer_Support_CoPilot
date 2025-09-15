import os
import json
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")
API_URL = os.getenv("HF_API_URL")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}


class TicketExtractionAgent:
    def __init__(self):
        self.chat_history = []
        # System prompt to enforce guardrails
        self.system_prompt = (
            "You are a helpdesk ticket extraction assistant. "
            "You DO NOT answer general questions or provide information. "
            "Your ONLY job is to ask clarifying questions to gather enough info to create a ticket. "
            "If the user types 'done', you acknowledge and prepare a ticket summary. "
            "Always keep responses short and focused on understanding the issue."
        )
        self.chat_history.append({"role": "system", "content": self.system_prompt})

    def add_user_message(self, message: str):
        self.chat_history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str):
        self.chat_history.append({"role": "assistant", "content": message})

    def converse(self, user_input: str) -> str:
        """
        Converse but never answer general questions.
        """
        self.add_user_message(user_input)

        # Guard: if user says done, we skip generating further assistant replies
        if user_input.lower() in ["done", "exit", "quit"]:
            return "Preparing ticket summary..."

        payload = {
            "model": HF_MODEL,
            "messages": self.chat_history,
            "temperature": 0.5,
        }

        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code != 200:
            raise Exception(f"HF API Error: {response.status_code}, {response.text}")

        reply = response.json()["choices"][0]["message"]["content"].strip()

        # Enforce guardrail: do not let the assistant answer questions
        if any(word in reply.lower() for word in ["i can tell you", "here's how", "you should", "the answer is"]):
            reply = "Please continue describing your issue. I cannot answer questions."

        self.add_assistant_message(reply)
        return reply

    def extract_ticket(self) -> dict:
        """
        Generate the ticket subject and body from the conversation.
        """
        prompt = (
            "You are an AI assistant that only extracts ticket info. "
            "Based on the conversation so far, output JSON only:\n"
            "{\n"
            '  "subject": "Concise subject of the issue",\n'
            '  "body": "Detailed description of the issue"\n'
            "}\n"
            "Do NOT answer any questions from the conversation, only summarize into a ticket."
        )
        self.add_user_message(prompt)

        payload = {
            "model": HF_MODEL,
            "messages": self.chat_history,
            "temperature": 0.2,
        }

        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code != 200:
            raise Exception(f"HF API Error: {response.status_code}, {response.text}")

        raw_text = response.json()["choices"][0]["message"]["content"].strip()
        try:
            ticket = json.loads(raw_text)
            return ticket
        except json.JSONDecodeError:
            raise Exception(f"Failed to parse ticket JSON: {raw_text}")


if __name__ == "__main__":
    agent = TicketExtractionAgent()
    print("📝 Start describing your issue. Type 'done' when finished.\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["done", "exit", "quit"]:
            print("Assistant: Preparing ticket summary...\n")
            break
        reply = agent.converse(user_input)
        print(f"Assistant: {reply}")

    ticket = agent.extract_ticket()
    print("\n✅ Extracted Ticket:")
    print(json.dumps(ticket, indent=2))
    print("\n✅ Extracted Ticket:")
    print(json.dumps(ticket, indent=2))
