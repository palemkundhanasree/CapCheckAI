import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import {
  Search, Globe, Image as ImageIcon, Film, Volume2, Upload, ArrowRight, Loader2, AlertCircle,
  FileSearch, Scale, BarChart3, X,
} from 'lucide-react';
import { verificationApi } from '../../services/verificationApi';
import { reportApi } from '../../services/reportApi';
import { authService } from '../../services/authService';
import { VerificationReport, InputType } from '../../types';
import { verdictTone } from '../../components/VerdictCard';

const TABS: { id: InputType; label: string; icon: React.ElementType; accept?: string; hint: string }[] = [
  { id: 'claim', label: 'Claim', icon: Search, hint: 'Paste a statement, headline or rumour.' },
  { id: 'url', label: 'Article link', icon: Globe, hint: 'Paste the link of a news article or post.' },
  { id: 'image', label: 'Image', icon: ImageIcon, accept: '.jpg,.jpeg,.png,.webp', hint: 'JPG, PNG or WebP, up to 25 MB.' },
  { id: 'video', label: 'Video', icon: Film, accept: '.mp4,.mov,.webm,.avi', hint: 'MP4, MOV, WebM or AVI, up to 150 MB.' },
  { id: 'audio', label: 'Audio', icon: Volume2, accept: '.mp3,.wav,.m4a,.ogg', hint: 'MP3, WAV, M4A or OGG, up to 50 MB.' },
];

const TONE_CLASS = {
  green: 'bg-green-100 text-green-800 border-green-200',
  red: 'bg-red-100 text-red-800 border-red-200',
  orange: 'bg-orange-100 text-orange-800 border-orange-200',
};
const TONE_LABEL = { green: 'Real / Verified', red: 'Fake / False', orange: 'Misleading / Uncertain' };

const STEPS = [
  { icon: FileSearch, title: '1. Submit', text: 'Enter a claim or link, or upload an image, video or audio clip.' },
  { icon: Scale, title: '2. We read the sources', text: 'Fact-check records and live news articles are searched and read. Media files go through forensic tests such as error-level analysis, metadata and AI-generation signals.' },
  { icon: BarChart3, title: '3. You get a verdict and the reasons', text: 'Each result shows a verdict, a confidence score, how every source affected that score, and links so you can read them yourself.' },
];

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const fileRef = useRef<HTMLInputElement>(null);
  const user = authService.getUser();

  const [tab, setTab] = useState<InputType>('claim');
  const [text, setText] = useState('');
  const [caption, setCaption] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recent, setRecent] = useState<VerificationReport[] | null>(null);

  useEffect(() => {
    reportApi.getHistory(4).then(setRecent).catch(() => setRecent([]));
  }, []);

  useEffect(() => {
    if (location.hash === '#how-it-works') {
      document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [location.hash]);

  const current = TABS.find((t) => t.id === tab)!;
  const isFileTab = !!current.accept;

  const switchTab = (id: InputType) => {
    setTab(id);
    setFile(null);
    setError(null);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      setLoading(true);
      let job;
      if (tab === 'claim') {
        if (text.trim().length < 5) throw new Error('Enter a claim of at least 5 characters.');
        job = await verificationApi.verifyClaim(text.trim());
      } else if (tab === 'url') {
        if (!/^https?:\/\/\S+\.\S+/.test(text.trim())) throw new Error('Enter a full link starting with http:// or https://');
        job = await verificationApi.verifyUrl(text.trim());
      } else {
        if (!file) throw new Error(`Choose a ${tab} file to upload.`);
        if (tab === 'image') job = await verificationApi.verifyImage(file, caption.trim() || undefined);
        else if (tab === 'video') job = await verificationApi.verifyVideo(file);
        else job = await verificationApi.verifyAudio(file);
      }
      navigate(`/verify?jobId=${job.id}`);
    } catch (err: any) {
      setError(err.message || 'Verification could not be started. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <section className="max-w-3xl mx-auto px-4 pt-12 pb-6 text-center">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">Know What to Trust.</h1>
        <p className="mt-3 text-base text-slate-600 max-w-xl mx-auto">
          Verify claims, images and videos using AI analysis and trusted sources. Every result shows the evidence behind it.
        </p>
        {user && <p className="mt-2 text-xs text-slate-500">Signed in as {user.name || user.email}</p>}
      </section>

      <section className="max-w-3xl mx-auto px-4 pb-12" aria-label="Verify">
        <form onSubmit={submit} className="bg-white border border-slate-200 rounded-lg shadow-sm p-5 sm:p-6 space-y-4">
          <div role="tablist" className="flex flex-wrap gap-1 border-b border-slate-200 -mx-1 px-1 pb-3">
            {TABS.map((t) => {
              const Icon = t.icon;
              const active = t.id === tab;
              return (
                <button
                  key={t.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => switchTab(t.id)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium cursor-pointer ${
                    active ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {t.label}
                </button>
              );
            })}
          </div>

          {!isFileTab ? (
            <div>
              <label htmlFor="verify-input" className="block text-sm font-medium text-slate-700 mb-1.5">
                {tab === 'claim' ? 'Claim to check' : 'Article link'}
              </label>
              {tab === 'claim' ? (
                <textarea
                  id="verify-input"
                  rows={4}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="e.g. The Great Wall of China is visible from space with the naked eye."
                  className="w-full p-3 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:border-blue-600"
                />
              ) : (
                <input
                  id="verify-input"
                  type="url"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="https://example.com/news/article"
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:border-blue-600"
                />
              )}
              <p className="mt-1.5 text-xs text-slate-500">{current.hint}</p>
            </div>
          ) : (
            <div className="space-y-3">
              <input
                ref={fileRef}
                id="verify-file"
                type="file"
                accept={current.accept}
                className="sr-only"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              {!file ? (
                <label
                  htmlFor="verify-file"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => { e.preventDefault(); setFile(e.dataTransfer.files?.[0] || null); }}
                  className="flex flex-col items-center justify-center gap-1.5 py-9 border-2 border-dashed border-slate-300 rounded-md bg-paper text-slate-600 hover:border-slate-400 cursor-pointer text-center"
                >
                  <Upload className="w-6 h-6 text-slate-400" />
                  <span className="text-sm font-medium text-slate-800">Choose a {tab} file or drop it here</span>
                  <span className="text-xs text-slate-500">{current.hint}</span>
                </label>
              ) : (
                <div className="flex items-center justify-between gap-3 p-3 border border-slate-200 rounded-md bg-paper">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                  <button type="button" aria-label="Remove file" onClick={() => { setFile(null); if (fileRef.current) fileRef.current.value = ''; }}
                    className="p-1.5 rounded hover:bg-slate-200 text-slate-600 cursor-pointer">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
              {tab === 'image' && (
                <div>
                  <label htmlFor="caption" className="block text-sm font-medium text-slate-700 mb-1.5">
                    Caption or claim that came with the image <span className="font-normal text-slate-500">(optional, also fact-checked)</span>
                  </label>
                  <input
                    id="caption"
                    type="text"
                    value={caption}
                    onChange={(e) => setCaption(e.target.value)}
                    placeholder="What does the post say this image shows?"
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:border-blue-600"
                  />
                </div>
              )}
            </div>
          )}

          {error && (
            <div role="alert" className="flex items-start gap-2 p-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-60 cursor-pointer"
          >
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Starting...</> : <>Verify Now<ArrowRight className="w-4 h-4" /></>}
          </button>
        </form>
      </section>

      <section id="how-it-works" className="bg-white border-y border-slate-200 py-12 scroll-mt-16">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-xl font-semibold text-slate-900 text-center">How it works</h2>
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map(({ icon: Icon, title, text }) => (
              <div key={title} className="flex gap-3">
                <div className="w-9 h-9 flex-shrink-0 rounded-md bg-blue-50 border border-blue-100 text-blue-700 flex items-center justify-center">
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
                  <p className="mt-1 text-sm text-slate-600 leading-relaxed">{text}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap justify-center gap-3 text-xs">
            {(['green', 'red', 'orange'] as const).map((t) => (
              <span key={t} className={`px-2.5 py-1 rounded-full border font-medium ${TONE_CLASS[t]}`}>{TONE_LABEL[t]}</span>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-500 text-center max-w-xl mx-auto">
            Automated checks can be wrong. When the evidence is thin, CapCheck AI says “uncertain” instead of guessing.
          </p>
        </div>
      </section>

      <section className="max-w-3xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-slate-900">Your recent verifications</h2>
          <Link to="/history" className="text-sm text-blue-600 hover:underline">View all</Link>
        </div>
        {recent === null ? (
          <div className="text-sm text-slate-500 flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" />Loading...</div>
        ) : recent.length === 0 ? (
          <p className="text-sm text-slate-500 bg-white border border-slate-200 rounded-md p-4">
            Nothing here yet. Your checks will appear here after you run your first verification.
          </p>
        ) : (
          <ul className="bg-white border border-slate-200 rounded-md divide-y divide-slate-100">
            {recent.map((r) => {
              const tone = verdictTone(r.overall_verdict);
              return (
                <li key={r.id}>
                  <Link to={`/results/${r.id}`} className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-slate-50">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{r.title}</p>
                      <p className="text-xs text-slate-500">
                        {r.input_type} · {new Date(r.created_at + 'Z').toLocaleDateString([], { dateStyle: 'medium' })} · {r.confidence_score}% confidence
                      </p>
                    </div>
                    <span className={`flex-shrink-0 px-2 py-0.5 rounded-full border text-xs font-medium ${TONE_CLASS[tone]}`}>{TONE_LABEL[tone]}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
};
