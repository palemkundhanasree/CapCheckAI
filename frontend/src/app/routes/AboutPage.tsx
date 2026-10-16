import React from 'react';
import { Shield, Cpu, BookOpen, AlertTriangle, Layers, Sparkles, CheckCircle } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      {/* Title */}
      <div className="space-y-2 text-center sm:text-left">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Platform Architecture & Methodology</span>
        </div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
          How CapCheck AI Verifies the Truth
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed max-w-2xl">
          An objective, multi-stage verification framework cross-referencing claims against independent factual databases, digital forensic indicators, and source consensus.
        </p>
      </div>

      {/* The 3 Pillars */}
      <div className="p-6 sm:p-8 rounded-xl bg-white border border-slate-200 shadow-sm space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <span>The 3 Pillars of Every Verification</span>
          </h2>
          <p className="text-xs text-slate-600 mt-1">
            Rather than relying on opaque singular labels, CapCheck AI breaks down verification into three verifiable pillars:
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">1. Factual Truth</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Cross-checked against verified encyclopedias, international fact-checking repositories, and peer-reviewed historical records.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">2. Media Authenticity</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Examines camera hardware provenance (EXIF, C2PA), sensor noise patterns, frequency spectra, and generative AI synthesis artifacts.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">3. Contextual Integrity</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Detects recycled authentic media paired with misleading or fabricated breaking-news captions.
            </p>
          </div>
        </div>
      </div>

      {/* Detection Technology */}
      <div className="p-6 sm:p-8 rounded-xl bg-white border border-slate-200 shadow-sm space-y-5">
        <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
          <Cpu className="w-5 h-5 text-blue-600" />
          <span>Forensic Inspection Techniques</span>
        </h2>

        <div className="space-y-3.5 text-xs">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <h4 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-blue-600" />
              <span>AI Image Synthesis & Fourier Spectrum Analysis</span>
            </h4>
            <p className="text-slate-600 leading-relaxed">
              Generative diffusion models leave characteristic periodic frequency fingerprints. We detect mathematical grid anomalies while recognizing authentic camera hardware signatures.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <h4 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-blue-600" />
              <span>Error Level Analysis (ELA) for Splicing</span>
            </h4>
            <p className="text-slate-600 leading-relaxed">
              When an element is digitally composited into a photo, compression degradation rates at boundary edges differ from the background canvas.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <h4 className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-blue-600" />
              <span>Synthetic Voice Clones & Acoustic Coherence</span>
            </h4>
            <p className="text-slate-600 leading-relaxed">
              Natural human speech features micro-tremors, breathing cadence, and ambient room reverberation, whereas neural voice clones often lack physical acoustic room dynamics.
            </p>
          </div>
        </div>
      </div>

      {/* Transparent Methodology */}
      <div className="p-5 rounded-lg bg-amber-50 border border-amber-200 space-y-2">
        <div className="flex items-center space-x-2 text-amber-900 font-semibold text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-700 flex-shrink-0" />
          <span>Transparent Verification Standards</span>
        </div>
        <p className="text-xs text-amber-800 leading-relaxed">
          CapCheck AI never invents evidence or pretends that an unverified claim has been checked. When evidence is scarce or media is heavily recompressed by social messaging apps, we transparently report the uncertainty with an honest confidence score.
        </p>
      </div>
    </div>
  );
};
