from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import uvicorn
import os
import shutil
from backend.ingest import process_file_from_path
from backend.rag import answer_query

app = FastAPI(title="Multimodal RAG System")

# Setup static directory for serving media files
UPLOAD_DIR = "backend/data_store"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save file persistently for frontend access
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Re-open file for ingestion (since pointer moved)
        with open(file_path, "rb") as f:
            # Create a mock object that behaves like UploadFile for the ingest function
            # Or better, update ingest to take a path.
            # For now, let's adapt ingest to take the path directly or handle it there.
            # But `ingest_file` expects a file-like object or UploadFile.
            # Let's modify `ingest_file` to accept the path, or just pass the path.

            # Actually, looking at `ingest_file` in `ingest.py`, it copies content to a temp file.
            # We can optimize this by passing the path we just saved.

            from backend.ingest import process_file_from_path
            docs = process_file_from_path(file_path, file.filename)

        if not docs:
            return {"message": "File processed but no content extracted (or unsupported type)."}

        # Add to vector store
        from backend.vector_store import add_documents
        count = add_documents(docs)

        return {"message": f"Successfully ingested {file.filename}", "chunks_added": count, "url": f"/static/{file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        result = answer_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Multimodal RAG Backend is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
