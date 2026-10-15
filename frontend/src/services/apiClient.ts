const PRIMARY_API_URL = '/api/v1';
const FALLBACK_API_URL = 'http://127.0.0.1:8000/api/v1';

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

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = localStorage.getItem('capcheck_token');
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const executeFetch = async (baseUrl: string) => {
    const url = `${baseUrl}${endpoint}`;
    return fetch(url, {
      ...options,
      headers,
    });
  };

  let response: Response;
  try {
    response = await executeFetch(activeBaseUrl);
  } catch (netErr: any) {
    // If primary relative URL failed due to proxy drop, switch to direct backend port 8000
    if (activeBaseUrl === PRIMARY_API_URL) {
      try {
        response = await executeFetch(FALLBACK_API_URL);
        activeBaseUrl = FALLBACK_API_URL;
      } catch {
        throw new ApiError('Unable to connect to the CapCheck AI backend service. Please ensure run.bat is running.', 0);
      }
    } else {
      throw new ApiError('Network connection failed. Please check if the backend server is running.', 0);
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
