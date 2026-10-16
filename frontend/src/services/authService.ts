import { request } from './apiClient';

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
    return localStorage.getItem('capcheck_token') || localStorage.getItem('truthlens_token');
  },

  getUser(): UserProfile | null {
    const raw = localStorage.getItem('capcheck_user') || localStorage.getItem('truthlens_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  setAuth(data: AuthResponse) {
    localStorage.setItem('capcheck_token', data.access_token);
    localStorage.setItem('capcheck_user', JSON.stringify(data.user));
    window.dispatchEvent(new Event('auth_state_changed'));
  },

  logout() {
    localStorage.removeItem('capcheck_token');
    localStorage.removeItem('capcheck_user');
    localStorage.removeItem('truthlens_token');
    localStorage.removeItem('truthlens_user');
    window.dispatchEvent(new Event('auth_state_changed'));
  },

  async login(identifier: string, password: string): Promise<AuthResponse> {
    const data = await request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: identifier, identifier, password }),
    });
    this.setAuth(data);
    return data;
  },

  async register(name: string, email: string, password: string, username?: string): Promise<AuthResponse> {
    const data = await request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password, username }),
    });
    this.setAuth(data);
    return data;
  },

  async forgotPassword(email: string): Promise<{ message: string; dev_otp?: string }> {
    return await request<{ message: string; dev_otp?: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  async verifyOtpAndReset(email: string, otp: string, new_password: string): Promise<{ message: string }> {
    return await request<{ message: string }>('/auth/verify-otp-reset', {
      method: 'POST',
      body: JSON.stringify({ email, otp, new_password }),
    });
  },

  async getCurrentUserProfile(): Promise<UserProfile | null> {
    const token = this.getToken();
    if (!token) return null;
    try {
      const user = await request<UserProfile>('/auth/me');
      localStorage.setItem('capcheck_user', JSON.stringify(user));
      return user;
    } catch {
      return null;
    }
  }
};

