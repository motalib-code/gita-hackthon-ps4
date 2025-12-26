from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

# Initialize Vector Store using Google Gemini Embeddings
# Using "models/text-embedding-004" which is a strong embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

PERSIST_DIRECTORY = "./backend/chroma_db"

def get_vector_store():
    return Chroma(
        collection_name="hackathon_rag",
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

def add_documents(documents):
    vector_store = get_vector_store()
    vector_store.add_documents(documents)
    return len(documents)

def query_documents(query, k=5):
    vector_store = get_vector_store()
    # Using MMR to get diverse results
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": 20}
    )
    return retriever.invoke(query)
