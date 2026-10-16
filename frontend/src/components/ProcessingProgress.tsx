import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle, AlertCircle, Shield } from 'lucide-react';
import { verificationApi } from '../services/verificationApi';
import { JobStatus } from '../types';

interface ProcessingProgressProps {
  jobId: string;
  onComplete: (reportId: string) => void;
  onError?: (errMessage: string) => void;
  onReset?: () => void;
}

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({ jobId, onComplete, onError, onReset }) => {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: any = null;

    const poll = async () => {
      try {
        const data = await verificationApi.getJobStatus(jobId);
        setJob(data);

        if (data.status === 'completed' && data.report_id) {
          clearInterval(interval);
          onComplete(data.report_id);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          const err = data.error_message || 'The verification engine encountered an unexpected issue while processing this source.';
          setError(err);
          if (onError) onError(err);
        }
      } catch (err: any) {
        clearInterval(interval);
        const fallbackMsg = err.message || 'Unable to communicate with the verification server. Please check your connection.';
        setError(fallbackMsg);
        if (onError) onError(fallbackMsg);
      }
    };

    poll();
    interval = setInterval(poll, 1000);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobId, onComplete, onError]);

  const stages = [
    { threshold: 25, label: 'Reading & parsing submitted input' },
    { threshold: 50, label: 'Querying international fact-checking databases & web sources' },
    { threshold: 75, label: 'Running forensic image, video, and audio feature detectors' },
    { threshold: 95, label: 'Synthesizing verdict, stance weighting, and confidence score' },
  ];

  const currentProgress = job?.progress || 10;

  return (
    <div className="max-w-xl mx-auto my-8 p-6 sm:p-8 rounded-xl bg-white border border-slate-200 shadow-sm text-center space-y-6">
      {/* Icon */}
      <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center ${
        error ? 'bg-red-50 border border-red-100 text-red-600' : job?.status === 'completed' ? 'bg-green-50 border border-green-100 text-green-600' : 'bg-blue-50 border border-blue-100 text-blue-600'
      }`}>
        {error ? (
          <AlertCircle className="w-6 h-6 text-red-600" />
        ) : job?.status === 'completed' ? (
          <CheckCircle className="w-6 h-6 text-green-600" />
        ) : (
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        )}
      </div>

      <div>
        <h3 className={`text-lg font-bold ${error ? 'text-red-700' : 'text-slate-900'}`}>
          {error ? 'Verification Scan Notice' : job?.status === 'completed' ? 'Verification Complete!' : 'Cross-Referencing Evidence...'}
        </h3>
        <p className="text-xs text-slate-600 mt-1">
          {error ? 'The scan could not complete due to target source restrictions.' : job?.current_stage || 'Connecting to CapCheck forensics engine...'}
        </p>
      </div>

      {/* Error Details & Recovery Action */}
      {error && (
        <div className="space-y-4">
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 text-left">
            <span className="font-semibold block mb-0.5">Diagnostic Details:</span>
            <span>{error}</span>
          </div>

          <div className="flex items-center justify-center space-x-3 pt-2">
            <button
              type="button"
              onClick={() => {
                if (onReset) {
                  onReset();
                } else {
                  window.location.href = '/verify';
                }
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-lg shadow-sm transition-colors cursor-pointer"
            >
              Verify Another Claim or URL
            </button>
            <button
              type="button"
              onClick={() => {
                window.location.reload();
              }}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs rounded-lg transition-colors cursor-pointer"
            >
              Retry Scan
            </button>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {!error && (
        <div className="space-y-2">
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-blue-600 h-full rounded-full transition-all duration-300 ease-out"
              style={{ width: `${currentProgress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-500 font-medium">
            <span>Stage Progress</span>
            <span className="font-semibold text-slate-800">{currentProgress}%</span>
          </div>
        </div>
      )}

      {/* Stage Indicators */}
      {!error && (
        <div className="space-y-2 text-left pt-4 border-t border-slate-100">
          {stages.map((st, idx) => {
            const isDone = currentProgress >= st.threshold;
            const isCurrent = currentProgress < st.threshold && (idx === 0 || currentProgress >= stages[idx - 1].threshold);
            return (
              <div key={idx} className="flex items-center space-x-2.5 text-xs">
                <span className={`w-2 h-2 rounded-full ${isDone ? 'bg-green-500' : isCurrent ? 'bg-blue-500 animate-pulse' : 'bg-slate-300'}`} />
                <span className={isDone ? 'text-slate-800 font-medium' : isCurrent ? 'text-blue-700 font-semibold' : 'text-slate-400'}>
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
