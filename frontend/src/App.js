import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import EvidenceViewer from './components/EvidenceViewer';

function App() {
  const [activeEvidence, setActiveEvidence] = useState(null);

  // Layout: Left 40% Chat, Right 60% Evidence
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-zinc-950">

      {/* Left Panel: Chat Interface */}
      <div className="w-[40%] h-full border-r border-zinc-800">
        <ChatInterface onEvidenceClick={setActiveEvidence} />
      </div>

      {/* Right Panel: Evidence Viewer */}
      <div className="w-[60%] h-full">
        <EvidenceViewer activeEvidence={activeEvidence} />
      </div>

    </div>
  );
}

export default App;
