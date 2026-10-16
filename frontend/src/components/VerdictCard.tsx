import React, { useEffect, useState } from 'react';
import {
  CheckCircle, XCircle, AlertTriangle, FileText, Clock, ExternalLink,
  Image as ImageIcon, Film, Volume2, Info, Loader2,
} from 'lucide-react';
import { VerificationReport } from '../types';
import { reportApi } from '../services/reportApi';

interface VerdictCardProps {
  report: VerificationReport;
}

type Tone = 'green' | 'red' | 'orange';

const TONES: Record<Tone, { border: string; header: string; badge: string; icon: JSX.Element; label: string }> = {
  green: {
    border: 'border-green-200', header: 'bg-green-50', badge: 'bg-green-100 text-green-800 border-green-300',
    icon: <CheckCircle className="w-7 h-7 text-green-600 flex-shrink-0" />, label: 'Real / Verified',
  },
  red: {
    border: 'border-red-200', header: 'bg-red-50', badge: 'bg-red-100 text-red-800 border-red-300',
    icon: <XCircle className="w-7 h-7 text-red-600 flex-shrink-0" />, label: 'Fake / False',
  },
  orange: {
    border: 'border-orange-200', header: 'bg-orange-50', badge: 'bg-orange-100 text-orange-800 border-orange-300',
    icon: <AlertTriangle className="w-7 h-7 text-orange-600 flex-shrink-0" />, label: 'Misleading / Uncertain',
  },
};

export function verdictTone(verdict: string): Tone {
  const v = (verdict || '').toUpperCase();
  if (v.includes('CONTRADICT') || v.includes('AI_GENERATED') || v.includes('MANIPULATED') || v.includes('FALSE') || v.includes('FAKE')) return 'red';
  if (v === 'SUPPORTED' || v === 'MOSTLY_SUPPORTED' || v.includes('AUTHENTIC') || v.includes('VERIFIED')) return 'green';
  return 'orange';
}

/** Renders the **bold** markers and "- " bullets produced by the verdict engine as plain, safe HTML. */
const Explanation: React.FC<{ text: string }> = ({ text }) => {
  const blocks = text.split(/\n\n+/).filter(Boolean);
  const bold = (line: string) =>
    line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith('**') ? <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong> : <span key={i}>{part}</span>
    );
  return (
    <div className="space-y-3 text-sm text-slate-700 leading-relaxed">
      {blocks.map((block, i) => {
        const lines = block.split('\n').filter(Boolean);
        return (
          <div key={i} className="space-y-1">
            {lines.map((line, j) =>
              line.startsWith('- ') ? (
                <div key={j} className="flex gap-2"><span className="text-slate-400">•</span><span>{bold(line.slice(2))}</span></div>
              ) : (
                <p key={j}>{bold(line)}</p>
              )
            )}
          </div>
        );
      })}
    </div>
  );
};

/** Loads the uploaded file through the authenticated API (an <img src> cannot send the sign-in token). */
function useMediaUrl(reportId: string, enabled: boolean) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!enabled) return;
    let objectUrl: string | null = null;
    let cancelled = false;
    reportApi.getMediaBlob(reportId)
      .then((blob) => { if (!cancelled) { objectUrl = URL.createObjectURL(blob); setUrl(objectUrl); } })
      .catch(() => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [reportId, enabled]);
  return { url, failed };
}

export const VerdictCard: React.FC<VerdictCardProps> = ({ report }) => {
  const tone = TONES[verdictTone(report.overall_verdict)];
  const isMedia = ['image', 'video', 'audio'].includes(report.input_type);
  const score = report.correctness_score ?? 0;
  const pctColor = score >= 70
    ? { text: 'text-green-700', bar: 'bg-green-600' }
    : score <= 30
      ? { text: 'text-red-700', bar: 'bg-red-600' }
      : { text: 'text-orange-700', bar: 'bg-orange-500' };
  const { url: mediaUrl, failed: mediaFailed } = useMediaUrl(report.id, isMedia);

  // Image/audio/video reports may carry the user's caption after a newline
  const [firstLine, ...rest] = (report.input_preview || report.title).split('\n');
  const caption = rest.join('\n').replace(/^Caption:\s*/, '');
  const urlMatch = report.input_type === 'url' ? (report.input_preview || '').match(/https?:\/\/\S+/) : null;

  const TypeIcon = report.input_type === 'image' ? ImageIcon : report.input_type === 'video' ? Film : report.input_type === 'audio' ? Volume2 : FileText;

  const MediaPlaceholder = (
    <div className="h-40 flex items-center justify-center text-xs text-slate-500 bg-slate-100 rounded">
      {mediaFailed ? 'The uploaded file is no longer stored (files are deleted after a short retention period).' : <Loader2 className="w-5 h-5 animate-spin" />}
    </div>
  );

  return (
    <div className={`bg-white rounded-lg border ${tone.border} shadow-sm overflow-hidden`}>
      <div className={`px-6 py-5 border-b border-slate-200 ${tone.header}`}>
        <div className="flex items-start gap-3">
          {tone.icon}
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold border ${tone.badge}`}>{tone.label}</span>
              <span className="text-xs font-medium text-slate-700">{report.confidence_score}% confidence ({report.confidence_level.toLowerCase()})</span>
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(report.created_at + 'Z').toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
              </span>
            </div>
            <h2 className="text-xl font-semibold text-slate-900 mt-1">{report.verdict_label || tone.label}</h2>
          </div>
        </div>
      </div>

      {/* Overall percentage correct */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white">
        {report.correctness_score != null ? (
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="sm:w-56 flex-shrink-0">
              <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
                {isMedia ? 'Likely genuine / correct' : 'Likely correct'}
              </div>
              <div className="flex items-baseline gap-1">
                <span className={`text-3xl font-bold ${pctColor.text}`}>{Math.round(report.correctness_score)}%</span>
              </div>
              <div className="mt-1.5 h-2 rounded-full bg-slate-200 overflow-hidden" role="img"
                aria-label={`${Math.round(report.correctness_score)} percent likely correct`}>
                <div className={`h-full ${pctColor.bar}`} style={{ width: `${Math.round(report.correctness_score)}%` }} />
              </div>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">{report.correctness_explanation}</p>
          </div>
        ) : (
          <div className="text-sm text-slate-700">
            <span className="font-semibold text-orange-700">No percentage given. </span>
            {report.correctness_explanation || 'There was not enough reliable evidence to estimate how likely this is to be correct.'}
          </div>
        )}
      </div>

      <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* What was checked */}
        <div className="lg:col-span-5 bg-paper rounded-md border border-slate-200 p-4 space-y-3">
          <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide flex items-center gap-1.5">
            <TypeIcon className="w-3.5 h-3.5" />
            <span>What you submitted</span>
          </div>

          {report.input_type === 'image' && (
            <div className="rounded border border-slate-200 bg-white overflow-hidden">
              {mediaUrl ? <img src={mediaUrl} alt="Submitted image" className="w-full max-h-72 object-contain bg-slate-100" /> : MediaPlaceholder}
              <p className="p-2 text-xs text-slate-500 border-t border-slate-100 break-all">{firstLine}</p>
            </div>
          )}
          {report.input_type === 'video' && (
            <div className="rounded border border-slate-200 bg-white overflow-hidden">
              {mediaUrl ? <video src={mediaUrl} controls className="w-full max-h-72 bg-black" /> : MediaPlaceholder}
              <p className="p-2 text-xs text-slate-500 border-t border-slate-100 break-all">{firstLine}</p>
            </div>
          )}
          {report.input_type === 'audio' && (
            <div className="rounded border border-slate-200 bg-white p-3 space-y-2">
              {mediaUrl ? <audio src={mediaUrl} controls className="w-full" /> : MediaPlaceholder}
              <p className="text-xs text-slate-500 break-all">{firstLine}</p>
            </div>
          )}
          {isMedia && caption && (
            <div className="rounded border border-slate-200 bg-white p-3">
              <p className="text-xs font-semibold text-slate-500 mb-1">Caption / claim that came with it</p>
              <p className="text-sm text-slate-800">“{caption}”</p>
            </div>
          )}

          {(report.input_type === 'claim' || report.input_type === 'url') && (
            <div className="rounded border border-slate-200 bg-white p-3 space-y-2">
              <p className="text-xs font-semibold text-slate-500">{report.input_type === 'claim' ? 'Claim' : 'Article'}</p>
              <blockquote className="text-sm font-medium text-slate-800 border-l-2 border-slate-300 pl-3 leading-relaxed break-words">
                {report.input_type === 'url' ? (report.input_preview || '').replace(/\s*—?\s*https?:\/\/\S+/, '') || report.title : report.input_preview || report.title}
              </blockquote>
              {urlMatch && (
                <a href={urlMatch[0]} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline break-all">
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />{urlMatch[0]}
                </a>
              )}
            </div>
          )}
        </div>

        {/* Why this verdict */}
        <div className="lg:col-span-7 space-y-4">
          <div>
            <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5" /><span>Why this verdict and score</span>
            </h3>
            <div className="bg-white p-4 rounded-md border border-slate-200">
              <Explanation text={report.explanation || report.summary} />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {[
              ['Fact check', report.factual_claim_verdict],
              ['Media authenticity', report.media_authenticity_verdict],
              ['Context', report.context_verdict],
            ].map(([label, value]) => (
              <div key={label as string} className="p-3 rounded-md border border-slate-200 bg-white">
                <div className="text-slate-500">{label}</div>
                <div className="font-semibold text-slate-900 mt-0.5">{value ? (value as string).replace(/_/g, ' ').toLowerCase() : 'not applicable'}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
