# Financial Earnings Research Agent

## What is it?
An agentic RAG system that lets you ask natural language questions about real public company earnings reports. Type "What were Apple's red flags in their latest 10-Q?" and the agent fetches the actual SEC filing, chunks and indexes it into a vector database, and answers with citations back to the exact chunks it used. Follow-up questions like "How does that compare to Services revenue?" work without repeating the company name — it remembers the context.


## What I built?

### 1. Document Ingestion Pipeline (tools.py):

**1. Downloading from SEC EDGAR:** Used `sec-edgar-downloader` to fetch the latest 10-Q filing directly from SEC EDGAR by ticker symbol. It downloads the full submission file which is a raw text file containing the HTML document.

**2. HTML Extraction:** The full submission file wraps the actual 10-Q in `<DOCUMENT>` tags. Used BeautifulSoup to parse out just the first document block, strip all the HTML tags, and get clean readable text. The alternative was parsing the whole file as-is, which would've included raw HTML noise in the chunks and killed retrieval quality.

**3. Chunking Strategy:** Decided on chunk size of 1000 characters with 200 character overlap. The overlap ensures that sentences or numbers that fall right at a boundary don't get split and lose context. Tested smaller chunks — they were too granular and missed multi-sentence financial context. Tested larger — retrieval became less precise.

**4. Embeddings:** Used OpenAI's `text-embedding-3-small` to embed every chunk. It's cost-effective and accurate enough for financial text retrieval. Batch embedded all chunks in one API call.

**5. Vector Storage with ChromaDB:** Stored all chunks and their embeddings in ChromaDB with a persistent client. Each company gets its own collection named by ticker (e.g. `AAPL`, `NVDA`). On re-query, it checks `collection.count()` first — if already indexed, skips the entire download-extract-embed pipeline. No redundant API calls.


### 2. The Agent (agent.py):

**1. Company Resolution:** The agent supports Apple, NVIDIA, Microsoft, Tesla, and Amazon. Built a simple resolver that checks the user's question for company name keywords and maps them to ticker symbols. If no company is mentioned, it falls back to the company from the current session — this is what enables follow-up questions to work.

**2. Conversational Memory:** Session state tracks the full message history including system prompt, user messages, tool call results, and assistant responses. Every `run_agent` call appends to this history, so the model always has context of prior turns.

**3. Agentic Tool Calling Loop:** The agent runs in a `while True` loop, calling the model and checking `finish_reason`. If the model returns `tool_calls`, it dispatches to the right tool, appends the result to messages, and loops again. If it returns `stop`, it exits with the final answer. This is the core agentic loop — the LLM decides what to call and when, not hardcoded logic.

**4. Two Tools Exposed:**
- `index_document`: downloads and indexes a 10-Q for a given ticker. The agent calls this first if the document hasn't been indexed yet.
- `search_knowledge_base`: embeds the query and does semantic search over ChromaDB, returning top-5 chunks with their IDs.

**5. System Prompt Engineering:** The prompt is strict — it tells the model to only answer using retrieved chunks, cite every chunk ID used as `[source: TICKER_chunk_N]`, and refuse to use outside knowledge. Without this, the model would confidently answer from training data and completely bypass the retrieval pipeline. Took a few iterations to make it refuse cleanly rather than hedge.

**6. Source Attribution:** Every answer cites the chunk IDs it pulled from. If a single sentence uses numbers from multiple chunks, it cites all of them. This was a deliberate design choice — you can trace any claim back to the exact section of the 10-Q it came from.


### Tech Stack
Python, OpenAI API (gpt-4o-mini + text-embedding-3-small), ChromaDB, sec-edgar-downloader, BeautifulSoup


### How to Run Locally
1. Clone the repo
2. Create a virtual environment and install requirements
3. Add a `.env` file with your OpenAI API key
4. `cd agent`
5. Run `python agent.py`
