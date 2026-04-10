import subprocess
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

TLDR_REPO = "https://github.com/tldr-pages/tldr.git"
DATA_DIR = Path(__file__).parent.parent / "data"
TLDR_DIR = DATA_DIR / "tldr-pages"
CHROMA_DIR = DATA_DIR / "chroma"
COLLECTION_NAME = "tldr"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 100


def clone_or_pull():
    if TLDR_DIR.exists():
        print("Updating tldr-pages...")
        subprocess.run(["git", "-C", str(TLDR_DIR), "pull"], check=True)
    else:
        print("Cloning tldr-pages...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth=1", TLDR_REPO, str(TLDR_DIR)], check=True
        )


def load_pages():
    pages_dir = TLDR_DIR / "pages"
    docs = []
    for platform_dir in sorted(pages_dir.iterdir()):
        if not platform_dir.is_dir():
            continue
        platform = platform_dir.name
        for md_file in sorted(platform_dir.glob("*.md")):
            command = md_file.stem
            content = md_file.read_text(encoding="utf-8")
            docs.append(
                {
                    "id": f"{platform}/{command}",
                    "text": content,
                    "metadata": {"command": command, "platform": platform},
                }
            )
    return docs


def embed_and_store(docs):
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        chroma.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma.create_collection(COLLECTION_NAME, embedding_function=ef)

    print(f"Embedding {len(docs)} documents...")
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        collection.add(
            ids=[d["id"] for d in batch],
            documents=[d["text"] for d in batch],
            metadatas=[d["metadata"] for d in batch],
        )
        print(f"  {min(i + BATCH_SIZE, len(docs))}/{len(docs)}")

    print(f"Stored {len(docs)} documents in Chroma at {CHROMA_DIR}")


def verify(query="list files in a directory"):
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma.get_collection(COLLECTION_NAME, embedding_function=ef)

    results = collection.query(query_texts=[query], n_results=3)

    print(f"\nVerification query: '{query}'")
    for i, (doc_id, doc) in enumerate(zip(results["ids"][0], results["documents"][0])):
        print(f"\n--- Result {i+1}: {doc_id} ---")
        print(doc[:300])


if __name__ == "__main__":
    clone_or_pull()
    docs = load_pages()
    print(f"Found {len(docs)} pages")
    embed_and_store(docs)
    verify()
