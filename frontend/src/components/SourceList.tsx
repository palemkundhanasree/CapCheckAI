import React, { useState } from 'react';
import { EvidenceItem } from '../types';
import { EvidenceCard } from './EvidenceCard';
import { CheckCircle, XCircle, FileText, ShieldCheck, ShieldAlert, BarChart3 } from 'lucide-react';

interface SourceListProps {
  evidenceItems: EvidenceItem[];
}

export const SourceList: React.FC<SourceListProps> = ({ evidenceItems }) => {
  const [filter, setFilter] = useState<'ALL' | 'SUPPORTS' | 'CONTRADICTS'>('ALL');

  const filtered = evidenceItems.filter((item) => {
    if (filter === 'ALL') return true;
    return item.stance === filter;
  });

  const supportCount = evidenceItems.filter((i) => i.stance === 'SUPPORTS').length;
  const contradictCount = evidenceItems.filter((i) => i.stance === 'CONTRADICTS').length;
  const contextCount = evidenceItems.filter((i) => i.stance !== 'SUPPORTS' && i.stance !== 'CONTRADICTS').length;

  const totalEvaluated = supportCount + contradictCount;
  const supportPct = totalEvaluated > 0 ? Math.round((supportCount / totalEvaluated) * 100) : 0;
  const isMeetsThreshold = supportPct >= 75 && supportCount > 0;

  return (
    <div className="space-y-4">
      {/* Source Audit Evaluation Card */}
      {evidenceItems.length > 0 && (
        <div className={`p-4 rounded-xl border ${isMeetsThreshold ? 'border-green-200 bg-green-50/40' : 'border-red-200 bg-red-50/40'}`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-2.5">
              {isMeetsThreshold ? (
                <ShieldCheck className="w-5 h-5 text-green-600 flex-shrink-0" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0" />
              )}
              <div>
                <h4 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                  <span>Source Audit Consensus:</span>
                  <span className={isMeetsThreshold ? 'text-green-700' : 'text-red-700'}>
                    {supportPct}% Verified Support
                  </span>
                </h4>
                <p className="text-xs text-slate-600">
                  {isMeetsThreshold
                    ? `Authoritative internet sources corroborate this content with ≥75% agreement (Accuracy Level of Real: ${supportPct}%).`
                    : `Content lacks required 75% verified internet corroboration or is actively refuted (Accuracy Level of Real: ${supportPct}%).`}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2 text-xs font-medium">
              <span className="px-2.5 py-1 rounded-md bg-white border border-slate-200 text-green-700 flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span>{supportCount} Supports</span>
              </span>
              <span className="px-2.5 py-1 rounded-md bg-white border border-slate-200 text-red-700 flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-red-500"></span>
                <span>{contradictCount} Contradicts</span>
              </span>
              {contextCount > 0 && (
                <span className="px-2.5 py-1 rounded-md bg-white border border-slate-200 text-slate-600">
                  {contextCount} Context
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Filter Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <span>Trusted Evidence & Source Audits ({evidenceItems.length})</span>
          </h3>
          <p className="text-xs text-slate-500">
            Authoritative documents, peer fact checks, and verified encyclopedia records retrieved for this query.
          </p>
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
              filter === 'ALL'
                ? 'bg-slate-900 text-white'
                : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
            }`}
          >
            All ({evidenceItems.length})
          </button>
          <button
            onClick={() => setFilter('SUPPORTS')}
            className={`px-3 py-1 rounded-md text-xs font-medium flex items-center space-x-1.5 transition-colors cursor-pointer ${
              filter === 'SUPPORTS'
                ? 'bg-green-600 text-white'
                : 'bg-white text-slate-600 hover:text-green-700 border border-slate-200'
            }`}
          >
            <CheckCircle className="w-3 h-3" />
            <span>Supports ({supportCount})</span>
          </button>
          <button
            onClick={() => setFilter('CONTRADICTS')}
            className={`px-3 py-1 rounded-md text-xs font-medium flex items-center space-x-1.5 transition-colors cursor-pointer ${
              filter === 'CONTRADICTS'
                ? 'bg-red-600 text-white'
                : 'bg-white text-slate-600 hover:text-red-700 border border-slate-200'
            }`}
          >
            <XCircle className="w-3 h-3" />
            <span>Contradicts ({contradictCount})</span>
          </button>
        </div>
      </div>

      {/* Grid of Evidence Cards */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((item, idx) => (
            <EvidenceCard key={item.id || idx} evidence={item} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 bg-white rounded-lg border border-slate-200 text-slate-500 text-xs">
          No sources found matching this filter criteria.
        </div>
      )}
    </div>
  );
};
