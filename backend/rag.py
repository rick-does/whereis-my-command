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
TOP_K = 5

PROMPT = ChatPromptTemplate.from_template(
    "You are a CLI command assistant. A user wants to accomplish something on the "
    "command line but doesn't know the exact command.\n\n"
    "Given the user's goal and relevant CLI documentation pages, identify the best "
    "command and explain how to use it.\n\n"
    "User's goal: {query}\n\n"
    "Relevant documentation:\n{context}\n\n"
    "Respond in this exact format:\n"
    "Command: <the command, with typical flags if helpful>\n"
    "Explanation: <plain English explanation of what it does>\n"
    "Source: <command name>"
)


def query(user_query: str) -> dict:
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma.get_collection(COLLECTION_NAME, embedding_function=ef)

    results = collection.query(query_texts=[user_query], n_results=TOP_K)
    context = "\n\n---\n\n".join(results["documents"][0])

    llm = ChatGoogleGenerativeAI(model=LLM_MODEL)
    response = (PROMPT | llm).invoke({"query": user_query, "context": context})

    result = {"query": user_query, "raw": response.content}
    for line in response.content.splitlines():
        if line.startswith("Command:"):
            result["command"] = line.split(":", 1)[1].strip()
        elif line.startswith("Explanation:"):
            result["explanation"] = line.split(":", 1)[1].strip()
        elif line.startswith("Source:"):
            result["source"] = line.split(":", 1)[1].strip()

    return result


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "recursively find files modified in the last 24 hours"
    result = query(q)
    print(f"Command:     {result.get('command', 'N/A')}")
    print(f"Explanation: {result.get('explanation', 'N/A')}")
    print(f"Source:      {result.get('source', 'N/A')}")
