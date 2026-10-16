import React, { useState } from 'react';
import { Globe, ArrowRight, AlertCircle, Shield } from 'lucide-react';

interface NewsUrlInputProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export const NewsUrlInput: React.FC<NewsUrlInputProps> = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let cleanUrl = url.trim();
    if (!cleanUrl) {
      setError('Please paste a link to an article or web page.');
      return;
    }

    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = `https://${cleanUrl}`;
    }

    try {
      const parsed = new URL(cleanUrl);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        setError('URL must begin with http:// or https://');
        return;
      }
      if (!parsed.hostname.includes('.')) {
        setError('Please enter a valid website domain (e.g. bbc.com or reuters.com).');
        return;
      }
    } catch {
      setError('Invalid link format. Please provide a valid web URL.');
      return;
    }

    setError(null);
    onSubmit(cleanUrl);
  };

  const sampleUrls = [
    { label: 'NASA Heliocentric Overview', url: 'https://solarsystem.nasa.gov/planets/earth/overview/' },
    { label: 'Encyclopaedia Britannica Paris', url: 'https://www.britannica.com/place/Paris' },
    { label: 'BBC News', url: 'https://www.bbc.com/news' },
    { label: 'Reuters World News', url: 'https://www.reuters.com/world/' },
  ];

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            News Article or Website URL
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Globe className="w-4 h-4" />
            </div>
            <input
              type="url"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (error) setError(null);
              }}
              placeholder="https://example.com/news/article-headline"
              className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-colors"
              disabled={isLoading}
            />
          </div>
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-xs text-red-700 bg-red-50 p-3 rounded-lg border border-red-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex items-center space-x-2 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
          <Shield className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <span>
            <b>Protected SSRF Scanner:</b> Validates target domain and securely extracts verifiable claims.
          </span>
        </div>

        <button
          type="submit"
          disabled={isLoading || !url.trim()}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
        >
          <span>{isLoading ? 'Scanning Article Claims...' : 'Scan & Fact-Check Article'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {/* Preset Links */}
      <div className="pt-4 border-t border-slate-100">
        <span className="text-xs text-slate-600 font-semibold block mb-2">Try a sample verified link:</span>
        <div className="flex flex-wrap gap-2">
          {sampleUrls.map((s, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setUrl(s.url);
                setError(null);
              }}
              className="text-xs px-2.5 py-1.5 rounded-md bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors cursor-pointer"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
