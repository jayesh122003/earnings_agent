import os
from sec_edgar_downloader import Downloader
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
import chromadb

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def download_earnings_report(ticker: str) -> str:
    """Download the latest 10-Q earnings report for a given ticker from SEC EDGAR."""
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    dl = Downloader("MyCompany", "myemail@example.com", DATA_DIR)
    dl.get("10-Q", ticker, limit=1)
    
    # Find the downloaded file
    ticker_dir = os.path.join(DATA_DIR, "sec-edgar-filings", ticker, "10-Q")
    
    if not os.path.exists(ticker_dir):
        raise FileNotFoundError(f"No 10-Q filing found for {ticker}")
    
    # Get the most recent filing
    filings = sorted(os.listdir(ticker_dir), reverse=True)
    if not filings:
        raise FileNotFoundError(f"No filings found for {ticker}")
    
    filing_path = os.path.join(ticker_dir, filings[0])
    return filing_path


def extract_filing_text(filing_dir):
    path = os.path.join(filing_dir, "full-submission.txt")
    with open(path, "r", encoding="utf-8") as f:
      content = f.read()
    i = content.find("<DOCUMENT>")
    j= content.find("</DOCUMENT>")
    first_doc = content[i+len("<DOCUMENT>"):j]
    soup = BeautifulSoup(first_doc, "html.parser")
    text = soup.get_text()
    return text


def chunk_text(text, chunk_size = 1000, overlap = 200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def embed_chunks(chunks):
    client = OpenAI()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
    )
    embeddings = [item.embedding for item in response.data]
    return embeddings


def index_document(ticker):
    
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name=ticker)
    if collection.count() > 0:
        print(f"{ticker} already indexed ({collection.count()} chunks)")
        return collection
    
    filing_path = download_earnings_report(ticker)
    text = extract_filing_text(filing_path)
    chunks = chunk_text(text)
    embeddings = embed_chunks(chunks)

    #store chunks
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{ticker}_chunk_{i}" for  i in range(len(chunks))]
    )

    print(f"Indexed {len(chunks)} chunks for {ticker}")
    return collection

def search_knowledge_base(query, ticker):

    client = OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = response.data[0].embedding

    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name=ticker)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    documents = results["documents"][0]
    ids = results["ids"][0]
    output = []
    for id, text in zip(ids, documents):
        output.append({"id":id, "text":text})
        
    return output



if __name__ == '__main__':
    #chunks = search_knowledge_base("what was Apple's iPhone revenue?", "AAPL")
    chunks = search_knowledge_base("revenue", "NVDA")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        #print(chunk[:300])
        print(chunk["id"])
        print(chunk["text"][:1000])

