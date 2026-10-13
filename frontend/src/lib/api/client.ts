import { ApiError } from '../types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class FetchError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'FetchError';
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData: ApiError = {
      error: {
        code: 'NETWORK_ERROR',
        message: `HTTP ${response.status} error`,
      },
    };

    try {
      const parsed = await response.json();
      if (parsed.error && parsed.error.message) {
        errorData = parsed;
      } else if (parsed.message) {
        errorData = {
          error: {
            code: parsed.error_code || 'API_ERROR',
            message: parsed.message,
            details: parsed.details,
          },
        };
      } else if (parsed.detail) {
        const detailMsg = Array.isArray(parsed.detail)
          ? parsed.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
          : typeof parsed.detail === 'string'
          ? parsed.detail
          : JSON.stringify(parsed.detail);
        errorData = {
          error: {
            code: 'API_ERROR',
            message: detailMsg,
          },
        };
      }
    } catch {
      // Use fallback errorData
    }

    throw new FetchError(
      response.status,
      errorData.error.code,
      errorData.error.message,
      errorData.error.details
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
