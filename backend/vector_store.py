import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
import shutil

PERSIST_DIRECTORY = "./backend/chroma_db"

def get_embeddings():
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return OpenAIEmbeddings(model="text-embedding-3-small")

def get_vector_store():
    # Ensure directory exists
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
    return Chroma(
        collection_name="hackathon_rag",
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIRECTORY
    )

def add_documents(documents):
    if not documents:
        return 0

    vector_store = get_vector_store()

    # 1. Idempotency Check: Remove existing chunks for these sources
    sources = list(set(doc.metadata.get("source") for doc in documents if doc.metadata.get("source")))

    if sources:
        try:
            # Note: Chroma deletion by metadata
            vector_store._collection.delete(where={"source": {"$in": sources}})
            print(f"Removed existing chunks for sources: {sources}")
        except Exception as e:
            # Fallback for single source or older chroma versions
            for source in sources:
                try:
                    vector_store._collection.delete(where={"source": source})
                except Exception as ex:
                    print(f"Warning: Could not delete existing chunks for {source}: {ex}")

    # 2. Add new chunks
    vector_store.add_documents(documents)
    return len(documents)

def query_documents(query, k=5):
    """
    Retrieve documents relevant to the query.
    """
    vector_store = get_vector_store()
    # Using MMR to get diverse results
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": 20}
    )
    return retriever.invoke(query)
