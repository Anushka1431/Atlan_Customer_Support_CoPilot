import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")

API_URL = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
}


def classify_ticket(ticket: dict) -> dict:
    """
    Classify a single ticket into categories.

    Args:
        ticket (dict): {
            "id": str,
            "subject": str,
            "body": str
        }
    Returns:
        dict: {
            "id": str,
            "category": dict
        }
    """
    prompt = f"""
    You are an AI agent for a helpdesk application. 
    Given a ticket (subject and body), analyze it and return ONLY a JSON object with:

    {{
      "topic_tags": [ ... ],   // choose from: How-to, Product, API/SDK, Connector, Lineage, SSO, Glossary, Best practices, Sensitive data.
      "sentiment": "...",      // choose from: Frustrated, Curious, Angry, Neutral
      "priority": "..."        // choose from: P0 (High), P1 (Medium), P2 (Low)
    }}

    Ticket Subject: {ticket['subject']}
    Ticket Body: {ticket['body']}

    Rules:
    - Output valid JSON only (no text around it).
    - Choose 1 or 2 most relevant topic tags.
    - Priority reflects urgency implied in the ticket.
    """

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": HF_MODEL,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"HF API Error: {response.status_code}, {response.text}")

    output = response.json()
    category = output["choices"][0]["message"]["content"].strip()
    parsed = json.loads(category)

    return {"id": ticket["id"], "category": parsed}


def classify_from_file(file_path: str, output_file: str = None):
    """
    Classify all tickets in a JSON file.
    """
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        tickets = json.load(f)

    results = [classify_ticket(ticket) for ticket in tickets]

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"✅ Saved results to {output_file}")
    else:
        for r in results:
            print(json.dumps(r, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ticket classification agent")
    parser.add_argument("--file", type=str, help="Path to JSON file with tickets")
    parser.add_argument("--output", type=str, help="Where to save classified results")
    args = parser.parse_args()

    if args.file:
        # Batch mode
        classify_from_file(args.file, args.output)
    else:
        # Single ticket mode
        sample_ticket = {
            "id": "TICKET-245",
            "subject": "help in deploying Atlan agent in secure VPC",
            "body": "Our primary data lake is hosted on-premise within a secure VPC and is not exposed to the internet. We understand we need to use the Atlan agent for this, but the setup instructions are a bit confusing for our security team. This is a critical source for us, and we can't proceed with our rollout until we get this connected. Can you provide a detailed deployment guide so we know how to do this."
        }
        print(json.dumps(classify_ticket(sample_ticket), indent=2))




# import os,json
# import requests
# from dotenv import load_dotenv

# # Load env variables
# load_dotenv()
# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL = os.getenv("HF_MODEL")
# HF_API_URL = os.getenv("HF_API_URL")

# API_URL = "https://router.huggingface.co/v1/chat/completions"
# headers = {
#     "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
# }

# def classify_ticket(ticket):
#     """
#     Classify a ticket into categories (e.g., Integration, Permissions, Documentation, Lineage, Urgent Issue).
    
#     Args:
#         ticket (dict): {
#             "id": str,
#             "subject": str,
#             "body": str
#         }
#     Returns:
#         dict: {
#             "id": str,
#             "category": str
#         }
#     """
#     prompt = f"""
#     You are an AI agent for a helpdesk application. 
#     Given a ticket (subject and body), you must analyze it and return a structured JSON response with the following fields:

#     Ticket Subject: {ticket['subject']}
#     Ticket Body: {ticket['body']}

#     {{
#     "topic_tags": [ ... ],   // choose from: How-to, Product, Connector, Lineage, API/SDK, SSO, Glossary, Best practices, Sensitive data
#     "sentiment": "...",      // choose from: Frustrated, Curious, Angry, Neutral
#     "priority": "..."        // choose from: P0 (High), P1 (Medium), P2 (Low)
#     }}

#     Rules:
#     - Always output valid JSON.
#     - Use multiple topic_tags if relevant.
#     - Priority reflects urgency implied in the ticket.
#     - Do not add explanations, only the JSON.
#     """
#     payload = {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         "model": os.environ["HF_MODEL"],
#         "response_format": {"type": "json_object"}
#     }
#     response = requests.post(API_URL, headers=headers, json=payload)
#     if response.status_code != 200:
#         raise Exception(f"HF API Error: {response.status_code}, {response.text}")
#     output = response.json()
#     category = output["choices"][0]["message"]["content"].strip()
#     parsed = json.loads(category)
#     return {
#         "id": ticket["id"],
#         "category": parsed
#     }

# # Example run
# if __name__ == "__main__":
#     sample_ticket = {
#         "id": "TICKET-245",
#         "subject": "Connecting Snowflake to Atlan - required permissions?",
#         "body": "Hi team, we're trying to set up our primary Snowflake production database..."
#     }
#     print(classify_ticket(sample_ticket))
