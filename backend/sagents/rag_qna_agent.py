import os
import requests
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load ENV vars
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")  # llama-v3p1-8b-instruct
HF_API_URL = os.getenv("HF_API_URL")
PERSIST_DIR = os.path.join("backend/knowledge_base", "vectorstore_chroma")

# Initialize Chroma client
client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_collection("atlan_docs")

# Embedding function (must match what we used for DB creation)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L12-v2"
)

def query_chroma(query, top_k=3):
    results = collection.query(
        query_texts=[query],   # <- only this
        n_results=top_k
    )
    docs = results["documents"][0]
    sources = results["metadatas"][0]
    return docs, sources

def generate_answer(ticket_id: str, topic: str, query: str, top_k: int = 5):
    """RAG pipeline: retrieve + synthesize answer."""
    docs, sources = query_chroma(query, top_k=top_k)
    context_text = "\n\n".join(docs)

    prompt = f"""
You are an AI support assistant for Atlan. 
A customer asked the following question:

Query: {query}
Topic: {topic}

Use the following documentation context to answer clearly and concisely:
{context_text}

If the answer is not found in the context, say "I could not find this in the documentation.".
Always cite the most relevant sources.

Answer:
"""

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": HF_MODEL,   # e.g. meta-llama/Llama-3.1-8B-Instruct:cerebras
        "messages": [
            {"role": "system", "content": "You are a helpful support assistant for Atlan."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
    }

    response = requests.post(
        HF_API_URL,   # should be: https://router.huggingface.co/v1/chat/completions
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise RuntimeError(f"HuggingFace API error: {response.text}")

    generated = response.json()["choices"][0]["message"]["content"].strip()


    source_urls = [s["source"] for s in sources if "source" in s]

    return {
        "ticket_id": ticket_id,
        "response": generated,
        "sources": list(dict.fromkeys(source_urls))[:3]  # unique, preserve order
    }

# Quick test
if __name__ == "__main__":
    test_ticket = {
        "ticket_id": "TICKET-246",
        "topic": "Lineage",
        "query": "Which connectors automatically capture lineage?"
    }
    result = generate_answer(**test_ticket)
    print(result)
