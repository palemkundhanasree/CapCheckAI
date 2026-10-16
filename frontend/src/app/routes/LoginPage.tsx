import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Mail, Lock, ArrowRight, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { authService } from '../../services/authService';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authService.isAuthenticated()) {
      navigate('/');
      return;
    }
    // Load remembered identifier if user previously opted into Remember Me
    const remembered = localStorage.getItem('capcheck_remembered_identifier');
    if (remembered) {
      setIdentifier(remembered);
      setRememberMe(true);
    }
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const cleanId = identifier.trim();
    if (!cleanId) {
      setError('Please enter your email or username.');
      setLoading(false);
      return;
    }

    try {
      await authService.login(cleanId, password);

      // Handle Remember Me preference
      if (rememberMe) {
        localStorage.setItem('capcheck_remembered_identifier', cleanId);
      } else {
        localStorage.removeItem('capcheck_remembered_identifier');
      }

      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-xl border border-slate-200 shadow-sm">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-50 text-blue-700 mb-3 border border-blue-100">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Sign in to CapCheck AI</h2>
          <p className="mt-1.5 text-xs text-slate-600">
            Enter your credentials to access the verification platform
          </p>
          <div className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            Strict ≥75% Source Verification Standard
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        <form className="space-y-4" onSubmit={handleLogin} method="POST">
          <div>
            <label htmlFor="login-identifier" className="block text-xs font-medium text-slate-700 mb-1">
              Email or Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail className="h-4 w-4" />
              </div>
              <input
                id="login-identifier"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="name@example.com or username"
                className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="login-password" className="block text-xs font-medium text-slate-700">
                Password
              </label>
              <Link
                to="/forgot-password"
                className="text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="h-4 w-4" />
              </div>
              <input
                id="login-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="block w-full pl-9 pr-10 py-2 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center space-x-2 text-xs text-slate-600 cursor-pointer select-none">
              <input
                type="checkbox"
                name="remember"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5"
              />
              <span>Remember my username</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {loading ? 'Signing in...' : 'Sign In'}
            <ArrowRight className="ml-2 w-4 h-4" />
          </button>
        </form>

        <div className="pt-3 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-600">
            Don't have an account?{' '}
            <Link to="/register" className="font-semibold text-blue-600 hover:text-blue-700">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
