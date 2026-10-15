import React from 'react';
import { Film, Clock } from 'lucide-react';
import { MediaAnalysisDetail } from '../types';

interface VideoFrameAnalysisProps {
  analysis: MediaAnalysisDetail;
}

export const VideoFrameAnalysis: React.FC<VideoFrameAnalysisProps> = ({ analysis }) => {
  const visual = analysis.visual_findings || {};
  const frameResults = visual.frame_results || [];
  const temporal = visual.temporal_analysis || {};
  const isDeepfake = analysis.deepfake_score >= 50;

  return (
    <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
            <Film className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Video Forensics & Temporal Consistency</h3>
            <p className="text-xs text-slate-500">Checking for face replacement, boundary flickering, and frame synthesis</p>
          </div>
        </div>
        <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
          isDeepfake 
            ? 'bg-red-100 text-red-800 border-red-200' 
            : 'bg-green-100 text-green-800 border-green-200'
        }`}>
          {isDeepfake ? `Deepfake Detected (${Math.round(analysis.deepfake_score)}%)` : `Authentic Video Capture`}
        </span>
      </div>

      {/* 2 Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Temporal Coherence</div>
          <div className="text-sm font-bold text-slate-900">
            {temporal.has_flicker_anomalies ? (
              <span className="text-red-700">Frame-to-Frame Jitter Detected</span>
            ) : (
              <span className="text-green-700">Smooth Optical Continuity</span>
            )}
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            {temporal.has_flicker_anomalies
              ? 'Abrupt boundary flickering or facial contour displacement between adjacent frames.'
              : 'Consistent lighting, continuous trajectory, and natural motion dynamics.'}
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Frames Inspected</div>
          <div className="text-sm font-bold text-slate-900">
            {frameResults.length} Keyframe Samples Analyzed
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            Regularly sampled across the media duration for neural synthesis artifacts.
          </p>
        </div>
      </div>

      {/* Frame Timeline Grid */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 mb-3">
          Keyframe Forensics Breakdown
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {frameResults.map((frame: any, idx: number) => (
            <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-700 mb-1.5 font-medium">
                <span>Frame #{frame.frame_index + 1}</span>
                <span className="flex items-center space-x-1 text-slate-400 text-[11px]">
                  <Clock className="w-3 h-3" />
                  <span>{frame.timestamp_seconds}s</span>
                </span>
              </div>

              {/* Artifact score bar */}
              <div className="space-y-1 my-1.5">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-500">Anomaly:</span>
                  <span className={`font-semibold ${frame.artifact_score > 50 ? 'text-red-600' : 'text-green-600'}`}>
                    {Math.round(frame.artifact_score)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${frame.artifact_score > 50 ? 'bg-red-500' : 'bg-green-500'}`}
                    style={{ width: `${Math.min(frame.artifact_score, 100)}%` }}
                  />
                </div>
              </div>

              <div className="text-[11px] text-slate-500 truncate">
                {frame.anomalies?.length > 0 ? frame.anomalies[0] : 'Natural frame'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
