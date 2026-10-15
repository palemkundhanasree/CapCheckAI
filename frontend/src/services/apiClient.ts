export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Resolves the active backend API v1 base URL.
 * Automatically checks environment variables for production deployments (Netlify, Next/Vite).
 * Supports: VITE_API_URL, NEXT_PUBLIC_API_URL, VITE_API_BASE_URL
 */
export const getBaseApiUrl = (): string => {
  // Support Vite and Next.js style client env variables
  const metaEnv: Record<string, string | undefined> = 
    (typeof import.meta !== 'undefined' && (import.meta as any).env) || {};
  const procEnv: Record<string, string | undefined> = 
    (typeof globalThis !== 'undefined' && (globalThis as any).process?.env) || {};

  const envUrl =
    metaEnv.VITE_API_URL ||
    metaEnv.NEXT_PUBLIC_API_URL ||
    metaEnv.VITE_API_BASE_URL ||
    procEnv.VITE_API_URL ||
    procEnv.NEXT_PUBLIC_API_URL ||
    procEnv.VITE_API_BASE_URL;

  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    const trimmed = envUrl.trim().replace(/\/+$/, '');
    if (trimmed.endsWith('/api/v1')) return trimmed;
    if (trimmed.endsWith('/api')) return `${trimmed}/v1`;
    return `${trimmed}/api/v1`;
  }

  // Relative path defaults to proxy or Netlify rewrite rule
  return '/api/v1';
};

/**
 * Resolves full media URL (for images, audio, video, PDF) for both local and decoupled production backends.
 */
export const resolveMediaUrl = (path?: string): string => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('blob:') || path.startsWith('data:')) {
    return path;
  }
  const base = getBaseApiUrl();
  if (base.startsWith('http://') || base.startsWith('https://')) {
    const origin = base.replace(/\/api\/v1\/?$/, '');
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${origin}${cleanPath}`;
  }
  return path.startsWith('/') ? path : `/${path}`;
};

const PRIMARY_API_URL = getBaseApiUrl();
const LOCAL_FALLBACK_URL = 'http://127.0.0.1:8000/api/v1';

let activeBaseUrl = PRIMARY_API_URL;

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = localStorage.getItem('capcheck_token') || localStorage.getItem('truthlens_token');
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const executeFetch = async (baseUrl: string) => {
    let cleanEndpoint = endpoint;
    if (cleanEndpoint.startsWith('/api/v1/')) {
      cleanEndpoint = cleanEndpoint.substring(7);
    } else if (!cleanEndpoint.startsWith('/')) {
      cleanEndpoint = `/${cleanEndpoint}`;
    }
    const url = `${baseUrl}${cleanEndpoint}`;
    return fetch(url, {
      ...options,
      headers,
    });
  };

  let response: Response;
  try {
    response = await executeFetch(activeBaseUrl);
  } catch (netErr: any) {
    // If running locally and relative proxy failed, attempt direct port 8000 fallback
    const isLocalhost = typeof window !== 'undefined' && (
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1'
    );

    if (isLocalhost && activeBaseUrl === PRIMARY_API_URL && activeBaseUrl !== LOCAL_FALLBACK_URL) {
      try {
        response = await executeFetch(LOCAL_FALLBACK_URL);
        activeBaseUrl = LOCAL_FALLBACK_URL;
      } catch {
        throw new ApiError('Unable to connect to local CapCheck AI backend on port 8000. Please ensure run.bat is running.', 0);
      }
    } else {
      throw new ApiError('Unable to reach CapCheck AI backend API. Please verify network or VITE_API_URL / NEXT_PUBLIC_API_URL environment configuration.', 0);
    }
  }

  if (!response.ok) {
    let errorDetail = `Request failed (HTTP ${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json() as Promise<T>;
}

