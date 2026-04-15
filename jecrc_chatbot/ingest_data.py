import os
import json
import hashlib
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DATA_DIR = os.path.join(BASE_DIR, "data")
FAISS_INDEX_PATH = os.path.join(DB_DIR, "faiss_index")
HASH_FILE = os.path.join(DB_DIR, "ingested_hashes.json")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def get_file_hash(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()

def load_hashes():
    try:
        return json.load(open(HASH_FILE))
    except:
        return {}

def save_hashes(hashes):
    json.dump(hashes, open(HASH_FILE, "w"), indent=2)

def main():
    print("Checking for new/changed files...")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    saved_hashes = load_hashes()
    new_docs = []
    updated_hashes = saved_hashes.copy()

    # ── Scan PDFs ────────────────────────────────────────────────
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found in data/ folder.")
    
    for filename in pdf_files:
        filepath = os.path.join(DATA_DIR, filename)
        current_hash = get_file_hash(filepath)

        if saved_hashes.get(filename) == current_hash:
            print(f"Skipped (unchanged): {filename}")
            continue

        try:
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            chunks = splitter.split_documents(docs)
            new_docs.extend(chunks)
            updated_hashes[filename] = current_hash
            print(f"Loaded: {filename} → {len(chunks)} chunks")
        except Exception as e:
            print(f"Failed to load {filename}: {e}")

    # ── Web Scraping (JECRC) ─────────────────────────────────────
    WEB_HASH_KEY = "__web_jecrc__"
    # Re-scrape only if you want fresh web data — set FORCE_WEB=true in .env
    force_web = os.getenv("FORCE_WEB", "false").lower() == "true"

    if force_web or WEB_HASH_KEY not in saved_hashes:
        try:
            print("Scraping JECRC website...")
            web_loader = RecursiveUrlLoader(
                url="https://jecrcfoundation.com/",
                max_depth=1,
                extractor=lambda x: BeautifulSoup(x, "html.parser").get_text(separator=" ", strip=True),
                prevent_outside=True
            )
            web_docs = web_loader.load()
            web_chunks = splitter.split_documents(web_docs)
            new_docs.extend(web_chunks)
            updated_hashes[WEB_HASH_KEY] = "scraped"
            print(f"JECRC website → {len(web_chunks)} chunks")
        except Exception as e:
            print(f"Web scraping failed: {e}")
    else:
        print("Skipped web scrape (already done). Set FORCE_WEB=true to re-scrape.")

    # ── Nothing new ──────────────────────────────────────────────
    if not new_docs:
        print("\n Index is already up to date. Nothing to do.")
        return

    # ── Build or update FAISS index ──────────────────────────────
    if os.path.exists(FAISS_INDEX_PATH):
        print(f"\n Existing index found. Merging {len(new_docs)} new chunks...")
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        vectorstore.add_documents(new_docs)
    else:
        print(f"\n No existing index. Building fresh from {len(new_docs)} chunks...")
        vectorstore = FAISS.from_documents(new_docs, embeddings)

    vectorstore.save_local(FAISS_INDEX_PATH)
    save_hashes(updated_hashes)
    print(f"\n Done! Index updated with {len(new_docs)} new chunks.")

if __name__ == "__main__":
    main()