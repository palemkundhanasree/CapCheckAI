import React from 'react';
import { Shield, CheckCircle, AlertTriangle, HelpCircle } from 'lucide-react';

interface ConfidenceMeterProps {
  score: number;
  level: 'LOW' | 'MEDIUM' | 'HIGH';
  className?: string;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({ score, level, className = '' }) => {
  const getStyle = () => {
    if (level === 'HIGH') {
      return {
        strokeColor: '#16a34a',
        badge: 'bg-green-100 text-green-800 border-green-200',
        text: 'High Confidence',
        desc: 'Multiple verified independent sources and forensic checks strongly converge.',
        icon: <CheckCircle className="w-4 h-4 text-green-600" />
      };
    }
    if (level === 'MEDIUM') {
      return {
        strokeColor: '#ea580c',
        badge: 'bg-orange-100 text-orange-800 border-orange-200',
        text: 'Medium Confidence',
        desc: 'Documented evidence found; some minor corroborating indicators are still developing.',
        icon: <AlertTriangle className="w-4 h-4 text-orange-600" />
      };
    }
    return {
      strokeColor: '#2563eb',
      badge: 'bg-blue-100 text-blue-800 border-blue-200',
      text: 'Low Confidence / Uncertain',
      desc: 'Insufficient public documentation or low media resolution prevents conclusive certainty.',
      icon: <HelpCircle className="w-4 h-4 text-blue-600" />
    };
  };

  const style = getStyle();

  // SVG circular dimensions
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className={`p-6 rounded-xl bg-white border border-slate-200 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-900">TruthLens Confidence Score</h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style.badge}`}>
          {style.text}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* Radial Meter */}
        <div className="relative w-24 h-24 flex-shrink-0 flex items-center justify-center">
          <svg className="w-24 h-24 transform -rotate-90">
            <circle
              cx="48"
              cy="48"
              r={radius}
              stroke="#e2e8f0"
              strokeWidth="6"
              fill="transparent"
            />
            <circle
              cx="48"
              cy="48"
              r={radius}
              stroke={style.strokeColor}
              strokeWidth="6"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-700 ease-out"
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <span className="text-xl font-bold text-slate-900">{Math.round(score)}%</span>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Certainty</span>
          </div>
        </div>

        {/* Explanation */}
        <div className="space-y-1 text-center sm:text-left">
          <div className="flex items-center justify-center sm:justify-start space-x-1.5 text-slate-900 font-semibold text-sm">
            {style.icon}
            <span>{style.text} ({Math.round(score)}% aggregate agreement)</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            {style.desc}
          </p>
          <p className="text-[11px] text-slate-500 pt-1">
            Calculated through source credibility ratings, claim stance alignment, and multi-detector cross-verification.
          </p>
        </div>
      </div>
    </div>
  );
};
