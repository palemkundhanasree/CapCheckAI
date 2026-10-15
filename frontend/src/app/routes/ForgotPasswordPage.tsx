import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { KeyRound, Mail, Lock, ShieldCheck, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { authService } from '../../services/authService';

export const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<'request_otp' | 'verify_otp'>('request_otp');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [devOtpHint, setDevOtpHint] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const resp = await authService.forgotPassword(email);
      setSuccessMsg(resp.message || 'OTP reset code has been sent to your email.');
      if (resp.dev_otp) {
        setDevOtpHint(resp.dev_otp);
        setOtp(resp.dev_otp);
      }
      setStep('verify_otp');
    } catch (err: any) {
      setError(err.message || 'Could not process request. Please check email address.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtpAndReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      setLoading(false);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      setLoading(false);
      return;
    }

    try {
      await authService.verifyOtpAndReset(email, otp.trim(), newPassword);
      setSuccessMsg('Password reset successful! Logging you in...');
      // Automatically log the user in with new credentials
      setTimeout(async () => {
        try {
          await authService.login(email, newPassword);
          navigate('/');
        } catch {
          navigate('/login');
        }
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please check the OTP code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 sm:p-10 rounded-xl border border-slate-200 shadow-sm">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-amber-50 text-amber-700 mb-4 border border-amber-100">
            <KeyRound className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
            {step === 'request_otp' ? 'Forgot Password' : 'Verify OTP & Reset'}
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            {step === 'request_otp'
              ? 'Enter your registered email address and we will send you a 6-digit one-time verification passcode (OTP).'
              : `Enter the 6-digit code sent to ${email} and choose a new password.`}
          </p>
        </div>

        {error && (
          <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-3.5 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm flex items-start space-x-2.5">
            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-600" />
            <span>{successMsg}</span>
          </div>
        )}

        {devOtpHint && (
          <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-800">
            <span className="font-semibold">Local Dev OTP Detected:</span> <code className="bg-blue-100 px-1.5 py-0.5 rounded font-mono font-bold text-blue-900">{devOtpHint}</code> (also logged in backend storage/email_outbox.log)
          </div>
        )}

        {step === 'request_otp' ? (
          <form className="mt-6 space-y-4" onSubmit={handleRequestOtp}>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Your Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@truthlens.ai or your email"
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loading ? 'Sending OTP Code...' : 'Send Verification OTP'}
              <ArrowRight className="ml-2 w-4 h-4" />
            </button>
          </form>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleVerifyOtpAndReset}>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                6-Digit OTP Code
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <ShieldCheck className="h-4 w-4" />
                </div>
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="123456"
                  className="block w-full pl-9 pr-3 py-2 text-sm font-mono tracking-widest border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                New Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="New password (min 6 characters)"
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Confirm New Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat new password"
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loading ? 'Verifying & Resetting...' : 'Verify OTP & Reset Password'}
              <ArrowRight className="ml-2 w-4 h-4" />
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => setStep('request_otp')}
                className="text-xs text-slate-500 hover:text-slate-700 underline cursor-pointer"
              >
                Resend OTP code
              </button>
            </div>
          </form>
        )}

        <div className="pt-4 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-600">
            Remembered your password?{' '}
            <Link to="/login" className="font-medium text-blue-600 hover:text-blue-700">
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
