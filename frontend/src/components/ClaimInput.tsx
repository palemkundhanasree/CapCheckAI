import React, { useState } from 'react';
import { Send, AlertCircle, Sparkles } from 'lucide-react';
import { DEMO_PRESETS } from '../services/demoData';

interface ClaimInputProps {
  onSubmit: (claimText: string, context?: string) => void;
  isLoading: boolean;
}

export const ClaimInput: React.FC<ClaimInputProps> = ({ onSubmit, isLoading }) => {
  const [claim, setClaim] = useState('');
  const [context, setContext] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!claim.trim() || claim.trim().length < 5) {
      setError('Please enter at least 5 characters for the claim statement.');
      return;
    }
    setError(null);
    onSubmit(claim.trim(), context.trim() || undefined);
  };

  const loadPreset = (presetText: string) => {
    setClaim(presetText);
    setError(null);
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Statement or Claim to Fact-Check
          </label>
          <textarea
            value={claim}
            onChange={(e) => {
              setClaim(e.target.value);
              if (error) setError(null);
            }}
            placeholder="Type or paste any statement (e.g. 'The Earth orbits around the Sun', 'Drinking bleach cures COVID', 'Water boils at 100 degrees Celsius')..."
            rows={4}
            className="w-full p-3 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-colors"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Origin / Context (Optional)
          </label>
          <input
            type="text"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="e.g. Social media post, WhatsApp forward, news conference"
            className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-colors"
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-xs text-red-700 bg-red-50 p-3 rounded-lg border border-red-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading || !claim.trim()}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
        >
          <Send className="w-4 h-4" />
          <span>{isLoading ? 'Verifying with Official Records...' : 'Verify Claim Now'}</span>
        </button>
      </form>

      {/* Preset Quick Test Buttons */}
      <div className="pt-4 border-t border-slate-100">
        <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600 mb-2">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Click a pre-verified statement to test:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {DEMO_PRESETS.map((demo) => (
            <button
              key={demo.id}
              type="button"
              onClick={() => loadPreset(demo.input)}
              className="text-xs px-2.5 py-1.5 rounded-md bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors cursor-pointer"
            >
              {demo.title}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
