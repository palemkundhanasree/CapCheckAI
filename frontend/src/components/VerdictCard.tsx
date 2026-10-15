import React from 'react';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  FileText,
  Cpu,
  Layers,
  Clock,
  ExternalLink,
  Image as ImageIcon,
  Film,
  Volume2,
  Info
} from 'lucide-react';
import { VerificationReport } from '../types';

interface VerdictCardProps {
  report: VerificationReport;
}

export const VerdictCard: React.FC<VerdictCardProps> = ({ report }) => {
  const getVerdictStyle = (verdict: string) => {
    const v = (verdict || '').toUpperCase();
    if (v.includes('SUPPORTED') || v.includes('AUTHENTIC') || v.includes('TRUE') || v.includes('VERIFIED')) {
      return {
        cardBorder: 'border-green-200',
        badgeBg: 'bg-green-100 text-green-800 border-green-300',
        headerBg: 'bg-green-50/60',
        textColor: 'text-green-700',
        icon: <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0" />,
        label: 'Real / Verified'
      };
    }
    if (v.includes('CONTRADICTED') || v.includes('AI_GENERATED') || v.includes('MANIPULATED') || v.includes('FALSE') || v.includes('FAKE')) {
      return {
        cardBorder: 'border-red-200',
        badgeBg: 'bg-red-100 text-red-800 border-red-300',
        headerBg: 'bg-red-50/60',
        textColor: 'text-red-700',
        icon: <XCircle className="w-8 h-8 text-red-600 flex-shrink-0" />,
        label: 'Fake / False'
      };
    }
    if (v.includes('CONTEXT') || v.includes('SUSPICIOUS') || v.includes('MISLEADING') || v.includes('UNCERTAIN')) {
      return {
        cardBorder: 'border-orange-200',
        badgeBg: 'bg-orange-100 text-orange-800 border-orange-300',
        headerBg: 'bg-orange-50/60',
        textColor: 'text-orange-700',
        icon: <AlertTriangle className="w-8 h-8 text-orange-600 flex-shrink-0" />,
        label: 'Misleading / Uncertain'
      };
    }
    return {
      cardBorder: 'border-slate-200',
      badgeBg: 'bg-slate-100 text-slate-800 border-slate-300',
      headerBg: 'bg-slate-50',
      textColor: 'text-slate-700',
      icon: <HelpCircle className="w-8 h-8 text-slate-500 flex-shrink-0" />,
      label: 'Inconclusive / Needs Context'
    };
  };

  const style = getVerdictStyle(report.overall_verdict);
  const mediaStreamUrl = report.media_url || `/api/v1/reports/${report.id}/media`;

  return (
    <div className={`bg-white rounded-xl border ${style.cardBorder} shadow-sm overflow-hidden`}>
      {/* Top Banner */}
      <div className={`p-6 border-b border-slate-200 ${style.headerBg}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center space-x-4">
            {style.icon}
            <div>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style.badgeBg}`}>
                  {style.label}
                </span>
                <span className="text-xs text-slate-500">•</span>
                <span className="text-xs font-medium text-slate-600">
                  {report.confidence_score}% Confidence
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-500 flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-slate-400" />
                  <span>{new Date(report.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                </span>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mt-1">
                {report.verdict_label || style.label}
              </h2>
            </div>
          </div>

          <div className="text-right">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Evaluation Model
            </span>
            <span className="text-xs text-slate-700 font-mono">
              TruthLens Forensics v1.0
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Area: Side-by-side Input Media Preview + Verdict Explanation */}
      <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Input Media Preview (Image / Video / Audio / News) */}
        <div className="lg:col-span-5 bg-slate-50 rounded-lg border border-slate-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
              {report.input_type === 'image' && <ImageIcon className="w-3.5 h-3.5 text-slate-600" />}
              {report.input_type === 'video' && <Film className="w-3.5 h-3.5 text-slate-600" />}
              {report.input_type === 'audio' && <Volume2 className="w-3.5 h-3.5 text-slate-600" />}
              {report.input_type === 'claim' && <FileText className="w-3.5 h-3.5 text-slate-600" />}
              {report.input_type === 'url' && <FileText className="w-3.5 h-3.5 text-slate-600" />}
              <span>Submitted {report.input_type.toUpperCase()} Input</span>
            </span>
            <span className="text-[11px] text-slate-500 font-mono">Verified Artifact</span>
          </div>

          {/* Image Display */}
          {report.input_type === 'image' && (
            <div className="rounded-lg overflow-hidden border border-slate-200 bg-white">
              <img
                src={mediaStreamUrl}
                alt="Analyzed media input"
                className="w-full h-auto max-h-64 object-contain mx-auto bg-slate-100"
                onError={(e) => {
                  // Fallback placeholder if image stream is offline
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              <div className="p-2.5 text-xs text-slate-600 border-t border-slate-100 bg-white">
                <span className="font-semibold text-slate-800">Inspection:</span> Error Level Analysis (ELA) and frequency spectrum checked.
              </div>
            </div>
          )}

          {/* Video Display */}
          {report.input_type === 'video' && (
            <div className="rounded-lg overflow-hidden border border-slate-200 bg-black">
              <video
                src={mediaStreamUrl}
                controls
                className="w-full max-h-64 object-contain mx-auto"
              />
              <div className="p-2.5 text-xs text-slate-600 border-t border-slate-100 bg-white">
                <span className="font-semibold text-slate-800">Video Forensics:</span> Temporal coherence and lip-synchronization analyzed.
              </div>
            </div>
          )}

          {/* Audio Display */}
          {report.input_type === 'audio' && (
            <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-3">
              <div className="flex items-center space-x-2 text-slate-700 text-xs font-medium">
                <Volume2 className="w-4 h-4 text-blue-600" />
                <span>Audio Recording Playback</span>
              </div>
              <audio src={mediaStreamUrl} controls className="w-full" />
              <p className="text-xs text-slate-500">
                Acoustic spectral artifacts and voice-cloning synthesis examined.
              </p>
            </div>
          )}

          {/* Text Claim or URL Input Display */}
          {(report.input_type === 'claim' || report.input_type === 'url') && (
            <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2">
              <p className="text-xs font-semibold text-slate-500 uppercase">Original Text / Statement:</p>
              <blockquote className="text-sm font-medium text-slate-800 italic border-l-2 border-blue-500 pl-3 leading-relaxed">
                "{report.input_preview || report.title}"
              </blockquote>
              {report.input_type === 'url' && (
                <div className="pt-2 text-xs text-slate-500 flex items-center space-x-1">
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                  <span className="truncate">Source URL: {report.input_preview}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Reasoning & Why the Score Was Given */}
        <div className="lg:col-span-7 space-y-5">
          <div>
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5 text-blue-600" />
              <span>Explanation & Evidence Rationale</span>
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-200">
              {report.summary}
            </p>
          </div>

          {/* 3-Pillar Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600">
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                <span>Fact-Check</span>
              </div>
              <div className="text-xs font-bold text-slate-900">
                {report.factual_claim_verdict ? report.factual_claim_verdict.replace(/_/g, ' ') : 'N/A (Media)'}
              </div>
              <p className="text-[11px] text-slate-500">Cross-verified against verified fact check databases.</p>
            </div>

            <div className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600">
                <Cpu className="w-3.5 h-3.5 text-blue-600" />
                <span>Media Authenticity</span>
              </div>
              <div className="text-xs font-bold text-slate-900">
                {report.media_authenticity_verdict ? report.media_authenticity_verdict.replace(/_/g, ' ') : 'N/A (Text)'}
              </div>
              <p className="text-[11px] text-slate-500">AI generation & pixel manipulation inspection.</p>
            </div>

            <div className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600">
                <Layers className="w-3.5 h-3.5 text-blue-600" />
                <span>Context Integrity</span>
              </div>
              <div className="text-xs font-bold text-slate-900">
                {report.context_verdict ? report.context_verdict.replace(/_/g, ' ') : 'Authentic Original'}
              </div>
              <p className="text-[11px] text-slate-500">Recycled media and misleading framing test.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
