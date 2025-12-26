import React, { useState, useEffect } from 'react';
import { FileText, Music, Image as ImageIcon } from 'lucide-react';

export default function EvidenceViewer({ activeEvidence }) {
  // activeEvidence format: { type: 'pdf' | 'audio' | 'image', url: string, timestamp?: number }
  const [activeTab, setActiveTab] = useState('pdf');

  // Auto-switch tab when evidence is clicked in chat
  useEffect(() => {
    if (activeEvidence?.type) {
      setActiveTab(activeEvidence.type);
    }
  }, [activeEvidence]);

  return (
    <div className="flex flex-col h-full bg-zinc-950 border-l border-zinc-800">
      {/* Tabs Header */}
      <div className="flex items-center border-b border-zinc-800 bg-zinc-900">
        <TabButton
          active={activeTab === 'pdf'}
          onClick={() => setActiveTab('pdf')}
          icon={<FileText size={16} />}
          label="Documents (PDF)"
        />
        <TabButton
          active={activeTab === 'audio'}
          onClick={() => setActiveTab('audio')}
          icon={<Music size={16} />}
          label="Audio Recordings"
        />
        <TabButton
          active={activeTab === 'image'}
          onClick={() => setActiveTab('image')}
          icon={<ImageIcon size={16} />}
          label="Visual Data"
        />
      </div>

      {/* Content Area */}
      <div className="flex-1 p-6 overflow-hidden relative">
        <div className="absolute inset-0 p-6 overflow-auto">

          {activeTab === 'pdf' && (
             <div className="h-full flex flex-col items-center justify-center text-zinc-500 border-2 border-dashed border-zinc-800 rounded-xl bg-zinc-900/50">
               {activeEvidence?.type === 'pdf' ? (
                 <iframe
                   src={activeEvidence.url}
                   className="w-full h-full rounded shadow-lg"
                   title="PDF Viewer"
                 />
               ) : (
                 <>
                   <FileText size={48} className="mb-4 opacity-20" />
                   <p>Select a citation to view the PDF source.</p>
                 </>
               )}
             </div>
          )}

          {activeTab === 'audio' && (
            <div className="h-full flex flex-col items-center justify-center bg-zinc-900/50 rounded-xl border border-zinc-800 p-8">
              {activeEvidence?.type === 'audio' ? (
                <div className="w-full max-w-md">
                   <div className="mb-8 text-center">
                     <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto flex items-center justify-center shadow-2xl animate-pulse">
                        <Music className="text-white w-10 h-10" />
                     </div>
                     <h3 className="mt-6 text-zinc-200 text-lg font-medium">Meeting Recording.mp3</h3>
                     <p className="text-zinc-500 text-sm">Timestamp: {formatTime(activeEvidence.timestamp || 0)}</p>
                   </div>

                   <audio
                     key={activeEvidence.timestamp} // Force re-render on seek
                     controls
                     autoPlay
                     className="w-full"
                     ref={(el) => {
                       if(el && activeEvidence.timestamp) el.currentTime = activeEvidence.timestamp;
                     }}
                   >
                     {/* In a real app, use the actual URL */}
                     <source src={activeEvidence.url || "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"} type="audio/mpeg" />
                     Your browser does not support the audio element.
                   </audio>
                </div>
              ) : (
                <div className="text-zinc-500 flex flex-col items-center">
                   <Music size={48} className="mb-4 opacity-20" />
                   <p>No audio citation selected.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'image' && (
            <div className="h-full flex items-center justify-center">
               {activeEvidence?.type === 'image' ? (
                 <img
                   src={activeEvidence.url}
                   alt="Evidence"
                   className="max-h-full max-w-full rounded shadow-2xl border border-zinc-700"
                 />
               ) : (
                  <div className="text-zinc-500 flex flex-col items-center">
                   <ImageIcon size={48} className="mb-4 opacity-20" />
                   <p>No visual evidence selected.</p>
                  </div>
               )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-6 py-4 text-sm font-medium transition-colors border-r border-zinc-800 ${
        active
          ? 'bg-zinc-800 text-white border-b-2 border-b-blue-500'
          : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
