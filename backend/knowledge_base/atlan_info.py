"""
Ingest docs.atlan.com and developer.atlan.com into a persistent Chroma DB.

Usage:
  python knowledge_base/ingest_chromadb.py

Notes:
- Tune SEED_URLS / MAX_PAGES_PER_DOMAIN / CHUNK_SIZE_WORDS as desired.
- Requires chromadb, sentence-transformers, requests, beautifulsoup4, tqdm, python-dotenv
"""

import os
import time
import json
import hashlib
from urllib.parse import urljoin, urlparse
from collections import deque

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import numpy as np

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# -------- CONFIG --------
PERSIST_DIR = os.path.join("backend/knowledge_base", "vectorstore_chroma")
os.makedirs(PERSIST_DIR, exist_ok=True)

SEED_URLS = [
    "https://docs.atlan.com/",
    "https://developer.atlan.com/"
]

ALLOWED_DOMAINS = ["docs.atlan.com", "developer.atlan.com"]

HEADERS = {
    "User-Agent": "Atlan-RAG-Ingest/1.0 (+https://your-org.example)"
}

# Crawl limits
MAX_PAGES_PER_DOMAIN = 200         # keep small for initial run
REQUEST_DELAY = 0.5                # seconds between requests

# Chunking
CHUNK_SIZE_WORDS = 400             # approx chunk length
CHUNK_OVERLAP_WORDS = 80

# Embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"

# Chroma collection name
CHROMA_COLLECTION_NAME = "atlan_docs"

# ------------------------

def fetch_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[fetch_page] Failed {url}: {e}")
        return None

def extract_text(html, base_url):
    """
    Extract main textual content from a page.
    Strategy: join text from <article>, or if not present, <main>, else <p> tags.
    Also grab the page title.
    """
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else base_url

    # Prefer semantic containers
    container = soup.find("article") or soup.find("main")
    if container:
        texts = [p.get_text(" ", strip=True) for p in container.find_all(["p","h1","h2","h3","li"])]
    else:
        # fallback: all paragraphs
        texts = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

    # Fallback if nothing found
    if not texts:
        texts = [soup.get_text(" ", strip=True)]

    # Join and normalize whitespace
    full_text = "\n\n".join(t for t in texts if t and len(t.strip())>20)
    return title, full_text

def chunk_text(text, size_words=CHUNK_SIZE_WORDS, overlap=CHUNK_OVERLAP_WORDS):
    """
    Simple word-based chunker with overlap.
    Returns list of chunks (strings).
    """
    words = text.split()
    if len(words) <= size_words:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + size_words
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    return chunks

def url_domain(url):
    parsed = urlparse(url)
    return parsed.netloc

def is_same_domain(seed_domain, url):
    try:
        return urlparse(url).netloc.endswith(seed_domain)
    except:
        return False

def canonical_id(url, chunk_idx):
    # deterministic id per (url, chunk_idx)
    key = f"{url}|||{chunk_idx}"
    return hashlib.sha1(key.encode()).hexdigest()

def crawl(seed_urls, max_pages_per_domain=MAX_PAGES_PER_DOMAIN):
    """
    Basic BFS crawler constrained to allowed domains.
    Returns dict: url -> page_text
    """
    visited = set()
    to_visit = deque(seed_urls)
    results = {}
    domain_counts = {}

    while to_visit:
        url = to_visit.popleft()
        if url in visited:
            continue
        domain = url_domain(url)
        domain_counts.setdefault(domain, 0)
        if domain not in ALLOWED_DOMAINS:
            continue
        if domain_counts[domain] >= max_pages_per_domain:
            continue

        time.sleep(REQUEST_DELAY)
        html = fetch_page(url)
        visited.add(url)
        if not html:
            continue

        title, text = extract_text(html, url)
        if text and len(text.split()) > 50:
            results[url] = {"title": title, "text": text}
            domain_counts[domain] += 1
            print(f"[crawl] saved {url} ({domain_counts[domain]} pages for {domain})")
        else:
            print(f"[crawl] skipped (short) {url}")

        # parse links and enqueue same-domain links
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            # make absolute
            try:
                full = urljoin(url, href)
            except:
                continue
            parsed = urlparse(full)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc in ALLOWED_DOMAINS and full not in visited:
                to_visit.append(full)

    return results

def embed_and_persist(pages, embedding_model_name=EMBEDDING_MODEL_NAME, persist_dir=PERSIST_DIR):
    # load embedding model
    print("[embed] loading embedding model:", embedding_model_name)
    embed_model = SentenceTransformer(embedding_model_name)

    # init chroma client (persistent)
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    # create or get collection
    try:
        collection = client.get_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        collection = client.create_collection(name=CHROMA_COLLECTION_NAME)

    ids, metadatas, documents, embeddings = [], [], [], []

    for url, page in tqdm(pages.items(), desc="Pages"):
        title = page["title"]
        text = page["text"]
        chunks = chunk_text(text)

        for idx, chunk in enumerate(chunks):
            cid = canonical_id(url, idx)
            ids.append(cid)
            documents.append(chunk)
            metadatas.append({
                "source": url,
                "title": title,
                "chunk_idx": idx,
                "length_words": len(chunk.split())
            })

    print(f"[embed] computing embeddings for {len(documents)} chunks...")
    # compute in batches
    B = 64
    for i in tqdm(range(0, len(documents), B), desc="Embedding batches"):
        batch_docs = documents[i:i+B]
        emb = embed_model.encode(batch_docs, show_progress_bar=False, convert_to_numpy=True)
        for e in emb:
            embeddings.append(e.tolist())

    print("[embed] upserting into Chroma...")
    # Upsert (add) into collection
        # Upsert (add) into collection
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    print("[embed] done. Chroma persisted at:", persist_dir)


def main():
    print("[main] starting crawl + ingest")
    pages = crawl(SEED_URLS)
    print(f"[main] pages fetched: {len(pages)}")
    if not pages:
        print("[main] no pages fetched; exiting")
        return
    embed_and_persist(pages)

if __name__ == "__main__":
    main()
