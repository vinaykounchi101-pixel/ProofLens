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
      if (parsed.error) {
        errorData = parsed;
      } else if (parsed.detail) {
        errorData = {
          error: {
            code: 'API_ERROR',
            message: typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail),
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
