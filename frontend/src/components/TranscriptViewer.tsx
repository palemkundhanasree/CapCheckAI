import React from 'react';
import { Mic, Clock, Quote } from 'lucide-react';

interface TranscriptViewerProps {
  transcript?: string;
  segments?: Array<{ start: number; end: number; text: string }>;
}

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({ transcript, segments = [] }) => {
  if (!transcript) return null;

  return (
    <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm space-y-4">
      <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100">
        <div className="p-1.5 rounded-md bg-blue-50 text-blue-600">
          <Mic className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">Audio Speech Transcription</h3>
          <p className="text-xs text-slate-500">Decoded verbal dialogue extracted from the audio track</p>
        </div>
      </div>

      {segments.length > 0 ? (
        <div className="space-y-2">
          {segments.map((seg, idx) => (
            <div key={idx} className="flex items-start space-x-3 p-3 rounded-md bg-slate-50 border border-slate-100">
              <span className="flex items-center space-x-1 text-[11px] font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200 flex-shrink-0">
                <Clock className="w-3 h-3 text-slate-400" />
                <span>{seg.start}s - {seg.end}s</span>
              </span>
              <p className="text-xs text-slate-800 leading-relaxed">
                "{seg.text}"
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-3.5 rounded-md bg-slate-50 border border-slate-100 text-xs text-slate-800 leading-relaxed italic">
          "{transcript}"
        </div>
      )}
    </div>
  );
};
