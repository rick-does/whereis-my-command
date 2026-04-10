import sys
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma"
COLLECTION_NAME = "tldr"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gemini-2.5-flash"
TOP_K = 10

REWRITE_PROMPT = ChatPromptTemplate.from_template(
    "Convert the following natural language goal into concise technical search terms "
    "that would appear in CLI command documentation. Focus on the operation type, "
    "tool category, and technical parameters — not the human-friendly phrasing.\n\n"
    "Goal: {query}\n\n"
    "Technical search terms (one line, no explanation):"
)

PROMPT = ChatPromptTemplate.from_template(
    "You are a CLI command assistant. A user wants to accomplish something on the "
    "command line but doesn't know the exact command.\n\n"
    "Given the user's goal and relevant CLI documentation pages, return 3 to 5 of the "
    "best commands, ranked from most to least commonly used. Prefer commands from the "
    "'common' or 'linux' platforms unless the user's goal explicitly mentions a "
    "different platform (e.g. Windows, macOS, Android). Include well-known standard "
    "tools before obscure ones.\n\n"
    "Before selecting commands, evaluate whether each documentation page actually "
    "addresses the user's goal. Discard any results that only match on incidental "
    "phrasing rather than the actual task — for example, if the user asks about "
    "filesystem operations, do not return version control commands (git, svn) just "
    "because they mention a similar timeframe or keyword.\n\n"
    "User's goal: {query}\n\n"
    "Relevant documentation:\n{context}\n\n"
    "Respond with 3 to 5 results in this exact format, repeating the block for each:\n"
    "Result:\n"
    "Command: <the command, with typical flags if helpful — replace any {{placeholder}} "
    "syntax with a realistic concrete example>\n"
    "Explanation: <plain English explanation of what it does>\n"
    "Source: <command name>\n"
)


_ef = None
_chroma = None
_collection = None


def _ensure_initialized():
    global _ef, _chroma, _collection
    if _collection is not None:
        return
    _ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    _chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        _collection = _chroma.get_collection(COLLECTION_NAME, embedding_function=_ef)
    except Exception:
        raise RuntimeError(
            "Corpus not found. Run ingest/ingest.py before starting the backend."
        )


def query(user_query: str) -> dict:
    _ensure_initialized()

    llm = ChatGoogleGenerativeAI(model=LLM_MODEL)
    rewritten = (REWRITE_PROMPT | llm).invoke({"query": user_query})
    search_query = rewritten.content.strip() if rewritten.content else user_query

    results = _collection.query(query_texts=[search_query], n_results=TOP_K)
    sections = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        sections.append(f"[platform: {meta['platform']}]\n{doc}")
    context = "\n\n---\n\n".join(sections)

    response = (PROMPT | llm).invoke({"query": user_query, "context": context})

    results = []
    current: dict = {}
    current_key = None
    current_lines: list = []

    def _flush_key():
        if current_key and current_lines:
            current[current_key] = "\n".join(current_lines).strip()

    def _flush_result():
        _flush_key()
        if current:
            if "command" in current:
                current["command"] = " ".join(current["command"].splitlines()).strip()
            results.append(current.copy())
            current.clear()

    for line in response.content.splitlines():
        if line.strip() == "Result:":
            _flush_result()
            current_key = None
            current_lines = []
        elif line.startswith("Command:"):
            _flush_key()
            current_key = "command"
            current_lines = [line.split(":", 1)[1].strip()]
        elif line.startswith("Explanation:"):
            _flush_key()
            current_key = "explanation"
            current_lines = [line.split(":", 1)[1].strip()]
        elif line.startswith("Source:"):
            _flush_key()
            current_key = "source"
            current_lines = [line.split(":", 1)[1].strip()]
        elif current_key:
            current_lines.append(line)

    _flush_result()

    return {"query": user_query, "raw": response.content, "results": results}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "recursively find files modified in the last 24 hours"
    result = query(q)
    for i, r in enumerate(result.get("results", []), 1):
        print(f"\n--- Result {i} ---")
        print(f"Command:     {r.get('command', 'N/A')}")
        print(f"Explanation: {r.get('explanation', 'N/A')}")
        print(f"Source:      {r.get('source', 'N/A')}")
