# Multimodal RAG System - Detailed Design Document

## 1. System Architecture & Workflow

### Workflow
1.  **User Upload**: Users upload files (PDF, MP3/WAV, JPG/PNG) via the React Frontend.
2.  **Ingestion API**: The Frontend sends files to the FastAPI backend (`/upload`).
3.  **Data Processing**:
    *   **PDF**: Parsed into text chunks using `PyPDFLoader`.
    *   **Audio**: Uploaded to **Google Gemini 1.5 Flash**. The model listens to the audio, transcribes it, and segments it with timestamps (`[START: MM:SS]`).
    *   **Images**: Sent to **Google Gemini 1.5 Flash**. The model analyzes charts/diagrams and generates a detailed text description.
4.  **Vectorization**: All text (from PDF, Audio transcripts, Image descriptions) is embedded using **Google Gemini Embeddings** (`models/text-embedding-004`).
5.  **Unified Vector Store**: Embeddings + Metadata are stored in **ChromaDB**.
6.  **Query Handling**:
    *   User asks a question.
    *   System retrieves top-k relevant chunks (Text/Audio/Image sources) from ChromaDB.
7.  **Conflict Detection & Generation**:
    *   The "Judge" LLM (Gemini 1.5 Flash) receives the retrieved chunks.
    *   It analyzes them for contradictions (e.g., Audio says "X", PDF says "Not X").
    *   It generates a final answer with **Strict Citations** (`[Source: file.mp3 at 02:30]`).

### Unified Vector Storage Strategy
To handle multimodal data in a single store, we convert everything to **Text** first:
*   **Audio** -> Text Transcript (with timestamp markers).
*   **Image** -> Text Description (capturing data points, trends, and visual elements).
*   **PDF** -> Raw Text.
Once everything is text, they share the same vector space (Gemini Embeddings), allowing a single query to retrieve relevant content from a video, a chart, or a document simultaneously.

---

## 2. Backend Logic (Python/FastAPI)

### Folder Structure
```
backend/
├── main.py            # FastAPI Entrypoint & Static File Serving
├── ingest.py          # Multimodal Ingestion (Gemini Logic)
├── rag.py             # "Judge" Logic & Conflict Detection
├── vector_store.py    # ChromaDB Wrapper
├── data_store/        # Persistent storage for uploaded files
└── requirements.txt   # Dependencies
```

### Ingestion Pipeline (Pseudo-Code / Logic)
```python
def process_audio(file_path):
    # 1. Upload to Gemini
    file = genai.upload_file(file_path)

    # 2. Prompt for Structured Transcription
    prompt = "Transcribe and segment with [START: MM:SS] tags."
    response = model.generate_content([file, prompt])

    # 3. Parse Response
    segments = parse_segments(response.text) # Returns list of chunks with timestamps
    return segments

def process_image(file_path):
    # 1. Analyze with Vision Model
    response = model.generate_content(["Describe this chart in detail", image_file])
    return response.text
```

### Critical Winning Feature: Conflict Detection Prompt
The system uses the following System Prompt for the LLM:

```text
You are an expert AI Analyst and Judge.
Your goal is to answer the user's query based ONLY on the provided context chunks.

CRITICAL RULES:
1. **Strict Citations**: You MUST cite the source for every claim. Format: `[Source: <citation_ref>]`.
   - Example: "Revenue increased by 5% [Source: meeting.mp3 at 04:20]."

2. **Conflict Detection**: You must actively look for contradictions.
   - If Source A says "Revenue up" and Source B says "Revenue down", you MUST report:
     "**CONFLICT DETECTED**: Source A claims revenue is up [Source: A], while Source B claims it is down [Source: B]."
   - Do NOT merge conflicting facts. Expose them.

3. **Adversarial Handling**: If the answer is not in the context, say "I don't know".
```

---

## 3. Database Schema & Metadata Design

Chunks in ChromaDB follow this JSON structure in their `metadata` field:

```json
{
  "source": "financial_report.pdf",       // Original Filename
  "type": "pdf",                          // 'pdf' | 'audio' | 'image'
  "citation_ref": "financial_report.pdf Page 2", // Display string for citation
  "timestamp": "02:30",                   // Only for Audio (optional)
  "page": 2,                              // Only for PDF (optional)
  "media_url": "/static/financial_report.pdf" // URL to serve the file
}
```

---

## 4. Frontend Design (React Component Logic)

### UI Layout
*   **Split Screen**:
    *   **Left (60%)**: Chat Interface. Bubbles for User and AI.
    *   **Right (40%)**: "Transparent Reasoning" Sidebar / Evidence Viewer.

### Features
1.  **Clickable Citations**:
    *   **Logic**: Regex parses `[Source: meeting.mp3 at 02:30]`.
    *   **Action**: `onClick` parses "02:30" -> 150 seconds. Sets `audioRef.current.currentTime = 150` and plays.
2.  **Reasoning Trace**:
    *   The Sidebar updates in real-time (mocked or via WebSocket in production) to show:
        *   "Found 3 relevant chunks..."
        *   "Analyzing Image #2..."
        *   "Conflict Check: PASSED/FAILED"

---

## 5. Error Handling & Anti-Hallucination

### Corrupt File Uploads
*   **Defense**: Use `python-magic` to verify file MIME types before processing.
*   **Fallback**: Wrap ingestion in `try/except`. If Gemini fails to process an audio file (e.g., encoding error), return a specific error message to the UI: "Audio processing failed. Please check file format."

### Anti-Hallucination
*   **Prompt Engineering**: The "Judge" prompt explicitly forbids using outside knowledge.
*   **Low Confidence**: If the retrieval step returns chunks with low similarity scores (distance > threshold), the system preemptively answers "I couldn't find relevant information in your documents."

### API Timeouts
*   **Retry Logic**: The backend uses exponential backoff (via `tenacity` library) when calling Google Gemini APIs.
*   **User Feedback**: The Frontend displays a "Thinking..." spinner to indicate deep processing, preventing users from assuming the app froze.
