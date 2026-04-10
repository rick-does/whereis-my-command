# whereis \<my-command\>

Natural language search across [tldr-pages](https://github.com/tldr-pages/tldr) CLI documentation.

You describe what you want to do. You get the command.

---

## What it does

Developers and sysadmins know what they want to accomplish but can't always remember
which tool or flag does it. `whereis <my-command>` lets you ask in plain English and
returns the right command with a plain-English explanation.

**Example queries:**

- _"recursively find files modified in the last 24 hours"_
- _"watch a log file and filter for errors"_
- _"list open ports on this machine"_

Powered by [tldr-pages](https://github.com/tldr-pages/tldr), sentence-transformers, and a RAG pipeline.

---

## Status

Under construction.

---

## Stack

- **Corpus:** tldr-pages (~3,000 commands, MIT licensed)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector store:** Chroma
- **RAG:** LangChain
- **Backend:** FastAPI
- **Frontend:** HTML/JS

---

## License

MIT
