import React from 'react';
import { Shield, Lock, Trash2, Globe, Server, CheckCircle } from 'lucide-react';

export const PrivacyPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      <div className="space-y-2 text-center sm:text-left">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
          <Lock className="w-3.5 h-3.5" />
          <span>Security & Data Protection Policy</span>
        </div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
          How CapCheck AI Protects Your Data
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed max-w-2xl">
          CapCheck AI is architected with security-by-design principles, local data retention limits, and zero non-consensual third-party tracking.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-xs space-y-2.5">
          <div className="w-10 h-10 rounded-md bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <Trash2 className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Automatic Storage Cleanup</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            All submitted media files (images, audio notes, video clips) are stored in isolated per-job storage and automatically expunged after 48 hours.
          </p>
        </div>

        <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-xs space-y-2.5">
          <div className="w-10 h-10 rounded-md bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <Shield className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Permanent One-Click Shredding</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Users retain full control of their audit trail. Deleting any report immediately deletes its database records and physical file artifacts from disk.
          </p>
        </div>

        <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-xs space-y-2.5">
          <div className="w-10 h-10 rounded-md bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <Globe className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Protected SSRF Web Scraping</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            When verifying news links, our crawler strictly blocks private IP ranges, cloud metadata addresses (AWS, GCP, Azure), and internal hostnames.
          </p>
        </div>

        <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-xs space-y-2.5">
          <div className="w-10 h-10 rounded-md bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <Server className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Zero AI Training on User Media</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Your verification queries and uploads are never indexed, sold, or used to fine-tune external generative foundation models.
          </p>
        </div>
      </div>
    </div>
  );
};
