# whereis \<my-command\>

Natural language search across [tldr-pages](https://github.com/tldr-pages/tldr) CLI documentation.

You describe what you want to do. You get the command.

---

## What it does

Developers and sysadmins know what they want to accomplish but can't always remember
which tool or flag does it. `whereis <my-command>` lets you ask in plain English and
returns the right command with a plain-English explanation.

Queries return 3–5 ranked results, from most common to most specialized, so both the
standard answer and the edge cases surface.

**Example queries:**

- _"recursively find files modified in the last 24 hours"_
- _"watch a log file and filter for errors"_
- _"list open ports on this machine"_
- _"copy files over SSH"_
- _"show disk usage sorted by size"_

Defaults to Linux/common commands. Add _on macOS_, _on Windows_, _on Android_, etc.
to target a specific platform.

Powered by [tldr-pages](https://github.com/tldr-pages/tldr), sentence-transformers, and a RAG pipeline.

---

## Status

Working locally. Deployment coming soon.

---

## Stack

- **Corpus:** tldr-pages (~7,000 pages, MIT licensed)
- **Embeddings:** sentence-transformers `all-MiniLM-L6-v2` (local, no API key required)
- **Vector store:** Chroma
- **RAG:** LangChain + Gemini 2.5 Flash
- **Backend:** FastAPI with per-IP rate limiting
- **Frontend:** Vanilla HTML/JS

---

## Running locally

**1. Ingest the corpus** (one-time, re-run to update):

```bash
cd ingest
pip install -r requirements.txt
python ingest.py
```

**2. Start the backend:**

```bash
cd backend
pip install -r requirements.txt
GOOGLE_API_KEY=your-key uvicorn main:app --reload
```

Open `http://localhost:8000`.

---

## License

MIT
