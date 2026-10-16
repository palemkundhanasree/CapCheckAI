import React, { useState } from 'react';
import { Download, Trash2, Share2, Check, AlertCircle } from 'lucide-react';
import { reportApi } from '../services/reportApi';

interface ReportDownloadProps {
  reportId: string;
  onDeleted?: () => void;
}

export const ReportDownload: React.FC<ReportDownloadProps> = ({ reportId, onDeleted }) => {
  const [copied, setCopied] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this report? Any uploaded files will be permanently deleted.')) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      await reportApi.deleteReport(reportId);
      if (onDeleted) onDeleted();
    } catch (err: any) {
      setError(err.message || 'Failed to delete report.');
      setDeleting(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
      <div className="flex items-center space-x-2.5">
        <a
          href={reportApi.getPdfDownloadUrl(reportId)}
          download
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium shadow-xs transition-colors cursor-pointer"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download PDF Forensic Report</span>
        </a>

        <button
          onClick={handleShare}
          className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-md bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium border border-slate-200 transition-colors cursor-pointer"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Share2 className="w-3.5 h-3.5 text-slate-500" />}
          <span>{copied ? 'Link Copied!' : 'Share Audit Link'}</span>
        </button>
      </div>

      <div className="flex items-center space-x-3">
        {error && <span className="text-xs text-red-600 flex items-center space-x-1"><AlertCircle className="w-3.5 h-3.5" /><span>{error}</span></span>}
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-md bg-white hover:bg-red-50 text-red-600 text-xs font-medium border border-red-200 transition-colors disabled:opacity-50 cursor-pointer"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>{deleting ? 'Deleting...' : 'Delete Report'}</span>
        </button>
      </div>
    </div>
  );
};
