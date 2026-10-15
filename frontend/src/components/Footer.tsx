import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, ExternalLink } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-20 text-slate-600 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2 space-y-3">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
                <Shield className="w-4 h-4" />
              </div>
              <span className="text-lg font-bold text-slate-900 tracking-tight">
                CapCheck <span className="text-blue-600">AI</span>
              </span>
            </div>
            <p className="text-slate-600 max-w-md text-xs leading-relaxed">
              An AI-powered verification platform providing clear factual analysis and deepfake detection for claims, articles, images, and videos.
            </p>
            <div className="flex items-center space-x-2 text-xs text-slate-500 pt-1">
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span>
                <span className="font-medium text-slate-700">Forensics Engine Online</span>
              </span>
              <span>•</span>
              <span>Cross-Referenced Evidence</span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900">Platform</h4>
            <ul className="mt-3 space-y-2 text-xs">
              <li><Link to="/verify" className="text-slate-600 hover:text-blue-600 transition-colors">Verify News & Media</Link></li>
              <li><Link to="/history" className="text-slate-600 hover:text-blue-600 transition-colors">Verification History</Link></li>
              <li><Link to="/about" className="text-slate-600 hover:text-blue-600 transition-colors">How It Works</Link></li>
              <li><Link to="/privacy" className="text-slate-600 hover:text-blue-600 transition-colors">Privacy & Security</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900">Authoritative Standards</h4>
            <ul className="mt-3 space-y-2 text-xs">
              <li>
                <a href="https://www.ifcncodeofprinciples.poynter.org/" target="_blank" rel="noreferrer" className="flex items-center space-x-1 text-slate-600 hover:text-blue-600 transition-colors">
                  <span>IFCN Code of Principles</span>
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
              <li>
                <a href="https://c2pa.org/" target="_blank" rel="noreferrer" className="flex items-center space-x-1 text-slate-600 hover:text-blue-600 transition-colors">
                  <span>C2PA Content Credentials</span>
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
              <li>
                <a href="https://toolbox.google.com/factcheck/explorer" target="_blank" rel="noreferrer" className="flex items-center space-x-1 text-slate-600 hover:text-blue-600 transition-colors">
                  <span>Google Fact Check Tools</span>
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <p>© {new Date().getFullYear()} CapCheck AI. All rights reserved.</p>
          <p className="mt-2 sm:mt-0">
            Know What to Trust • Objective Evidence • Transparent Forensics
          </p>
        </div>
      </div>
    </footer>
  );
};
