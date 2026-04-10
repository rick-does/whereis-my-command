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
- ~3,000-4,000 command files, each 200-400 tokens
- Clean, consistent format: short description + practical examples per command
- One-time ingest; incremental updates by diffing against the tldr-pages repo

### Stack
- **Embeddings:** OpenAI `text-embedding-3-small` (cheap) or sentence-transformers (free/local)
- **Vector store:** Chroma for development; design the abstraction layer so it can be swapped to Pinecone/Weaviate for production scale-up without rewriting the query pipeline
- **RAG layer:** LangChain
- **Backend:** FastAPI
- **Frontend:** Simple React or plain HTML — function over form
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

### Phase 1 — Ingest
- [ ] Clone tldr-pages repo
- [ ] Write ingest script: walk files, chunk, embed, store in Chroma
- [ ] Verify corpus is queryable

### Phase 2 — RAG layer
- [ ] LangChain query pipeline
- [ ] Prompt engineering: natural language in → command + explanation out
- [ ] Test with representative queries

### Phase 3 — Backend
- [ ] FastAPI app with `/query` endpoint
- [ ] API key middleware (wired in, keys free for now)
- [ ] `/health` endpoint
- [ ] Rate limiting

### Phase 4 — Frontend
- [ ] Simple web UI: text input, results display
- [ ] Show command, explanation, and source (tldr-pages attribution)

### Phase 5 — Deploy
- [ ] Dockerfile — stateless container, Chroma baked in at build time for now
- [ ] Deploy to Lightsail container
- [ ] GitHub Actions CI

### Phase 6 — Polish
- [ ] README with examples and screenshots
- [ ] Documentation
- [ ] Add to rick-does org-readme and resume

---

## Rules
- Never add comments or docstrings to code that wasn't changed
- Never add features beyond what was asked
- Don't create new files to document changes — edit existing files or nothing
