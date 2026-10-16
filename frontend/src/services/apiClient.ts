const PRIMARY_API_URL = '/api/v1';
const FALLBACK_API_URL = 'http://127.0.0.1:8000/api/v1';
const TOKEN_KEY = 'truthlens_token';

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

let activeBaseUrl = PRIMARY_API_URL;

function clearSessionAndRedirect() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('truthlens_user');
  window.dispatchEvent(new Event('auth_state_changed'));
}

async function send(endpoint: string, options: RequestInit): Promise<Response> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }
  const token = localStorage.getItem(TOKEN_KEY);
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const run = (base: string) => fetch(`${base}${endpoint}`, { ...options, headers });

  let response: Response;
  try {
    response = await run(activeBaseUrl);
  } catch {
    if (activeBaseUrl === PRIMARY_API_URL) {
      try {
        response = await run(FALLBACK_API_URL);
        activeBaseUrl = FALLBACK_API_URL;
      } catch {
        throw new ApiError('Cannot reach the CapCheck AI server. Make sure the backend is running, then try again.', 0);
      }
    } else {
      throw new ApiError('Network connection failed. Check that the backend server is running.', 0);
    }
  }

  if (!response.ok) {
    let detail = `Request failed (HTTP ${response.status})`;
    try {
      const j = await response.json();
      if (j && j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      // ignore body parse errors
    }
    if (response.status === 401 && token) {
      clearSessionAndRedirect();
      detail = 'Your session has expired. Please sign in again.';
    }
    throw new ApiError(detail, response.status);
  }
  return response;
}

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await send(endpoint, options);
  return response.json() as Promise<T>;
}

/** Fetches a protected file (uploaded media, PDF report) with the sign-in token. */
export async function requestBlob(endpoint: string): Promise<Blob> {
  const response = await send(endpoint, {});
  return response.blob();
}
