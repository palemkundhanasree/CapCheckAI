import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import { reportApi } from '../../services/reportApi';
import { VerificationReport } from '../../types';

import { VerdictCard } from '../../components/VerdictCard';
import { ConfidenceMeter } from '../../components/ConfidenceMeter';
import { SourceList } from '../../components/SourceList';
import { ImageAnalysis } from '../../components/ImageAnalysis';
import { VideoFrameAnalysis } from '../../components/VideoFrameAnalysis';
import { AudioAnalysis } from '../../components/AudioAnalysis';
import { TranscriptViewer } from '../../components/TranscriptViewer';
import { LimitationsPanel } from '../../components/LimitationsPanel';
import { ReportDownload } from '../../components/ReportDownload';

export const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<VerificationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    reportApi.getReport(id)
      .then(setReport)
      .catch((err) => setError(err.message || 'Report not found.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-24 text-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">Retrieving Verification Audit...</h2>
        <p className="text-xs text-slate-500">Compiling source consensus, forensic checks, and confidence ratings.</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-md mx-auto py-20 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-50 border border-red-100 text-red-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Report Unavailable</h2>
        <p className="text-xs text-slate-600">
          {error || 'This report may have been purged or does not exist.'}
        </p>
        <Link
          to="/verify"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Verify Another Item</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Top Breadcrumb Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/history"
          className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Verification History</span>
        </Link>

        <div className="text-xs text-slate-500 font-mono bg-white px-2.5 py-1 rounded border border-slate-200">
          Audit ID: #{report.id.substring(0, 8)}
        </div>
      </div>

      {/* Main Verdict Card with Media Preview and Reason */}
      <VerdictCard report={report} />

      {/* Confidence Meter */}
      <ConfidenceMeter score={report.confidence_score} level={report.confidence_level} />

      {/* Detailed Analysis Modules */}
      {report.media_analysis && report.media_analysis.media_type === 'image' && (
        <ImageAnalysis analysis={report.media_analysis} />
      )}

      {report.media_analysis && report.media_analysis.media_type === 'video' && (
        <VideoFrameAnalysis analysis={report.media_analysis} />
      )}

      {report.media_analysis && report.media_analysis.media_type === 'audio' && (
        <AudioAnalysis analysis={report.media_analysis} />
      )}

      {/* Transcript Viewer if Audio transcript present */}
      {report.media_analysis?.transcript && (
        <TranscriptViewer
          transcript={report.media_analysis.transcript}
          segments={report.media_analysis.audio_findings?.segments}
        />
      )}

      {/* Documented Evidence & Fact-Checks List */}
      <SourceList evidenceItems={report.evidence_items || []} />

      {/* Limitations & Methodology Panel */}
      <LimitationsPanel
        limitations={report.limitations || []}
        checksPerformed={report.checks_performed || []}
        checksUnavailable={report.checks_unavailable || []}
      />

      {/* Report Download and Shredding Action Bar */}
      <ReportDownload
        reportId={report.id}
        onDeleted={() => navigate('/history')}
      />
    </div>
  );
};
