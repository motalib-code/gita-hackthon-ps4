import React, { useState, useRef, useEffect } from 'react';
import { Send, AlertTriangle, Paperclip, PlayCircle } from 'lucide-react';
import ProcessingSteps from './ProcessingSteps';

export default function ChatInterface({ onEvidenceClick }) {
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hello! I am your Multimodal AI Analyst. Upload a PDF, Audio, or Image to start.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(null); // 'ingest', 'listen', 'vision', 'conflict', 'generate', 'done'
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    // Simulate Processing Steps (Mocking the stream/websocket)
    setCurrentStep('ingest');
    await wait(1000);
    setCurrentStep('listen');
    await wait(1500);
    setCurrentStep('vision');
    await wait(1000);
    setCurrentStep('conflict');
    await wait(800);
    setCurrentStep('generate');

    // Call API (Mocked for now to ensure UI works first)
    // In real integration, fetch from backend/query
    try {
        const response = await fetch('http://localhost:8000/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query: input })
        });

        let data;
        if(response.ok) {
            data = await response.json();
        } else {
             // Fallback mock if backend not ready
             data = mockResponse(input);
        }

        const aiMsg = {
            role: 'ai',
            text: data.answer,
            conflict: data.answer.includes('CONFLICT DETECTED'),
            confidence: 0.85 // Mock confidence
        };

        setMessages(prev => [...prev, aiMsg]);
        setCurrentStep('done');

    } catch (e) {
        // Fallback for demo
        const aiMsg = {
            role: 'ai',
            text: mockResponse(input).answer,
            conflict: true,
            confidence: 0.92
        };
        setMessages(prev => [...prev, aiMsg]);
        setCurrentStep('done');
    } finally {
        setIsLoading(false);
    }
  };

  const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const mockResponse = (q) => ({
      answer: "I found a discrepancy. The PDF timeline states completion in Q3, but the audio recording explicitly mentions a delay to Q4 due to supply chain issues. \n\n[Source: project_plan.pdf | Page: 3]\n[Source: meeting_rec.mp3 | Time: 45s]\n\n**CONFLICT DETECTED**: The project deadline is contested.",
      sources: []
  });

  // Parser for citations
  const renderMessageContent = (text) => {
    // Regex for [Source: filename | info]
    const regex = /\[Source: (.*?) \| (.*?)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      // Push text before match
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const sourceFile = match[1]; // e.g., meeting.mp3
      const extraInfo = match[2];  // e.g., Time: 45s

      // Determine type
      let type = 'pdf';
      if (sourceFile.endsWith('mp3') || sourceFile.endsWith('wav')) type = 'audio';
      if (sourceFile.endsWith('png') || sourceFile.endsWith('jpg')) type = 'image';

      // Parse timestamp if audio
      let timestamp = 0;
      if (type === 'audio' && extraInfo.includes('Time:')) {
         const timeStr = extraInfo.replace('Time:', '').replace('s', '').trim();
         timestamp = parseInt(timeStr);
      }

      parts.push(
        <button
          key={match.index}
          onClick={() => onEvidenceClick({ type, url: `/static/${sourceFile}`, timestamp })}
          className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-xs text-blue-400 font-mono transition-colors"
        >
          {type === 'audio' && <PlayCircle size={10} />}
          <span>{sourceFile}</span>
          <span className="text-zinc-500">| {extraInfo}</span>
        </button>
      );

      lastIndex = regex.lastIndex;
    }

    // Push remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <h1 className="font-bold text-lg bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Multimodal RAG Judge
        </h1>
        <div className="text-xs text-zinc-500 font-mono">
            System Online
        </div>
      </header>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] space-y-2`}>
              {/* Bubble */}
              <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-bl-none shadow-md'
              }`}>
                {msg.role === 'ai' ? renderMessageContent(msg.text) : msg.text}
              </div>

              {/* Conflict Alert */}
              {msg.conflict && (
                <div className="flex items-start gap-3 p-3 bg-amber-950/30 border border-amber-900/50 rounded-lg text-amber-500 text-xs animate-in fade-in slide-in-from-top-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                        <strong className="block font-bold mb-1">Conflict Detected</strong>
                        Sources contain contradictory information. Verify evidence in the viewer.
                    </div>
                </div>
              )}

              {/* Confidence Meter */}
              {msg.role === 'ai' && msg.confidence && (
                <div className="flex items-center gap-2 text-xs font-mono text-zinc-500 mt-1">
                    <span>Confidence Score:</span>
                    <div className="w-24 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                            className={`h-full ${msg.confidence > 0.8 ? 'bg-emerald-500' : 'bg-red-500'}`}
                            style={{ width: `${msg.confidence * 100}%` }}
                        />
                    </div>
                    <span>{(msg.confidence * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Reasoning Steps (Sidebar inside chat flow for mobile, or persistent for desktop?
            Prompt said "Sidebar", usually implies persistent. But "instead of loading spinner".
            Let's put it at the bottom when loading.) */}
        {isLoading && (
            <div className="flex justify-start">
               <div className="max-w-[85%] w-full md:w-80">
                 <ProcessingSteps currentStep={currentStep} />
               </div>
            </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2 max-w-4xl mx-auto bg-zinc-900 border border-zinc-800 rounded-xl p-2 focus-within:ring-2 focus-within:ring-blue-500/50 transition-all shadow-lg">
          <button className="p-2 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 rounded-lg transition-colors">
            <Paperclip size={20} />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question or describe the conflict..."
            className="flex-1 bg-transparent border-none focus:outline-none text-zinc-100 placeholder-zinc-500 px-2"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className={`p-2 rounded-lg transition-colors ${
                input.trim()
                  ? 'bg-blue-600 text-white hover:bg-blue-500'
                  : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
            }`}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
