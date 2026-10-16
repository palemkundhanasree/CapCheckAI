export interface UserProfile {
  id: string;
  email: string;
  name: string;
  username: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export const authService = {
  getToken(): string | null {
    return localStorage.getItem('truthlens_token');
  },

  getUser(): UserProfile | null {
    const raw = localStorage.getItem('truthlens_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  setAuth(data: AuthResponse) {
    localStorage.setItem('truthlens_token', data.access_token);
    localStorage.setItem('truthlens_user', JSON.stringify(data.user));
    window.dispatchEvent(new Event('auth_state_changed'));
  },

  logout() {
    localStorage.removeItem('truthlens_token');
    localStorage.removeItem('truthlens_user');
    window.dispatchEvent(new Event('auth_state_changed'));
  },

  async login(identifier: string, password: string): Promise<AuthResponse> {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Invalid email/username or password');
    }

    const data: AuthResponse = await res.json();
    this.setAuth(data);
    return data;
  },

  async register(name: string, email: string, password: string, username?: string): Promise<AuthResponse> {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, username }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || 'Registration failed');
    }

    const data: AuthResponse = await res.json();
    this.setAuth(data);
    return data;
  },

  async requestLoginCode(email: string): Promise<{ message: string; email_delivery_configured: boolean; dev_otp?: string }> {
    const res = await fetch('/api/v1/auth/login-otp/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Could not send the sign-in code');
    }
    return await res.json();
  },

  async loginWithCode(email: string, otp: string): Promise<AuthResponse> {
    const res = await fetch('/api/v1/auth/login-otp/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Verification failed' }));
      throw new Error(err.detail || 'Invalid or expired code');
    }
    const data: AuthResponse = await res.json();
    this.setAuth(data);
    return data;
  },

  async forgotPassword(email: string): Promise<{ message: string; email_delivery_configured: boolean; dev_otp?: string }> {
    const res = await fetch('/api/v1/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Failed to send reset code');
    }

    return await res.json();
  },

  async verifyOtpAndReset(email: string, otp: string, new_password: string): Promise<{ message: string }> {
    const res = await fetch('/api/v1/auth/verify-otp-reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp, new_password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Verification failed' }));
      throw new Error(err.detail || 'Invalid or expired OTP code');
    }

    return await res.json();
  }
};
