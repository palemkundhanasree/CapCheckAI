import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { History, Search, FileText, Globe, Image as ImageIcon, Film, Volume2, ArrowRight, Trash2, Download } from 'lucide-react';
import { reportApi } from '../../services/reportApi';
import { ApiError } from '../../services/apiClient';
import { VerificationReport } from '../../types';
import { verdictTone } from '../../components/VerdictCard';

export const HistoryPage: React.FC = () => {
  const [reports, setReports] = useState<VerificationReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = () => {
    setLoading(true);
    setError(null);
    reportApi.getHistory(50)
      .then((data) => setReports(Array.isArray(data) ? data : []))
      .catch((err: unknown) => {
        setReports([]);
        setError(err instanceof ApiError || err instanceof Error
          ? err.message
          : 'Could not load your history.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDownload = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const blob = await reportApi.getPdfBlob(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CapCheck_Report_${id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Could not download the report.');
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm('Delete this report and its associated forensics data?')) return;
    try {
      await reportApi.deleteReport(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
    } catch {
      alert('Failed to delete report.');
    }
  };

  const filtered = reports.filter((r) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch = (r.title || '').toLowerCase().includes(term) ||
                          (r.summary || '').toLowerCase().includes(term);
    const matchesType = typeFilter === 'ALL' || r.input_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'url':
        return <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-medium"><Globe className="w-3 h-3" /><span>Article</span></span>;
      case 'image':
        return <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 text-[11px] font-medium"><ImageIcon className="w-3 h-3" /><span>Photo</span></span>;
      case 'video':
        return <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-200 text-[11px] font-medium"><Film className="w-3 h-3" /><span>Video</span></span>;
      case 'audio':
        return <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-[11px] font-medium"><Volume2 className="w-3 h-3" /><span>Audio</span></span>;
      default:
        return <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 text-[11px] font-medium"><FileText className="w-3 h-3" /><span>Claim</span></span>;
    }
  };

  const getVerdictStyle = (overall: string) => {
    const tone = verdictTone(overall);
    if (tone === 'green') return 'bg-green-100 text-green-800 border-green-200';
    if (tone === 'red') return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-orange-100 text-orange-800 border-orange-200';
  };

  const filterTabs = [
    { id: 'ALL', label: 'All Checks' },
    { id: 'claim', label: 'Claims' },
    { id: 'url', label: 'Articles' },
    { id: 'image', label: 'Photos' },
    { id: 'video', label: 'Videos' },
    { id: 'audio', label: 'Audio' },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
              <History className="w-6 h-6" />
            </div>
            <span>Verification History</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse, search, export PDF forensic summaries, or manage previous checks.
          </p>
        </div>

        <Link
          to="/verify"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-sm transition-colors"
        >
          <span>Verify New Item</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by claim title or keywords..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-xs focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-colors"
          />
        </div>

        <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {filterTabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTypeFilter(t.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                typeFilter === t.id
                  ? 'bg-slate-900 text-white font-semibold'
                  : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Reports List */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-xs">
          Loading past verification records...
        </div>
      ) : error ? (
        <div className="text-center py-14 bg-white rounded-lg border border-red-200 space-y-3">
          <h3 className="text-sm font-semibold text-red-700">Could not load your history</h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto">{error}</p>
          <button
            onClick={fetchHistory}
            className="inline-flex items-center px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-700 text-white text-xs font-medium cursor-pointer"
          >
            Try again
          </button>
        </div>
      ) : filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map((r) => (
            <Link
              key={r.id}
              to={`/results/${r.id}`}
              className="block p-4 sm:p-5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 shadow-xs transition-colors group"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    {getTypeBadge(r.input_type)}
                    <span className="text-slate-300">•</span>
                    <span className="text-xs text-slate-400 font-medium">
                      {Number.isNaN(new Date(r.created_at).getTime())
                        ? ''
                        : new Date(r.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                    {r.title}
                  </h3>
                  <p className="text-xs text-slate-600 line-clamp-2 max-w-3xl leading-relaxed">
                    {r.summary}
                  </p>
                </div>

                <div className="flex items-center space-x-4 flex-shrink-0">
                  <div className="text-right">
                    <span className={`inline-block px-2.5 py-0.5 rounded text-xs font-semibold border ${getVerdictStyle(r.overall_verdict)}`}>
                      {r.verdict_label}
                    </span>
                    <div className="text-[11px] text-slate-500 font-medium mt-1">
                      {r.correctness_score != null ? `${Math.round(r.correctness_score)}% likely correct` : `${Math.round(r.confidence_score || 0)}% confidence`}
                    </div>
                  </div>

                  <div className="flex items-center space-x-1" onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      onClick={(e) => handleDownload(e, r.id)}
                      title="Download PDF"
                      className="p-2 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => handleDelete(e, r.id)}
                      title="Delete Report"
                      className="p-2 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-white rounded-lg border border-slate-200 space-y-3">
          <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">No Past Verification Records</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {searchTerm || typeFilter !== 'ALL'
              ? 'No reports match your search query or chosen filter.'
              : 'You haven\'t verified any claims, images, or audio yet.'}
          </p>
          <Link
            to="/verify"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium shadow-sm transition-colors"
          >
            <span>Verify Your First Claim</span>
          </Link>
        </div>
      )}
    </div>
  );
};
