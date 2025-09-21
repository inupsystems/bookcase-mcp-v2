import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import urllib.robotparser as robotparser
from markdownify import markdownify as md
from pymongo import MongoClient
from datetime import datetime
# Removed problematic import
import numpy as np  # Para criar embeddings simples
import os
import hashlib
import json

# Configurações
BASE_URL = "https://docs.frappe.io/erpnext/user/manual/en/"
START_PAGE = "introduction"
DELAY = 2  # segundos entre requisições
MONGO_URI = "mongodb://admin:admin123@localhost:27018/?authSource=admin"
DATABASE_NAME = "dev_memory_db"
COLLECTION_NAME = "documentacao"
CACHE_FILE = "embeddings_cache.json"
CHUNK_SIZE = 500  # tamanho máximo de cada chunk em caracteres

# Função simplificada para embeddings (substituindo SentenceTransformer)
def create_simple_embedding(text, vector_size=384):
    # Implementação simples de embedding baseado em hash
    # Não é tão eficaz quanto SentenceTransformer mas funciona para demonstração
    np.random.seed(int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32))
    return np.random.randn(vector_size).tolist()

# Conexão MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Carregar cache de embeddings
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        embedding_cache = json.load(f)
else:
    embedding_cache = {}

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(embedding_cache, f)

def hash_text(text):
    """Gera hash para identificar um texto no cache"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def can_fetch(url):
    rp = robotparser.RobotFileParser()
    robots_url = urljoin(BASE_URL, "/robots.txt")
    rp.set_url(robots_url)
    rp.read()
    return rp.can_fetch("*", url)

def get_page(url):
    if not can_fetch(url):
        print(f"[BLOQUEADO pelo robots.txt] {url}")
        return None
    
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FrappeScraper/1.0)"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"[ERRO {response.status_code}] {url}")
        return None

def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") or href.startswith(base_url) or not href.startswith("http"):
            full_url = urljoin(base_url, href)
            if full_url.startswith(base_url):
                links.append(full_url)
    return list(set(links))

def get_embedding(text):
    """Gera embedding usando cache local"""
    key = hash_text(text)
    if key in embedding_cache:
        return embedding_cache[key]
    emb = create_simple_embedding(text)
    embedding_cache[key] = emb
    save_cache()
    return emb

def chunk_text(text, max_size=CHUNK_SIZE):
    """Divide um texto em chunks menores por parágrafo"""
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) + 1 <= max_size:
            current_chunk += "\n" + p if current_chunk else p
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def extract_chunks(url, html):
    soup = BeautifulSoup(html, "html.parser")
    doc_title = soup.title.string.strip() if soup.title else url.split("/")[-1]
    slug = urlparse(url).path.strip("/").split("/")[-1]
    category = urlparse(url).path.strip("/").split("/")[0] or "geral"
    
    chunks_list = []
    for h2 in soup.find_all("h2"):
        chunk_title = h2.get_text().strip()
        content_parts = []
        for sibling in h2.find_next_siblings():
            if sibling.name == "h2":
                break
            if sibling.name in ["p", "ul", "ol", "pre"]:
                content_parts.append(md(str(sibling)))
        full_text = "\n".join(content_parts).strip()
        if full_text:
            for sub_chunk in chunk_text(full_text):
                embedding = get_embedding(sub_chunk)
                chunks_list.append({
                    "software": {
                        "id": "erpfreedom",
                        "name": "ERP Freedom",
                        "version": "15.0.0"
                    },
                    "doc_title": doc_title,
                    "doc_slug": slug,
                    "category": category,
                    "tags": [category.lower(), "erpnext", "frappe"],
                    "chunk_title": chunk_title,
                    "chunk_content": sub_chunk,
                    "chunk_embedding": embedding,
                    "source": {
                        "type": "paragraph",
                        "url": url,
                        "lastUpdated": datetime.utcnow()
                    }
                })
    return chunks_list

def save_to_mongo(docs):
    if docs:
        collection.insert_many(docs)
        print(f"[MONGO] Inseridos {len(docs)} chunks")

def scrape_docs(start_url, limit=5):
    visited = set()
    to_visit = [start_url]
    
    while to_visit and len(visited) < limit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        print(f"[BAIXANDO] {url}")
        html = get_page(url)
        if not html:
            continue

        chunks = extract_chunks(url, html)
        save_to_mongo(chunks)

        links = extract_links(html, BASE_URL)
        for link in links:
            if link not in visited:
                to_visit.append(link)

        time.sleep(DELAY)

if __name__ == "__main__":
    start_url = urljoin(BASE_URL, START_PAGE)
    scrape_docs(start_url, limit=5000)  # Teste com 3 páginas
    