import React from 'react';
import { Image as ImageIcon, Zap, Camera, CheckCircle } from 'lucide-react';
import { MediaAnalysisDetail } from '../types';

interface ImageAnalysisProps {
  analysis: MediaAnalysisDetail;
}

export const ImageAnalysis: React.FC<ImageAnalysisProps> = ({ analysis }) => {
  const visual = analysis.visual_findings || {};
  const metadata = analysis.metadata_info || {};
  const isAi = analysis.ai_generated_score >= 50;

  return (
    <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
            <ImageIcon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Image Forensics & Artifact Inspection</h3>
            <p className="text-xs text-slate-500">Checking for AI generation grids, pixel splicing, and EXIF camera provenance</p>
          </div>
        </div>
        <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
          isAi 
            ? 'bg-red-100 text-red-800 border-red-200' 
            : 'bg-green-100 text-green-800 border-green-200'
        }`}>
          {isAi ? `AI Generated (${Math.round(analysis.ai_generated_score)}%)` : `Authentic Camera Sensor (${100 - Math.round(analysis.ai_generated_score)}% Real)`}
        </span>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        {/* Card 1: AI Patterns */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">1. Frequency Spectrum</div>
          <div className="text-sm font-bold text-slate-900">
            {visual.frequency_analysis?.abnormal_frequency_spectrum ? (
              <span className="text-red-700">AI Grid Artifacts Detected</span>
            ) : (
              <span className="text-green-700">Natural Optical Distribution</span>
            )}
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            {visual.frequency_analysis?.abnormal_frequency_spectrum
              ? 'Artificial checkerboard patterns from generative upsampling identified.'
              : 'Natural continuous optical decay confirmed across high frequencies.'}
          </p>
        </div>

        {/* Card 2: Photoshop Edits */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">2. Error Level Analysis (ELA)</div>
          <div className="text-sm font-bold text-slate-900">
            {visual.ela?.splicing_detected ? (
              <span className="text-red-700">Possible Splicing / Compositing</span>
            ) : (
              <span className="text-green-700">Uniform Compression Canvas</span>
            )}
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            {visual.ela?.splicing_detected
              ? 'Inconsistent compression error rates detected along boundary contours.'
              : 'Consistent compression noise across the entire image frame.'}
          </p>
        </div>

        {/* Card 3: Camera Provenance */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">3. Hardware Provenance</div>
          <div className="text-sm font-bold text-slate-900 flex items-center space-x-1">
            {metadata.camera_make ? (
              <>
                <Camera className="w-4 h-4 text-slate-700" />
                <span>{metadata.camera_make} {metadata.camera_model || ''}</span>
              </>
            ) : (
              <span className="text-slate-600 font-medium text-xs">Web / Cleaned Metadata</span>
            )}
          </div>
          <p className="text-xs text-slate-500 leading-snug">
            {metadata.camera_make
              ? 'Verified physical camera device profile embedded in file headers.'
              : 'EXIF metadata stripped by messaging service or web compressor.'}
          </p>
        </div>
      </div>

      {/* Clues Found List */}
      {analysis.manipulation_indicators && analysis.manipulation_indicators.length > 0 && (
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
            <Zap className="w-3.5 h-3.5 text-blue-600" />
            <span>Forensic Findings & Anomaly Indicators</span>
          </div>
          <ul className="space-y-1">
            {analysis.manipulation_indicators.map((ind, i) => (
              <li key={i} className="text-xs text-slate-700 flex items-start space-x-2">
                <span className="text-blue-600 font-bold">•</span>
                <span>{ind}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* File dimensions */}
      <div className="text-xs text-slate-500 flex flex-wrap gap-4 pt-2 border-t border-slate-100">
        <div>
          <span className="font-medium text-slate-700">Dimensions:</span> {visual.dimensions || 'Standard'}
        </div>
        <div>
          <span className="font-medium text-slate-700">Software:</span> {metadata.software || 'None recorded'}
        </div>
      </div>
    </div>
  );
};
