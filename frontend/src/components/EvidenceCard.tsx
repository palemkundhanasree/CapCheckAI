import React from 'react';
import { ExternalLink, Check, X, AlertCircle, FileText, CheckCircle2 } from 'lucide-react';
import { EvidenceItem } from '../types';

interface EvidenceCardProps {
  evidence: EvidenceItem;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence }) => {
  const getStanceStyle = (stance: string) => {
    switch (stance.toUpperCase()) {
      case 'SUPPORTS':
        return {
          badge: 'bg-green-100 text-green-800 border-green-200',
          icon: <Check className="w-3 h-3 text-green-700" />,
          label: 'Supports'
        };
      case 'CONTRADICTS':
        return {
          badge: 'bg-red-100 text-red-800 border-red-200',
          icon: <X className="w-3 h-3 text-red-700" />,
          label: 'Contradicts'
        };
      case 'CONTEXT':
        return {
          badge: 'bg-orange-100 text-orange-800 border-orange-200',
          icon: <AlertCircle className="w-3 h-3 text-orange-700" />,
          label: 'Provides Context'
        };
      default:
        return {
          badge: 'bg-slate-100 text-slate-800 border-slate-200',
          icon: <FileText className="w-3 h-3 text-slate-600" />,
          label: 'Reference'
        };
    }
  };

  const stanceStyle = getStanceStyle(evidence.stance);

  return (
    <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-colors">
      <div>
        {/* Source header & stance badge */}
        <div className="flex items-start justify-between gap-3 mb-2.5">
          <div className="flex items-center space-x-1.5">
            <span className="font-semibold text-slate-900 text-xs">
              {evidence.source_name}
            </span>
            {evidence.credibility_score >= 85 && (
              <span className="text-[10px] text-blue-700 font-semibold bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                High reliability
              </span>
            )}
          </div>
          <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold border ${stanceStyle.badge}`}>
            {stanceStyle.icon}
            <span>{stanceStyle.label}</span>
          </span>
        </div>

        {/* Title */}
        <h4 className="text-xs font-semibold text-slate-800 line-clamp-2 mb-2">
          {evidence.title}
        </h4>

        {/* Snippet */}
        <p className="text-xs text-slate-600 leading-relaxed line-clamp-4 bg-slate-50 p-2.5 rounded border border-slate-100 mb-3">
          "{evidence.snippet}"
        </p>
      </div>

      {/* Footer link */}
      <div className="flex items-center justify-between pt-2.5 border-t border-slate-100 text-xs">
        <span className="text-slate-400 text-[11px]">
          {evidence.publish_date || 'Fact-checking record'}
        </span>

        {evidence.source_url ? (
          <a
            href={evidence.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1 text-blue-600 hover:text-blue-700 font-medium text-xs transition-colors"
          >
            <span>Read Source</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        ) : (
          <span className="text-slate-400 text-[11px]">Direct record</span>
        )}
      </div>
    </div>
  );
};
