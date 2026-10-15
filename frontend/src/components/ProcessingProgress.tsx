import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle, AlertCircle, Shield } from 'lucide-react';
import { verificationApi } from '../services/verificationApi';
import { JobStatus } from '../types';

interface ProcessingProgressProps {
  jobId: string;
  onComplete: (reportId: string) => void;
  onError?: (errMessage: string) => void;
}

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({ jobId, onComplete, onError }) => {
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
          const err = data.error_message || 'Verification pipeline encountered a failure.';
          setError(err);
          if (onError) onError(err);
        }
      } catch (err: any) {
        clearInterval(interval);
        setError(err.message || 'Failed to poll verification progress.');
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
      <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
        {error ? (
          <AlertCircle className="w-6 h-6 text-red-600" />
        ) : job?.status === 'completed' ? (
          <CheckCircle className="w-6 h-6 text-green-600" />
        ) : (
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        )}
      </div>

      <div>
        <h3 className="text-lg font-bold text-slate-900">
          {error ? 'Verification Paused' : job?.status === 'completed' ? 'Verification Complete!' : 'Cross-Referencing Evidence...'}
        </h3>
        <p className="text-xs text-slate-600 mt-1">
          {error ? error : job?.current_stage || 'Connecting to CapCheck forensics engine...'}
        </p>
      </div>

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
