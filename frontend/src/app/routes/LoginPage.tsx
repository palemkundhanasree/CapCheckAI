import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { ShieldCheck, Mail, Lock, ArrowRight, AlertCircle, CheckCircle2, KeyRound } from 'lucide-react';
import { authService } from '../../services/authService';

type Mode = 'password' | 'code';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = (location.state as { from?: string } | null)?.from || '/';

  const [mode, setMode] = useState<Mode>('password');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const switchMode = (m: Mode) => {
    setMode(m);
    setError(null);
    setNotice(null);
    setCodeSent(false);
    setCode('');
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authService.login(identifier, password);
      navigate(redirectTo, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Sign in failed. Please check your details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const resp = await authService.requestLoginCode(identifier.trim());
      setCodeSent(true);
      setNotice(
        resp.email_delivery_configured === false
          ? 'Email delivery is not set up on this server yet, so no email was sent. The administrator must add SMTP settings to the .env file.'
          : resp.message
      );
      if (resp.dev_otp) setCode(resp.dev_otp);
    } catch (err: any) {
      setError(err.message || 'Could not send the code.');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authService.loginWithCode(identifier.trim(), code.trim());
      navigate(redirectTo, { replace: true });
    } catch (err: any) {
      setError(err.message || 'That code did not work.');
    } finally {
      setLoading(false);
    }
  };

  const inputCls =
    'block w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-md bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:border-blue-600';

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full space-y-6 bg-white p-8 rounded-lg border border-slate-200 shadow-sm">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-blue-50 text-blue-700 mb-3 border border-blue-100">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Sign in to CapCheck AI</h1>
          <p className="mt-1.5 text-sm text-slate-600">You need an account to verify claims, images and videos.</p>
        </div>

        <div className="grid grid-cols-2 gap-1 p-1 bg-slate-100 rounded-md text-sm">
          {(['password', 'code'] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => switchMode(m)}
              className={`py-1.5 rounded font-medium cursor-pointer ${
                mode === m ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {m === 'password' ? 'Password' : 'Email code'}
            </button>
          ))}
        </div>

        {error && (
          <div role="alert" className="p-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {notice && (
          <div className="p-3 rounded-md bg-green-50 border border-green-200 text-green-800 text-sm flex items-start space-x-2">
            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{notice}</span>
          </div>
        )}

        {mode === 'password' ? (
          <form className="space-y-4" onSubmit={handlePasswordLogin}>
            <div>
              <label htmlFor="identifier" className="block text-sm font-medium text-slate-700 mb-1">Email or username</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input id="identifier" type="text" required autoComplete="username" value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)} placeholder="name@example.com" className={inputCls} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="password" className="block text-sm font-medium text-slate-700">Password</label>
                <Link to="/forgot-password" className="text-xs font-medium text-blue-600 hover:text-blue-700">Forgot password?</Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input id="password" type="password" required autoComplete="current-password" value={password}
                  onChange={(e) => setPassword(e.target.value)} className={inputCls} />
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 cursor-pointer">
              {loading ? 'Signing in...' : 'Sign in'}
              <ArrowRight className="ml-2 w-4 h-4" />
            </button>
          </form>
        ) : !codeSent ? (
          <form className="space-y-4" onSubmit={handleSendCode}>
            <div>
              <label htmlFor="code-email" className="block text-sm font-medium text-slate-700 mb-1">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input id="code-email" type="email" required value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)} placeholder="name@example.com" className={inputCls} />
              </div>
              <p className="mt-1.5 text-xs text-slate-500">We will email you a 6-digit code. No password needed.</p>
            </div>
            <button type="submit" disabled={loading}
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 cursor-pointer">
              {loading ? 'Sending...' : 'Email me a code'}
              <ArrowRight className="ml-2 w-4 h-4" />
            </button>
          </form>
        ) : (
          <form className="space-y-4" onSubmit={handleCodeLogin}>
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-slate-700 mb-1">6-digit code sent to {identifier}</label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input id="otp" type="text" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} required autoComplete="one-time-code"
                  value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                  className={inputCls + ' tracking-[0.4em] font-mono'} placeholder="••••••" />
              </div>
            </div>
            <button type="submit" disabled={loading || code.length !== 6}
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 cursor-pointer">
              {loading ? 'Checking...' : 'Sign in'}
              <ArrowRight className="ml-2 w-4 h-4" />
            </button>
            <button type="button" onClick={() => { setCodeSent(false); setCode(''); setNotice(null); }}
              className="w-full text-xs text-slate-600 hover:text-slate-900 cursor-pointer">
              Use a different email or send a new code
            </button>
          </form>
        )}

        <p className="pt-4 border-t border-slate-100 text-center text-sm text-slate-600">
          New to CapCheck AI?{' '}
          <Link to="/register" className="font-medium text-blue-600 hover:text-blue-700">Create an account</Link>
        </p>
      </div>
    </div>
  );
};
