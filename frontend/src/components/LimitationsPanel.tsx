import React from 'react';
import { CheckCircle, Shield, Info } from 'lucide-react';

interface LimitationsPanelProps {
  limitations: string[];
  checksPerformed: string[];
  checksUnavailable: string[];
}

export const LimitationsPanel: React.FC<LimitationsPanelProps> = ({
  limitations = [],
  checksPerformed = [],
  checksUnavailable = []
}) => {
  return (
    <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm space-y-6">
      <div className="flex items-center space-x-2.5 pb-4 border-b border-slate-100">
        <Shield className="w-5 h-5 text-blue-600" />
        <div>
          <h3 className="text-sm font-bold text-slate-900">Audit Scope & Analytical Limitations</h3>
          <p className="text-xs text-slate-500">Methodological details on forensics executed and data constraints</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Checks Performed */}
        <div className="space-y-2.5">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-green-600" />
            <span>Forensic Checks Executed ({checksPerformed.length})</span>
          </h4>
          <ul className="space-y-1.5">
            {checksPerformed.map((chk, idx) => (
              <li key={idx} className="text-xs text-slate-700 flex items-start space-x-2 bg-slate-50 p-2.5 rounded border border-slate-100">
                <span className="text-green-600 font-bold">✓</span>
                <span>{chk}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Limitations */}
        <div className="space-y-2.5">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
            <Info className="w-3.5 h-3.5 text-blue-600" />
            <span>Methodological Considerations</span>
          </h4>
          <ul className="space-y-1.5">
            {limitations.map((lim, idx) => (
              <li key={idx} className="text-xs text-slate-700 flex items-start space-x-2 bg-slate-50 p-2.5 rounded border border-slate-100">
                <span className="text-blue-600 font-bold">•</span>
                <span>{lim}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
