# Multimodal RAG System Challenge

This repository contains the solution for the Multimodal RAG System Challenge (PS ID: GITACVPS004). It is a robust system capable of ingesting Text (PDF), Audio (MP3/WAV), and Images (Charts), storing them in a unified vector database, and answering queries with strict citations and conflict detection.

## Key Features

1.  **Unified Storage**: All modalities are indexed in a single ChromaDB instance.
2.  **Strict Citations**: Every claim is cited with `[Source: filename at timestamp/page]`.
3.  **Conflict Detection**: The system explicitly detects and reports contradictions between sources (e.g., Audio vs PDF).
4.  **Transparent Reasoning**: The Frontend shows the exact chunks retrieved for every answer.

## Tech Stack

-   **Backend**: Python (FastAPI), LangChain, ChromaDB.
-   **AI Engines**: OpenAI GPT-4o (Reasoning & Vision), Whisper (Audio), OpenAI Embeddings.
-   **Frontend**: React.js with Tailwind CSS.

## Setup & Running

### Prerequisites
-   Python 3.10+
-   Node.js & npm
-   OpenAI API Key

### Backend
1.  Navigate to the root directory.
2.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
3.  Set your API Key:
    ```bash
    export OPENAI_API_KEY="your-sk-..."
    ```
4.  Run the server:
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The API will be available at `http://localhost:8000`.

### Frontend
1.  Navigate to the `frontend` folder:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm start
    ```
    The app will run at `http://localhost:3000`.

## Architecture Details

### Conflict Detection Strategy
The system uses a unique "Judge" prompt in `backend/rag.py`. When retrieval happens, the LLM is instructed to:
1.  Analyze all retrieved chunks.
2.  Identify mutually exclusive claims.
3.  If a conflict exists, output: "**CONFLICT DETECTED**: Source A claims X, while Source B claims Y."

### Strict Citations
The ingestion pipeline (`backend/ingest.py`) assigns a `citation_ref` metadata field to every chunk (e.g., "meeting.mp3 at 02:45"). The LLM is forced via system prompt to append this reference to every generated sentence.

### Frontend Logic
The React app parses the LLM's response for `[Source: ...]` tags. These are converted into clickable elements. If the source is an audio file with a timestamp, the frontend parses the time (e.g., "02:30") and seeks the audio player to that point.

## Deliverables Checklist
- [x] Unified Storage (ChromaDB)
- [x] Strict Citations (Implemented in Prompts & Metadata)
- [x] Conflict Detection (Implemented in Judge Logic)
- [x] React Frontend Architecture
- [x] Backend API (FastAPI)
