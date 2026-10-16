import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, HelpCircle, AlertCircle } from 'lucide-react';

export type CanonicalVerdict =
  | 'SUPPORTED'
  | 'FALSE'
  | 'MISLEADING'
  | 'MIXED'
  | 'UNVERIFIED'
  | 'ERROR';

/**
 * Normalizes any backend, legacy, or formatted verdict into the single canonical enum.
 * Never defaults unknown or missing values to SUPPORTED / Green.
 */
export function normalizeVerdict(
  rawVerdict?: string | null,
  rawLabel?: string | null,
  score?: number | null
): CanonicalVerdict {
  const v = (rawVerdict || '').trim().toUpperCase();
  const l = (rawLabel || '').trim().toLowerCase();

  // 1. Direct canonical / exact matches on rawVerdict
  if (v === 'SUPPORTED' || v === 'AUTHENTIC' || v === 'REAL' || v === 'VERIFIED') {
    return 'SUPPORTED';
  }
  if (v === 'FALSE' || v === 'FAKE' || v === 'CONTRADICTED' || v === 'AI_GENERATED' || v === 'MANIPULATED') {
    return 'FALSE';
  }
  if (v === 'MISLEADING' || v === 'MISLEADING_CONTEXT' || v === 'OUT_OF_CONTEXT') {
    return 'MISLEADING';
  }
  if (v === 'MIXED' || v === 'PARTIALLY_SUPPORTED') {
    return 'MIXED';
  }
  if (v === 'ERROR' || v === 'FAILED') {
    return 'ERROR';
  }
  if (v === 'UNVERIFIED' || v === 'INCONCLUSIVE' || v === 'OPINION') {
    return 'UNVERIFIED';
  }

  // 2. Evaluated fallback on rawLabel
  if (l.includes('false') || l.includes('contradicted') || l.includes('fake') || l.includes('ai-generated') || l.includes('0.0%') || l.includes('0%')) {
    return 'FALSE';
  }
  if (l.includes('supported by evidence') || (l.includes('supported') && !l.includes('unsupported'))) {
    return 'SUPPORTED';
  }
  if (l.includes('misleading')) {
    return 'MISLEADING';
  }
  if (l.includes('mixed')) {
    return 'MIXED';
  }
  if (l.includes('unverified') || l.includes('inconclusive') || l.includes('opinion')) {
    return 'UNVERIFIED';
  }
  if (l.includes('failed') || l.includes('error')) {
    return 'ERROR';
  }

  // 3. Fallback based on score (only when verdict string is completely missing)
  if (score !== null && score !== undefined) {
    if (score >= 75) return 'SUPPORTED';
    if (score > 25 && score < 75) return 'MIXED';
    if (score <= 25 && score > 0) return 'FALSE';
  }

  // Safe default: UNVERIFIED (Never defaults to green / SUPPORTED)
  return 'UNVERIFIED';
}

export interface VerdictPresentation {
  canonical: CanonicalVerdict;
  label: string;
  badgeBg: string;
  textColor: string;
  headerBg: string;
  cardBorder: string;
  progressBarColor: string;
  icon: React.ReactNode;
  accessibleStatus: string;
  colorName: 'green' | 'red' | 'orange' | 'grey';
}

/**
 * Shared presentation mapping used consistently across Results Page, History Page, and Dashboard.
 * Guarantees visual and functional consistency:
 * - SUPPORTED: Green ("Supported by evidence")
 * - FALSE: Red ("False")
 * - MISLEADING: Orange ("Misleading")
 * - MIXED: Orange ("Mixed evidence")
 * - UNVERIFIED: Grey ("Unverified")
 * - ERROR: Grey ("Verification failed")
 */
export function getVerdictPresentation(
  rawVerdict?: string | null,
  rawLabel?: string | null,
  score?: number | null
): VerdictPresentation {
  const canonical = normalizeVerdict(rawVerdict, rawLabel, score);

  switch (canonical) {
    case 'SUPPORTED':
      return {
        canonical: 'SUPPORTED',
        label: 'Supported by evidence',
        badgeBg: 'bg-green-100 text-green-800 border-green-300',
        textColor: 'text-green-700',
        headerBg: 'bg-green-50/70',
        cardBorder: 'border-green-300',
        progressBarColor: 'bg-green-500',
        icon: <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />,
        accessibleStatus: 'Verified: Claim or media is supported by credible independent evidence.',
        colorName: 'green'
      };

    case 'FALSE':
      return {
        canonical: 'FALSE',
        label: 'False',
        badgeBg: 'bg-red-100 text-red-800 border-red-300',
        textColor: 'text-red-700',
        headerBg: 'bg-red-50/70',
        cardBorder: 'border-red-300',
        progressBarColor: 'bg-red-500',
        icon: <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />,
        accessibleStatus: 'Refuted: Strong credible evidence contradicts this claim or indicates manipulation.',
        colorName: 'red'
      };

    case 'MISLEADING':
      return {
        canonical: 'MISLEADING',
        label: 'Misleading',
        badgeBg: 'bg-amber-100 text-amber-800 border-amber-300',
        textColor: 'text-amber-700',
        headerBg: 'bg-amber-50/70',
        cardBorder: 'border-amber-300',
        progressBarColor: 'bg-amber-500',
        icon: <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />,
        accessibleStatus: 'Caution: The claim contains significant factual distortion or omitted context.',
        colorName: 'orange'
      };

    case 'MIXED':
      return {
        canonical: 'MIXED',
        label: 'Mixed evidence',
        badgeBg: 'bg-orange-100 text-orange-800 border-orange-300',
        textColor: 'text-orange-700',
        headerBg: 'bg-orange-50/70',
        cardBorder: 'border-orange-300',
        progressBarColor: 'bg-orange-500',
        icon: <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0" />,
        accessibleStatus: 'Mixed: Statement contains both supported assertions and contradicted elements.',
        colorName: 'orange'
      };

    case 'ERROR':
      return {
        canonical: 'ERROR',
        label: 'Verification failed',
        badgeBg: 'bg-slate-100 text-slate-700 border-slate-300',
        textColor: 'text-slate-600',
        headerBg: 'bg-slate-50/70',
        cardBorder: 'border-slate-300',
        progressBarColor: 'bg-slate-400',
        icon: <AlertCircle className="w-5 h-5 text-slate-600 flex-shrink-0" />,
        accessibleStatus: 'Technical Failure: Verification could not be completed.',
        colorName: 'grey'
      };

    case 'UNVERIFIED':
    default:
      return {
        canonical: 'UNVERIFIED',
        label: 'Unverified',
        badgeBg: 'bg-slate-100 text-slate-700 border-slate-300',
        textColor: 'text-slate-700',
        headerBg: 'bg-slate-50/70',
        cardBorder: 'border-slate-300',
        progressBarColor: 'bg-slate-400',
        icon: <HelpCircle className="w-5 h-5 text-slate-500 flex-shrink-0" />,
        accessibleStatus: 'Unverified: Insufficient reliable evidence found to reach a definitive conclusion.',
        colorName: 'grey'
      };
  }
}

interface VerdictBadgeProps {
  verdict?: string | null;
  label?: string | null;
  score?: number | null;
  showIcon?: boolean;
  className?: string;
}

export const VerdictBadge: React.FC<VerdictBadgeProps> = ({
  verdict,
  label,
  score,
  showIcon = true,
  className = ''
}) => {
  const pres = getVerdictPresentation(verdict, label, score);

  return (
    <span
      className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-xs font-semibold border ${pres.badgeBg} ${className}`}
      title={pres.accessibleStatus}
    >
      {showIcon && pres.icon}
      <span>{label || pres.label}</span>
    </span>
  );
};
