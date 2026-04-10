# CLAUDE.md — whereis my command

Natural language search across CLI documentation. You describe what you want to do
in plain English; the app returns the command and an explanation.

Portfolio project for Rick Mallery (github.com/rick-does).

---

## What This App Does

Developers and sysadmins know what they want to accomplish but can't remember which
CLI tool or command does it. This app lets them ask in plain English and get the
right command back.

**Core value proposition:** "Describe what you want to do. Get the command."

**Target users:** Developers and sysadmins. If you recognize `whereis` as a CLI
command, you're the target user.

**Public name:** whereis \<my-command\>
**npm/repo name:** whereis-my-command

---

## Architecture

### Corpus
- **Source:** tldr-pages (`tldr-pages/tldr` on GitHub) — MIT licensed, community-maintained
- ~7,000 pages (pages/ directory only, English)
- Clean, consistent format: short description + practical examples per command
- One-time ingest; incremental updates by diffing against the tldr-pages repo

### Stack
- **Embeddings:** sentence-transformers `all-MiniLM-L6-v2` (free/local, no API key)
- **Vector store:** Chroma for development; design the abstraction layer so it can be swapped to Pinecone/Weaviate for production scale-up without rewriting the query pipeline
- **RAG layer:** LangChain + Gemini 2.5 Flash (requires `GOOGLE_API_KEY`)
- **Backend:** FastAPI
- **Frontend:** Vanilla HTML/JS — function over form
- **Deployment:** Lightsail container (same pattern as md-tree demo)

### Scalability considerations
Design stateless from the start — vector store should be treated as external even if
it's currently local Chroma. This makes the swap to a hosted vector store (Pinecone etc.)
easy if traffic warrants it. API key middleware should be wired in from day one even if
keys are free initially — enables rate limiting and eventual monetization without
rearchitecting.

### API key middleware
Build it in from the start even if all keys are free. Enables:
- Rate limiting heavy users
- Future paid tiers if the service gets traction

---

## Repository Structure

```
whereis-my-command/
  ingest/           # Scripts to clone tldr-pages, embed, and store
  backend/          # FastAPI app — query endpoint, API key middleware
  frontend/         # Web UI
  data/             # Chroma vector store (gitignored)
  CLAUDE.md
```

---

## TODO

### Phase 1 — Ingest ✓
- [x] Clone tldr-pages repo
- [x] Write ingest script: walk files, chunk, embed, store in Chroma
- [x] Verify corpus is queryable

### Phase 2 — RAG layer ✓
- [x] LangChain query pipeline
- [x] Prompt engineering: natural language in → 3-5 ranked commands + explanations out
- [x] Prefer common/linux platform; pass platform metadata to LLM
- [x] Test with representative queries

### Phase 3 — Backend ✓
- [x] FastAPI app with `/query` endpoint
- [x] `/health` endpoint
- [x] Rate limiting (per IP; API key middleware deferred until traffic warrants it)

### Phase 4 — Frontend ✓
- [x] Simple web UI: text input, results display
- [x] Show command, explanation, and source (tldr-pages attribution)
- [x] Returns 3-5 ranked results per query
- [x] Per-result Copy button

### Phase 5 — Deploy ✓
- [x] Dockerfile — multi-stage build; Chroma + model cache baked in at build time
- [x] Deploy to Lightsail container (container-service-1, Micro, us-west-2)
- [x] GitHub Actions CI — smoke-tests /health on every push to main

### Phase 6 — Polish
- [x] README with examples and screenshots
- [x] CI badge
- [ ] Add to rick-does org-readme and resume

---

## Rules
- Never add comments or docstrings to code that wasn't changed
- Never add features beyond what was asked
- Don't create new files to document changes — edit existing files or nothing
