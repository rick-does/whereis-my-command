import os
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from rag import query as rag_query

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "20"))
RATE_WINDOW = 60

app = FastAPI(title="whereis <my-command>")

_request_log: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str):
    now = time.time()
    window_start = now - RATE_WINDOW
    timestamps = _request_log[ip]
    _request_log[ip] = [t for t in timestamps if t > window_start]
    if len(_request_log[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    _request_log[ip].append(now)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    command: str
    explanation: str
    source: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: Request, body: QueryRequest):
    ip = request.client.host
    _check_rate_limit(ip)

    if not body.query or not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = rag_query(body.query.strip())

    if "command" not in result or "explanation" not in result:
        raise HTTPException(status_code=500, detail="Failed to generate a result.")

    return QueryResponse(
        command=result["command"],
        explanation=result["explanation"],
        source=result.get("source", ""),
    )
