import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  Search,
  Globe,
  Image as ImageIcon,
  Film,
  Volume2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Database,
  Cpu,
  FileText,
  Clock,
  ExternalLink
} from 'lucide-react';
import { verificationApi } from '../../services/verificationApi';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'claim' | 'url' | 'image' | 'video' | 'audio'>('claim');
  const [claimText, setClaimText] = useState('');
  const [urlText, setUrlText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (activeTab === 'claim') {
        if (!claimText.trim()) throw new Error('Please enter a claim to verify.');
        const job = await verificationApi.verifyClaim(claimText);
        navigate(`/verify?jobId=${job.id}`);
      } else if (activeTab === 'url') {
        if (!urlText.trim()) throw new Error('Please enter an article URL.');
        const job = await verificationApi.verifyUrl(urlText);
        navigate(`/verify?jobId=${job.id}`);
      } else if (activeTab === 'image') {
        if (!selectedFile) throw new Error('Please select an image file to upload.');
        const job = await verificationApi.verifyImage(selectedFile);
        navigate(`/verify?jobId=${job.id}`);
      } else if (activeTab === 'video') {
        if (!selectedFile) throw new Error('Please select a video file to upload.');
        const job = await verificationApi.verifyVideo(selectedFile);
        navigate(`/verify?jobId=${job.id}`);
      } else if (activeTab === 'audio') {
        if (!selectedFile) throw new Error('Please select an audio file to upload.');
        const job = await verificationApi.verifyAudio(selectedFile);
        navigate(`/verify?jobId=${job.id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Verification could not be initiated.');
    } finally {
      setLoading(false);
    }
  };

  const sampleClaims = [
    { text: "The Earth orbits around the Sun.", expected: "Verified", color: "green" },
    { text: "Drinking disinfectant or bleach is a cure for viral infections.", expected: "False", color: "red" },
    { text: "The Great Wall of China is visible from space with the naked eye.", expected: "Misleading", color: "orange" },
  ];

  const recentChecks = [
    {
      id: "demo-1",
      title: "Scientific planetary motion of planet Earth",
      type: "Claim",
      verdict: "Real / Verified",
      status: "green",
      confidence: 96,
      date: "10 mins ago",
      snippet: "Supported by NASA planetary observation and astrophysics consensus."
    },
    {
      id: "demo-2",
      title: "Miracle chemical cures for coronavirus infections",
      type: "Claim",
      verdict: "Fake / False",
      status: "red",
      confidence: 99,
      date: "35 mins ago",
      snippet: "Debunked by World Health Organization. Toxic ingestion causes severe chemical injury."
    },
    {
      id: "demo-3",
      title: "Visible landmarks from low Earth orbit",
      type: "Claim",
      verdict: "Misleading / Uncertain",
      status: "orange",
      confidence: 88,
      date: "1 hour ago",
      snippet: "Astronaut observation records confirm Great Wall is virtually indistinguishable without optical magnification."
    }
  ];

  return (
    <div className="space-y-16 py-10">
      {/* Hero Section */}
      <section className="max-w-4xl mx-auto px-4 text-center space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
          <Shield className="w-3.5 h-3.5" />
          <span>CapCheck AI Forensic Intelligence • Strict ≥75% Source Standard</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-900">
          Know What to Trust.
        </h1>
        <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto">
          Verify claims, news articles, images, and videos using artificial intelligence and independent, verified sources.
        </p>
      </section>

      {/* Verification Card Area */}
      <section className="max-w-3xl mx-auto px-4">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
          {/* Tabs */}
          <div className="flex border-b border-slate-200 pb-3 space-x-2 sm:space-x-4 overflow-x-auto">
            <button
              onClick={() => { setActiveTab('claim'); setSelectedFile(null); }}
              className={`flex items-center space-x-2 pb-2 text-xs sm:text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                activeTab === 'claim'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Search className="w-4 h-4" />
              <span>Enter Claim</span>
            </button>

            <button
              onClick={() => { setActiveTab('url'); setSelectedFile(null); }}
              className={`flex items-center space-x-2 pb-2 text-xs sm:text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                activeTab === 'url'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Globe className="w-4 h-4" />
              <span>News URL</span>
            </button>

            <button
              onClick={() => setActiveTab('image')}
              className={`flex items-center space-x-2 pb-2 text-xs sm:text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                activeTab === 'image'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
              <span>Upload Image</span>
            </button>

            <button
              onClick={() => setActiveTab('video')}
              className={`flex items-center space-x-2 pb-2 text-xs sm:text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                activeTab === 'video'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Film className="w-4 h-4" />
              <span>Upload Video</span>
            </button>

            <button
              onClick={() => setActiveTab('audio')}
              className={`flex items-center space-x-2 pb-2 text-xs sm:text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                activeTab === 'audio'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Volume2 className="w-4 h-4" />
              <span>Audio Clip</span>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleVerifySubmit} className="mt-6 space-y-4">
            {activeTab === 'claim' && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Statement or Claim to Verify
                </label>
                <textarea
                  rows={3}
                  value={claimText}
                  onChange={(e) => setClaimText(e.target.value)}
                  placeholder="Paste or write any statement, viral rumor, quote, or statistic..."
                  className="w-full p-3.5 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                />
              </div>
            )}

            {activeTab === 'url' && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Article or Website URL
                </label>
                <input
                  type="url"
                  value={urlText}
                  onChange={(e) => setUrlText(e.target.value)}
                  placeholder="https://example-news.org/article/breaking-story"
                  className="w-full p-3.5 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                />
              </div>
            )}

            {(activeTab === 'image' || activeTab === 'video' || activeTab === 'audio') && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Upload {activeTab === 'image' ? 'Image File (JPEG, PNG, WEBP)' : activeTab === 'video' ? 'Video File (MP4, WEBM)' : 'Audio File (WAV, MP3)'}
                </label>
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center hover:border-slate-300 transition-colors">
                  <input
                    type="file"
                    id="media-upload"
                    accept={activeTab === 'image' ? 'image/*' : activeTab === 'video' ? 'video/*' : 'audio/*'}
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                  <label htmlFor="media-upload" className="cursor-pointer space-y-2 block">
                    <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center mx-auto">
                      {activeTab === 'image' && <ImageIcon className="w-5 h-5" />}
                      {activeTab === 'video' && <Film className="w-5 h-5" />}
                      {activeTab === 'audio' && <Volume2 className="w-5 h-5" />}
                    </div>
                    <div className="text-sm font-medium text-slate-700">
                      {selectedFile ? selectedFile.name : 'Click to select file from device'}
                    </div>
                    <p className="text-xs text-slate-500">
                      {selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB selected` : 'Drag and drop or browse files'}
                    </p>
                  </label>
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-md">
                {error}
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
              <div className="text-xs text-slate-500">
                Verified against encyclopedic sources, international fact-checking databases, and forensic detectors.
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer"
              >
                <span>{loading ? 'Verifying...' : 'Verify Now'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>

          {/* Quick Examples */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <div className="text-xs text-slate-500 mb-2 font-medium">Try verifying these example statements:</div>
            <div className="flex flex-wrap gap-2">
              {sampleClaims.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setActiveTab('claim');
                    setClaimText(item.text);
                  }}
                  className="text-left text-xs px-3 py-1.5 rounded-md bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 transition-colors flex items-center space-x-1.5 cursor-pointer"
                >
                  <span className={`w-2 h-2 rounded-full ${item.color === 'green' ? 'bg-green-500' : item.color === 'red' ? 'bg-red-500' : 'bg-orange-500'}`} />
                  <span className="truncate max-w-[260px]">{item.text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Result Status System Explanation */}
      <section className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Clear, Objective Verdicts (≥75% Verification Rule)</h2>
          <p className="text-sm text-slate-600 mt-1">
            CapCheck AI requires at least 75% verified support across authoritative internet sources to declare information Real.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-5 rounded-lg border border-green-200 bg-green-50/20 space-y-2">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-sm text-green-900">Green: Real / Verified (≥75%)</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Substantiated by at least 75% supporting evidence from verified registries, scientific consensus, or authentic camera sensor noise.
            </p>
          </div>

          <div className="bg-white p-5 rounded-lg border border-red-200 bg-red-50/20 space-y-2">
            <div className="flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <h3 className="font-semibold text-sm text-red-900">Red: Fake / False (&lt;75%)</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Contradicted by factual records, debunked by established fact-checkers, or failing the required 75% credibility threshold.
            </p>
          </div>

          <div className="bg-white p-5 rounded-lg border border-orange-200 bg-orange-50/20 space-y-2">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              <h3 className="font-semibold text-sm text-orange-900">Orange: Misleading / Context</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Contains partial truth but omits vital context, uses unverified claims, or repurposes authentic media with misleading captions.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="bg-slate-100 py-12 border-y border-slate-200">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">How CapCheck AI Works</h2>
            <p className="text-sm text-slate-600 mt-1 max-w-xl mx-auto">
              Our multi-stage verification architecture searches internet sources and analyzes text claims, image metadata, and audio-video temporal signals.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="w-8 h-8 rounded bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-sm">
                1
              </div>
              <h3 className="font-semibold text-slate-900 text-base">Submit Claim or Media</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Provide text statements, news URLs, photos, videos, or audio voice recordings. Our system isolates assertions and verifies file integrity.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="w-8 h-8 rounded bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-sm">
                2
              </div>
              <h3 className="font-semibold text-slate-900 text-base">Cross-Source Forensics</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                We query global fact-checking registries, authoritative encyclopedic sources, error-level analysis (ELA), facial landmarks, and voice spectral cues.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="w-8 h-8 rounded bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-sm">
                3
              </div>
              <h3 className="font-semibold text-slate-900 text-base">Transparent Verdict</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                You receive a color-coded status, confidence percentage, direct citations to trusted sources, and an explanation of why the conclusion was reached.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Verifications Feed */}
      <section className="max-w-4xl mx-auto px-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Recent Verifications</h2>
            <p className="text-xs text-slate-500">Live checks processed across web claims and digital media</p>
          </div>
          <Link
            to="/history"
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
          >
            <span>View All Records</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-slate-200 bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          {recentChecks.map((item) => (
            <div key={item.id} className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50 transition-colors">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                    item.status === 'green'
                      ? 'bg-green-100 text-green-800'
                      : item.status === 'red'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-orange-100 text-orange-800'
                  }`}>
                    {item.verdict}
                  </span>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs text-slate-500">{item.confidence}% Confidence</span>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs text-slate-400 flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{item.date}</span>
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-slate-900">{item.title}</h4>
                <p className="text-xs text-slate-600">{item.snippet}</p>
              </div>

              <Link
                to="/verify"
                className="self-start sm:self-center px-3 py-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-xs font-medium text-slate-700 whitespace-nowrap shadow-xs"
              >
                Inspect
              </Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
