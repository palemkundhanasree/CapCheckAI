import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { authService } from '../services/authService';

// Pages
import { HomePage } from './routes/HomePage';
import { VerifyPage } from './routes/VerifyPage';
import { ResultsPage } from './routes/ResultsPage';
import { HistoryPage } from './routes/HistoryPage';
import { AboutPage } from './routes/AboutPage';
import { PrivacyPage } from './routes/PrivacyPage';
import { LoginPage } from './routes/LoginPage';
import { RegisterPage } from './routes/RegisterPage';
import { ForgotPasswordPage } from './routes/ForgotPasswordPage';
import { AdminPage } from './routes/AdminPage';

/** Shows a readable message (and a reload button) instead of a blank white page if a screen crashes. */
class ErrorBoundary extends React.Component<{ children: React.ReactNode; resetKey: string }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidUpdate(prev: { resetKey: string }) {
    // Moving to another page clears the error so navigation always works
    if (this.state.error && prev.resetKey !== this.props.resetKey) this.setState({ error: null });
  }
  render() {
    if (this.state.error) {
      return (
        <div className="max-w-xl mx-auto px-4 py-20 text-center space-y-3">
          <h2 className="text-lg font-semibold text-slate-900">Something went wrong on this page</h2>
          <p className="text-xs text-slate-600">{this.state.error.message}</p>
          <button className="px-4 py-2 rounded-lg bg-slate-900 text-white text-xs" onClick={() => window.location.assign('/')}>
            Back to home
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const RoutedBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  return <ErrorBoundary resetKey={location.pathname + location.search}>{children}</ErrorBoundary>;
};

function useSignedIn(): boolean {
  const [signedIn, setSignedIn] = useState<boolean>(!!authService.getToken());
  useEffect(() => {
    const sync = () => setSignedIn(!!authService.getToken());
    window.addEventListener('auth_state_changed', sync);
    return () => window.removeEventListener('auth_state_changed', sync);
  }, []);
  return signedIn;
}

/** The whole product is members-only: anonymous visitors are sent to the sign-in page. */
const RequireAuth: React.FC = () => {
  const signedIn = useSignedIn();
  const location = useLocation();
  if (!signedIn) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return <Outlet />;
};

const GuestOnly: React.FC = () => {
  const signedIn = useSignedIn();
  if (signedIn) return <Navigate to="/" replace />;
  return <Outlet />;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="flex flex-col min-h-screen bg-paper text-slate-900">
        <Navbar />
        <main className="flex-1">
          <RoutedBoundary>
          <Routes>
            <Route element={<GuestOnly />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            </Route>
            <Route element={<RequireAuth />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/verify" element={<VerifyPage />} />
              <Route path="/results/:id" element={<ResultsPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </RoutedBoundary>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
};

export default App;
