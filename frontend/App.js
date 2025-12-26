
import React, { useState, useRef } from 'react';
import { Upload, FileText, Mic, Image as ImageIcon, AlertTriangle, Play, Pause } from 'lucide-react';

const API_URL = "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sources, setSources] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const audioRef = useRef(null);

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      alert(data.message);
    } catch (error) {
      console.error("Upload failed", error);
      alert("Upload failed!");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    setMessages([...messages, userMsg]);
    setInput("");

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      });
      const data = await response.json();

      const aiMsg = { role: "ai", text: data.answer };
      setMessages((prev) => [...prev, aiMsg]);
      setSources(data.sources);
    } catch (error) {
      console.error("Query failed", error);
    }
  };

  const parseTextWithCitations = (text) => {
    // Regex to find [Source: ...]
    const parts = text.split(/(\[Source:.*?\])/g);
    return parts.map((part, index) => {
      if (part.startsWith("[Source:") && part.endsWith("]")) {
        const sourceContent = part.replace("[Source: ", "").replace("]", "");
        return (
          <span
            key={index}
            className="text-blue-500 cursor-pointer underline ml-1"
            onClick={() => handleCitationClick(sourceContent)}
          >
            {part}
          </span>
        );
      }
      return part;
    });
  };

  const handleCitationClick = (source) => {
    console.log("Clicked source:", source);
    // Logic to play audio if source contains timestamp
    // e.g., "meeting.mp3 at 02:30"
    if (source.includes("at")) {
        const parts = source.split(" at ");
        const timeStr = parts[1];
        // Parse "02:30" -> seconds
        const [min, sec] = timeStr.split(":").map(Number);
        const seconds = min * 60 + sec;

        // In a real app, map filename to URL.
        // For demo, assuming we have one audio player.
        if (audioRef.current) {
            audioRef.current.currentTime = seconds;
            audioRef.current.play();
        }
        alert(`Jumping to ${timeStr} in audio player`);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      {/* Sidebar: Transparent Reasoning */}
      <div className="w-1/4 bg-white p-4 border-r overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Transparent Reasoning</h2>
        <div className="space-y-4">
          {sources.map((src, idx) => (
            <div key={idx} className="p-3 border rounded shadow-sm bg-gray-50">
              <div className="flex items-center gap-2 mb-2">
                {src.type === 'audio' && <Mic size={16} />}
                {src.type === 'pdf' && <FileText size={16} />}
                {src.type === 'image' && <ImageIcon size={16} />}
                <span className="font-semibold text-sm truncate">{src.source}</span>
              </div>
              <p className="text-xs text-gray-600 mb-2">
                {src.citation_ref}
              </p>
              <div className="text-xs bg-gray-200 p-1 rounded truncate">
                Chunk ID: {idx}
              </div>
            </div>
          ))}
          {sources.length === 0 && <p className="text-gray-500">No context retrieved yet.</p>}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white text-gray-800 shadow'}`}>
                {msg.role === 'ai' ? parseTextWithCitations(msg.text) : msg.text}
              </div>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t">
          <div className="flex gap-2">
             <label className="p-2 bg-gray-200 rounded cursor-pointer hover:bg-gray-300">
                <Upload size={20} />
                <input type="file" className="hidden" onChange={handleUpload} disabled={isUploading} />
             </label>
             <input
                type="text"
                className="flex-1 border rounded p-2"
                placeholder="Ask a question about your files..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
             />
             <button
                onClick={handleSend}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
             >
                Send
             </button>
          </div>
          {isUploading && <p className="text-xs text-blue-600 mt-2">Uploading and processing...</p>}
        </div>
      </div>

      {/* Hidden Audio Player for Demo */}
      <audio ref={audioRef} controls className="hidden" />
    </div>
  );
}
