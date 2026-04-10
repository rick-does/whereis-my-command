import os
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rag import query as rag_query

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "20"))
RATE_WINDOW = 60

app = FastAPI(title="whereis <my-command>")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

_request_log: dict[str, list[float]] = defaultdict(list)
_last_cleanup = time.time()
_CLEANUP_INTERVAL = 300


def _check_rate_limit(ip: str):
    global _last_cleanup
    now = time.time()
    window_start = now - RATE_WINDOW

    if now - _last_cleanup > _CLEANUP_INTERVAL:
        stale = [k for k, v in _request_log.items() if not any(t > window_start for t in v)]
        for k in stale:
            del _request_log[k]
        _last_cleanup = now

    _request_log[ip] = [t for t in _request_log[ip] if t > window_start]
    if len(_request_log[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    _request_log[ip].append(now)


class QueryRequest(BaseModel):
    query: str


class CommandResult(BaseModel):
    command: str
    explanation: str
    source: str


class QueryResponse(BaseModel):
    results: list[CommandResult]


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        from rag import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL
        ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = chroma.get_collection(COLLECTION_NAME, embedding_function=ef)
        return {"pages": collection.count()}
    except Exception:
        return {"pages": None}


@app.post("/query", response_model=QueryResponse)
def query(request: Request, body: QueryRequest):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)

    if not body.query or not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = rag_query(body.query.strip())

    if not result.get("results"):
        raise HTTPException(status_code=500, detail="Failed to generate a result.")

    return QueryResponse(
        results=[
            CommandResult(
                command=r.get("command", ""),
                explanation=r.get("explanation", ""),
                source=r.get("source", ""),
            )
            for r in result["results"]
        ]
    )
