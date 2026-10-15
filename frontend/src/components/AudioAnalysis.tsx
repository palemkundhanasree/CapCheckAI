import React from 'react';
import { Volume2, Mic, Activity } from 'lucide-react';
import { MediaAnalysisDetail } from '../types';

interface AudioAnalysisProps {
  analysis: MediaAnalysisDetail;
}

export const AudioAnalysis: React.FC<AudioAnalysisProps> = ({ analysis }) => {
  const audio = analysis.audio_findings || {};
  const waveform = audio.waveform || {};
  const consistency = audio.speaker_consistency || {};
  const isSynthetic = analysis.ai_generated_score >= 50;

  return (
    <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
            <Volume2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Audio Forensics & Synthetic Speech Analysis</h3>
            <p className="text-xs text-slate-500">Checking for neural voice cloning, spectral dynamic range, and ambient microphone noise</p>
          </div>
        </div>
        <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
          isSynthetic 
            ? 'bg-red-100 text-red-800 border-red-200' 
            : 'bg-green-100 text-green-800 border-green-200'
        }`}>
          {isSynthetic ? `AI Voice Clone (${Math.round(analysis.ai_generated_score)}%)` : `Natural Human Voice`}
        </span>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Dynamic Range</div>
          <div className="text-sm font-bold text-slate-900">
            {waveform.dynamic_range_db ? `${waveform.dynamic_range_db} dB Dynamic Variance` : 'Natural Modulation'}
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            {waveform.dynamic_range_db && waveform.dynamic_range_db < 10
              ? 'Compressed volume profile characteristic of text-to-speech vocoders.'
              : 'Natural volume variations between emphasized words and unstressed syllables.'}
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Acoustic Room Resonance</div>
          <div className="text-sm font-bold text-slate-900">
            {waveform.noise_floor_db && waveform.noise_floor_db < -65 ? (
              <span className="text-red-700">Zero Noise Floor (Pure Digital)</span>
            ) : (
              <span className="text-green-700">Natural Microphone Ambience</span>
            )}
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            {waveform.noise_floor_db && waveform.noise_floor_db < -65
              ? 'Artificial silence lacking physical microphone room air characteristics.'
              : 'Consistent ambient microphone noise and breath acoustics detected.'}
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Speech Coherence</div>
          <div className="text-sm font-bold text-slate-900">
            {consistency.splicing_detected ? (
              <span className="text-red-700">Audio Splice Detected</span>
            ) : (
              <span className="text-green-700">Smooth Continuous Speech</span>
            )}
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            {consistency.splicing_detected
              ? 'Incoherent phase boundary detected indicating spliced sound bites.'
              : 'Unbroken single voice recording from start to finish.'}
          </p>
        </div>
      </div>
    </div>
  );
};
