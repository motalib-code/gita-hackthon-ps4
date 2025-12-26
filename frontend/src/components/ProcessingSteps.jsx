import React from 'react';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';

const steps = [
  { id: 'ingest', label: 'Ingesting Documents' },
  { id: 'listen', label: 'Listening to Audio (Whisper)' },
  { id: 'vision', label: 'Analyzing Charts (Vision)' },
  { id: 'conflict', label: 'Checking for Conflicts' },
  { id: 'generate', label: 'Generating Answer' },
];

export default function ProcessingSteps({ currentStep }) {
  // currentStep could be 'ingest', 'listen', etc., or 'done'

  const getStatus = (stepId) => {
    const stepIndex = steps.findIndex(s => s.id === stepId);
    const currentIndex = steps.findIndex(s => s.id === currentStep);

    if (currentStep === 'done') return 'completed';
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-4 shadow-lg">
      <h3 className="text-zinc-400 text-xs font-bold uppercase tracking-wider mb-3">
        Reasoning Engine
      </h3>
      <div className="space-y-3">
        {steps.map((step) => {
          const status = getStatus(step.id);
          return (
            <div key={step.id} className="flex items-center gap-3">
              {status === 'completed' && (
                <CheckCircle className="w-4 h-4 text-emerald-500" />
              )}
              {status === 'active' && (
                <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
              )}
              {status === 'pending' && (
                <Circle className="w-4 h-4 text-zinc-700" />
              )}

              <span className={`text-sm ${
                status === 'active' ? 'text-blue-400 font-medium' :
                status === 'completed' ? 'text-zinc-300' : 'text-zinc-600'
              }`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
