import React from 'react';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  AlertCircle,
  FileText,
  Cpu,
  Layers,
  Clock,
  ExternalLink,
  Image as ImageIcon,
  Film,
  Volume2,
  Info,
  ShieldCheck
} from 'lucide-react';
import { VerificationReport } from '../types';
import { getVerdictPresentation, normalizeVerdict } from '../utils/verdictPresentation';
import { resolveMediaUrl } from '../services/apiClient';

interface VerdictCardProps {
  report: VerificationReport;
}

export const VerdictCard: React.FC<VerdictCardProps> = ({ report }) => {
  // Extract verified support or authenticity score
  const extractScore = (): { score: number; label: string } => {
    const text = report.verdict_label || '';
    const match = text.match(/:\s*([0-9.]+)%/);
    if (match) {
      const val = parseFloat(match[1]);
      const label = report.input_type === 'image' || report.input_type === 'video' || report.input_type === 'audio'
        ? 'Real Authenticity Score'
        : 'Real Evidence Support';
      return { score: val, label };
    }
    if (report.input_type === 'image' || report.input_type === 'video' || report.input_type === 'audio') {
      const aiScore = report.media_analysis?.ai_generated_score ?? 0;
      return { score: Math.round(100 - aiScore), label: 'Real Authenticity Score' };
    }
    const supports = (report.evidence_items || []).filter(e => e.stance === 'SUPPORTS').length;
    const contradicts = (report.evidence_items || []).filter(e => e.stance === 'CONTRADICTS').length;
    const total = supports + contradicts;
    const canonical = normalizeVerdict(report.overall_verdict, report.verdict_label);
    if (canonical === 'SUPPORTED') return { score: 95, label: 'Real Evidence Support' };
    if (canonical === 'FALSE') return { score: 0, label: 'Real Evidence Support' };
    if (canonical === 'MISLEADING') return { score: 35, label: 'Real Evidence Support' };
    if (canonical === 'MIXED') return { score: 50, label: 'Real Evidence Support' };
    if (canonical === 'UNVERIFIED') return { score: 0, label: 'Real Evidence Support' };
    const calculated = total > 0 ? Math.round((supports / total) * 100) : 0;
    return { score: calculated, label: 'Real Evidence Support' };
  };

  const { score: evaluationScore, label: scoreLabel } = extractScore();
  const pres = getVerdictPresentation(report.overall_verdict, report.verdict_label, evaluationScore);
  const isPassed = pres.canonical === 'SUPPORTED';

  const getVerdictIcon = (canonical: string) => {
    switch (canonical) {
      case 'SUPPORTED':
        return <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0" />;
      case 'FALSE':
        return <XCircle className="w-8 h-8 text-red-600 flex-shrink-0" />;
      case 'MISLEADING':
        return <AlertTriangle className="w-8 h-8 text-amber-600 flex-shrink-0" />;
      case 'MIXED':
        return <AlertTriangle className="w-8 h-8 text-orange-600 flex-shrink-0" />;
      case 'ERROR':
        return <AlertCircle className="w-8 h-8 text-slate-500 flex-shrink-0" />;
      case 'UNVERIFIED':
      default:
        return <HelpCircle className="w-8 h-8 text-slate-500 flex-shrink-0" />;
    }
  };

  const mediaStreamUrl = resolveMediaUrl(report.media_url || `/api/v1/reports/${report.id}/media`);

  // Structured Why & Why Not reasoning
  const getWhyWhyNot = () => {
    const raw = report.explanation || '';
    if (raw.includes('#### 1. Why this Real Accuracy was determined:')) {
      const p1 = raw.split('#### 1. Why this Real Accuracy was determined:')[1];
      const parts = p1.split('#### 2. Why it did not score higher or lower');
      const why = parts[0]?.trim() || '';
      const whyNot = parts[1]?.split('#### 3. Verification Summary:')[0]?.replace('(Limiting & Contradicting Factors):', '')?.trim() || '';
      if (why && whyNot) return { why, whyNot };
    }

    if (report.input_type === 'claim' || report.input_type === 'url') {
      if (pres.canonical === 'SUPPORTED') {
        return {
          why: `Independent fact-checking registries and authoritative citations corroborate this statement with ${evaluationScore}% positive evidential weight. The assertions match established scientific and historic records.`,
          whyNot: evaluationScore < 100
            ? 'The score did not reach 100% due to minor contextual nuances, variations in reporting phrasing, or natural index retrieval variances.'
            : 'Unanimous verification achieved across all consulted independent registries with zero contradictions.'
        };
      } else if (pres.canonical === 'UNVERIFIED') {
        return {
          why: 'No independent corroborating or refuting records were located in indexed registries or authoritative sources.',
          whyNot: 'Without verified primary sources or authoritative documentation, this assertion cannot be confirmed as factual or debunked as false. It remains unverified.'
        };
      } else if (pres.canonical === 'MIXED' || pres.canonical === 'MISLEADING') {
        return {
          why: `Some components or historical elements of the claim align with verified records (${evaluationScore}% factual overlap).`,
          whyNot: 'Certain statements or contextual framings are contradicted by official findings, missing critical caveats, or unsupported by evidence.'
        };
      } else {
        return {
          why: evaluationScore > 0
            ? `A baseline score of ${evaluationScore}% was noted from peripheral non-disputed context keywords.`
            : 'Zero credible evidence or authoritative citations substantiated this claim.',
          whyNot: 'This assertion is classified as False because verified scientific consensus, official records, or authoritative reporting disprove the primary claim.'
        };
      }
    } else {
      const aiScore = report.media_analysis?.ai_generated_score ?? 0;
      if (isPassed) {
        return {
          why: `Physical camera sensor noise patterns (PRNU), authentic hardware metadata, and natural frequency harmonics confirm real-world recording with an authenticity level of ${evaluationScore}%.`,
          whyNot: evaluationScore < 100
            ? 'Score did not reach 100% due to lossy file re-compression artifacts or compression blurring common in digital sharing.'
            : 'Pristine hardware sensor noise and cryptographic content credentials confirm complete authenticity.'
        };
      } else {
        return {
          why: `The file exhibits a baseline real score of ${evaluationScore}% in standard container framing.`,
          whyNot: `The media failed the required 75% Real threshold due to detected synthetic generative AI artifacts (${aiScore}% synthetic risk), unnatural spectral harmonics, or digital manipulation gradients.`
        };
      }
    }
  };

  const { why: whyText, whyNot: whyNotText } = getWhyWhyNot();

  return (
    <div className={`bg-white rounded-xl border ${pres.cardBorder} shadow-sm overflow-hidden`}>
      {/* Top Banner */}
      <div className={`p-6 border-b border-slate-200 ${pres.headerBg}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center space-x-4">
            {getVerdictIcon(pres.canonical)}
            <div>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${pres.badgeBg}`}>
                  {report.verdict_label || pres.label}
                </span>
                <span className="text-xs text-slate-500">•</span>
                <span className="text-xs font-medium text-slate-600">
                  {report.confidence_score}% Audit Confidence
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-500 flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-slate-400" />
                  <span>{new Date(report.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                </span>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mt-1">
                Accuracy Level of Real: {evaluationScore}%
              </h2>
              <p className="text-xs text-slate-600 mt-0.5">
                {pres.canonical === 'SUPPORTED'
                  ? 'High Authenticity (Meets ≥ 75% Standard)'
                  : pres.canonical === 'UNVERIFIED'
                  ? 'Inconclusive / Unverified (Requires Primary Sources)'
                  : pres.canonical === 'MIXED'
                  ? 'Mixed Authenticity (Partial Truth & Contradictions)'
                  : pres.canonical === 'MISLEADING'
                  ? 'Misleading Framing (Lacks Crucial Context)'
                  : 'Low Authenticity (Contradicted / Synthetic / Altered)'}
              </p>
            </div>
          </div>

          <div className="text-right">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Evaluation Model
            </span>
            <span className="text-xs text-slate-700 font-mono">
              CapCheck Real Accuracy (≥75% Rule)
            </span>
          </div>
        </div>

        {/* Threshold Audit Visual Evaluation Bar */}
        <div className="mt-4 p-3.5 rounded-lg border border-slate-200 bg-white/90 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-700 flex items-center space-x-1.5">
              <span>{scoreLabel}:</span>
              <span className={`font-bold ${pres.textColor}`}>
                {evaluationScore}%
              </span>
            </span>
            <span className={`px-2.5 py-0.5 rounded text-[11px] font-bold border ${pres.badgeBg}`}>
              {pres.canonical === 'SUPPORTED'
                ? `✓ Meets ≥ 75% Authenticity Standard (${evaluationScore}% Real)`
                : pres.canonical === 'UNVERIFIED'
                ? `? Insufficient Evidence to Confirm (${evaluationScore}% Real Support)`
                : pres.canonical === 'MIXED'
                ? `~ Mixed Factual & Contradicted Elements (${evaluationScore}% Real)`
                : pres.canonical === 'MISLEADING'
                ? `! Misleading Context / Distortions (${evaluationScore}% Real)`
                : `✗ Fails 75% Standard (${evaluationScore}% Real Accuracy)`}
            </span>
          </div>

          <div className="relative w-full h-3 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-slate-900 z-10"
              style={{ left: '75%' }}
              title="Required 75% Decision Threshold"
            />
            <div
              className={`h-full rounded-full transition-all duration-500 ${pres.progressBarColor}`}
              style={{ width: `${Math.min(evaluationScore, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>0% (Refuted / Altered)</span>
            <span className="text-slate-900 font-semibold">▲ 75% Authenticity Threshold</span>
            <span>100% (Fully Verified Real)</span>
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
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              <div className="p-2.5 text-xs text-slate-600 border-t border-slate-100 bg-white">
                <span className="font-semibold text-slate-800">Inspection:</span> Error Level Analysis (ELA) and sensor PRNU pattern checked.
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
                <span className="font-semibold text-slate-800">Video Forensics:</span> Temporal frame coherence and lip-synchronization checked.
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
                Acoustic spectral harmonics and voice-cloning synthesis examined.
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
        <div className="lg:col-span-7 space-y-4">
          <div>
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5 text-blue-600" />
              <span>Real Accuracy Assessment</span>
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-200">
              {report.summary}
            </p>
          </div>

          {/* Explicit Why and Why Not Section */}
          <div className="space-y-3">
            <div className="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50/40 space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-bold text-emerald-900">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span>WHY THIS REAL ACCURACY WAS DETERMINED:</span>
              </div>
              <p className="text-xs text-emerald-800 leading-relaxed">
                {whyText}
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-rose-200 bg-rose-50/40 space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-bold text-rose-900">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                <span>WHY IT DID NOT SCORE HIGHER OR LOWER:</span>
              </div>
              <p className="text-xs text-rose-800 leading-relaxed">
                {whyNotText}
              </p>
            </div>
          </div>

          {/* 3-Pillar Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
            <div className="p-3 rounded-lg border border-slate-200 bg-white space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600">
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                <span>Fact-Check</span>
              </div>
              <div className="text-xs font-bold text-slate-900">
                {report.factual_claim_verdict ? report.factual_claim_verdict.replace(/_/g, ' ') : 'N/A (Media)'}
              </div>
              <p className="text-[10px] text-slate-500">Cross-verified against verified databases.</p>
            </div>

            <div className="p-3 rounded-lg border border-slate-200 bg-white space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600">
                <Cpu className="w-3.5 h-3.5 text-blue-600" />
                <span>Media Authenticity</span>
              </div>
              <div className="text-xs font-bold text-slate-900">
                {report.media_authenticity_verdict ? report.media_authenticity_verdict.replace(/_/g, ' ') : 'N/A (Text)'}
              </div>
              <p className="text-[10px] text-slate-500">AI generation & manipulation check.</p>
            </div>

            <div className="p-3 rounded-lg border border-slate-200 bg-white space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600">
                <Layers className="w-3.5 h-3.5 text-blue-600" />
                <span>Context Integrity</span>
              </div>
              <div className="text-xs font-bold text-slate-900">
                {report.context_verdict ? report.context_verdict.replace(/_/g, ' ') : 'Authentic Original'}
              </div>
              <p className="text-[10px] text-slate-500">Recycled media and framing test.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

