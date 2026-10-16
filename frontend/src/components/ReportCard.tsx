import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, HelpCircle, ClipboardCheck } from 'lucide-react';
import { CardStatus, VerificationReport } from '../types';

interface ReportCardProps {
  report: VerificationReport;
}

const STATUS_STYLE: Record<CardStatus, { text: string; bar: string; chip: string; label: string; icon: JSX.Element }> = {
  good: {
    text: 'text-green-700', bar: 'bg-green-600', chip: 'bg-green-50 text-green-800 border-green-200', label: 'Looks fine',
    icon: <CheckCircle className="w-4 h-4 text-green-600" />,
  },
  warn: {
    text: 'text-orange-700', bar: 'bg-orange-500', chip: 'bg-orange-50 text-orange-800 border-orange-200', label: 'Uncertain',
    icon: <AlertTriangle className="w-4 h-4 text-orange-600" />,
  },
  bad: {
    text: 'text-red-700', bar: 'bg-red-600', chip: 'bg-red-50 text-red-800 border-red-200', label: 'Warning signs',
    icon: <XCircle className="w-4 h-4 text-red-600" />,
  },
  unknown: {
    text: 'text-slate-600', bar: 'bg-slate-300', chip: 'bg-slate-50 text-slate-700 border-slate-200', label: 'No result',
    icon: <HelpCircle className="w-4 h-4 text-slate-500" />,
  },
};

const GRADE_COLOR: Record<string, string> = {
  A: 'bg-green-600', B: 'bg-green-500', C: 'bg-orange-500', D: 'bg-orange-600', F: 'bg-red-600', '?': 'bg-slate-400',
};

/** Fallback for reports saved before report cards existed: build a minimal card from the old fields. */
function fallbackCard(report: VerificationReport) {
  const pct = report.correctness_score ?? null;
  const grade = pct == null ? '?' : pct >= 85 ? 'A' : pct >= 70 ? 'B' : pct >= 55 ? 'C' : pct >= 40 ? 'D' : 'F';
  return {
    overall_percent: pct,
    grade,
    grade_label: pct == null ? 'Not enough reliable evidence to give a percentage' : 'Estimated from the stored result',
    confidence_score: report.confidence_score,
    confidence_level: report.confidence_level,
    sections: [],
    how_calculated: '',
    explanation: report.correctness_explanation || '',
    caveats: ['This report was saved before per-test breakdowns were available. Run the check again to see them.'],
  };
}

export const ReportCard: React.FC<ReportCardProps> = ({ report }) => {
  const card = report.report_card || fallbackCard(report);
  const pct = card.overall_percent;
  const overallStatus: CardStatus = pct == null ? 'unknown' : pct >= 70 ? 'good' : pct >= 40 ? 'warn' : 'bad';
  const style = STATUS_STYLE[overallStatus];

  return (
    <section className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden" aria-label="Report card">
      <div className="px-6 py-4 border-b border-slate-200 bg-paper flex items-center gap-2">
        <ClipboardCheck className="w-4 h-4 text-slate-600" />
        <h3 className="text-sm font-semibold text-slate-900">Report card</h3>
      </div>

      <div className="p-6 space-y-6">
        {/* Overall grade + percentage */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <div
            className={`w-20 h-20 rounded-xl flex items-center justify-center text-white text-4xl font-bold flex-shrink-0 ${GRADE_COLOR[card.grade] || 'bg-slate-400'}`}
            aria-label={`Grade ${card.grade}`}
          >
            {card.grade}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2 flex-wrap">
              <span className={`text-4xl font-bold ${style.text}`}>{pct == null ? '—' : `${Math.round(pct)}%`}</span>
              <span className="text-sm font-medium text-slate-700">{card.grade_label}</span>
            </div>
            {pct != null && (
              <div className="mt-2 h-2.5 rounded-full bg-slate-200 overflow-hidden" role="img"
                aria-label={`${Math.round(pct)} percent likely correct`}>
                <div className={`h-full ${style.bar}`} style={{ width: `${Math.round(pct)}%` }} />
              </div>
            )}
            <p className="mt-2 text-xs text-slate-500">
              How sure the system is about this result: <span className="font-semibold text-slate-700">
                {Math.round(card.confidence_score)}% ({card.confidence_level.toLowerCase()} confidence)</span>
            </p>
          </div>
        </div>

        {/* Per-test breakdown */}
        {card.sections.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-3">What each check found</h4>
            <ul className="space-y-3">
              {card.sections.map((sec) => {
                const st = STATUS_STYLE[sec.status] || STATUS_STYLE.unknown;
                return (
                  <li key={sec.key} className="rounded-md border border-slate-200 p-3">
                    <div className="flex items-center justify-between gap-3 flex-wrap">
                      <div className="flex items-center gap-2 min-w-0">
                        {st.icon}
                        <span className="text-sm font-medium text-slate-900">{sec.title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[11px] px-2 py-0.5 rounded-full border ${st.chip}`}>{st.label}</span>
                        <span className={`text-sm font-bold tabular-nums w-12 text-right ${st.text}`}>
                          {sec.percent == null ? 'n/a' : `${Math.round(sec.percent)}%`}
                        </span>
                      </div>
                    </div>
                    {sec.percent != null && (
                      <div className="mt-2 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div className={`h-full ${st.bar}`} style={{ width: `${Math.round(sec.percent)}%` }} />
                      </div>
                    )}
                    {sec.detail && <p className="mt-2 text-xs text-slate-600 leading-relaxed">{sec.detail}</p>}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {/* Explanation of the number */}
        <div className="rounded-md bg-slate-50 border border-slate-200 p-4 space-y-2">
          <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">How this percentage was worked out</h4>
          {card.how_calculated && <p className="text-sm text-slate-700 leading-relaxed">{card.how_calculated}</p>}
          {card.explanation && <p className="text-sm text-slate-700 leading-relaxed">{card.explanation}</p>}
        </div>

        {card.caveats.length > 0 && (
          <ul className="text-xs text-slate-500 space-y-1 list-disc pl-4">
            {card.caveats.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        )}
      </div>
    </section>
  );
};
