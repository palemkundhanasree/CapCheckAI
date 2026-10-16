import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Trash2, CheckCircle, AlertCircle, LogOut, Database } from 'lucide-react';
import { authService } from '../../services/authService';
import { request, ApiError } from '../../services/apiClient';

export const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [purgeMsg, setPurgeMsg] = useState<string | null>(null);

  const token = authService.getToken() || localStorage.getItem('capcheck_token');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }

    request<any>('/admin/stats')
      .then((data) => {
        if (data) setStats(data);
      })
      .catch((err) => {
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          authService.logout();
          navigate('/login');
        }
      })
      .finally(() => setLoading(false));
  }, [token, navigate]);

  const handlePurge = async () => {
    if (!window.confirm('Trigger immediate manual purge of files older than 24 hours?')) return;
    try {
      const data = await request<{ message: string }>('/admin/purge-old-files', {
        method: 'POST',
      });
      setPurgeMsg(data.message);
    } catch (err: any) {
      setPurgeMsg(err?.message || 'Purge failed.');
    }
  };

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  if (loading) {
    return <div className="py-24 text-center text-slate-500 text-xs">Loading telemetry & diagnostics...</div>;
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-100 text-blue-600 flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">System Dashboard & Health</h1>
            <p className="text-xs text-slate-500">CapCheck AI operational telemetry and media retention status.</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium border border-slate-200 transition-colors cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>

      {purgeMsg && (
        <div className="p-3.5 rounded-lg bg-green-50 border border-green-200 text-green-800 text-xs font-medium flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-green-600" />
          <span>{purgeMsg}</span>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-xs">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Checks</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{stats?.total_jobs || 0}</div>
        </div>
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-xs">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Completed</div>
          <div className="text-2xl font-bold text-green-700 mt-1">{stats?.completed_jobs || 0}</div>
        </div>
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-xs">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Incomplete / Errors</div>
          <div className="text-2xl font-bold text-red-700 mt-1">{stats?.failed_jobs || 0}</div>
        </div>
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-xs">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Stored Reports</div>
          <div className="text-2xl font-bold text-blue-700 mt-1">{stats?.total_reports || 0}</div>
        </div>
      </div>

      {/* Storage and Actions */}
      <div className="p-6 rounded-lg bg-white border border-slate-200 space-y-3 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
          <Database className="w-4 h-4 text-blue-600" />
          <span>File Storage & Retention Sweep</span>
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          Uploaded media files are automatically purged after 48 hours. You can trigger an immediate maintenance sweep below to delete temp files older than 24 hours.
        </p>

        <button
          onClick={handlePurge}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-md bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Purge Uploads Older Than 24 Hours</span>
        </button>
      </div>
    </div>
  );
};
