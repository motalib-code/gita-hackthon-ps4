# Frontend Architecture & Implementation Plan

## 1. Overview
The frontend is a React.js application designed to provide a clean, modern interface for the Multimodal RAG System. It emphasizes "Transparent Reasoning" and "Strict Citations".

## 2. Component Structure

### `App.js`
- Main container.
- Manages state for:
  - `messages`: List of chat messages (user and AI).
  - `isUploading`: Loading state for file uploads.
  - `ragReasoning`: Data about retrieved chunks for the sidebar.

### `Sidebar.js` (The "Transparent Reasoning View")
- **Purpose**: Shows users what the AI found *before* generating the answer.
- **Props**: `ragReasoning` (List of sources).
- **UI**:
  - Displays a list of "Evidence Chunks".
  - Icons for modality (Audio icon, PDF icon, Image icon).
  - "Conflict Check": A visual indicator showing if conflicts were detected (parsed from the AI response or a separate flag).
- **Interactivity**: Clicking a chunk shows the full text content in a modal.

### `ChatInterface.js`
- **Purpose**: Main chat area.
- **Components**:
  - `MessageList`: Renders bubbles.
  - `InputArea`: Text input + File Upload button.
- **Features**:
  - **Clickable Citations**: When the AI response contains `[Source: meeting.mp3 at 02:30]`, it is rendered as a clickable link/button.
  - **Action**: Clicking the link triggers an event. If it's audio/video, it opens a player seeking to that timestamp.

### `FileUploader.js`
- Drag & Drop zone.
- Progress bar for ingestion.

## 3. Key Feature Implementation Details

### A. Clickable Citations & Audio Playback
**Logic:**
1. **Regex Parsing**: The `Message` component parses the AI's text response using a regex like `/\[Source: (.*?)\]/g`.
2. **Replacement**: Replaces the text with a `<CitationBadge source={match} />` component.
3. **Handling Click**:
   ```javascript
   const handleCitationClick = (sourceString) => {
       // sourceString example: "meeting.mp3 at 02:30"
       const [filename, timestamp] = parseSource(sourceString);
       if (filename.endsWith('.mp3')) {
           const seconds = convertTimestampToSeconds(timestamp);
           audioPlayerRef.current.src = getFileUrl(filename);
           audioPlayerRef.current.currentTime = seconds;
           audioPlayerRef.current.play();
       }
   };
   ```

### B. Conflict Detection Visualization
**Logic:**
- The backend returns the answer.
- If the answer contains specific keywords like "**CONFLICT DETECTED**", the frontend highlights this section in **Red** or **Yellow** to alert the user.

## 4. API Integration (React Hooks)

- `useUpload`:
  - `POST /upload` (multipart/form-data).
- `useQuery`:
  - `POST /query` (JSON: `{ query: "..." }`).
  - Response: `{ answer: "...", sources: [...] }`.
  - Updates `messages` and `ragReasoning` state.

## 5. Edge Case Handling (Frontend)
- **Upload Failures**: Show toast notifications ("File corrupted" or "Format not supported").
- **Empty Retrieval**: If `sources` is empty, show "No relevant documents found" in the Sidebar.

## 6. Styling
- **Tailwind CSS** for rapid UI development.
- **Lucide React** for icons.
