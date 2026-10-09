/**
 * BookLeaf Unified API Client
 * Centralizes request dispatching, authentication token propagation,
 * and robust URL normalization for local, Render, and Vercel environments.
 */

const resolveApiBaseUrl = (): string => {
  const envUrl = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '').trim();
  if (!envUrl) {
    return '/api/v1';
  }
  const clean = envUrl.replace(/\/+$/, '');
  // If the configured URL already ends with /api/v1, use it as is; otherwise append /api/v1
  return clean.endsWith('/api/v1') ? clean : `${clean}/api/v1`;
};

export const API_BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(message: string, code: string, status: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('bookleaf_token');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Remove leading slash from endpoint if present to concatenate cleanly
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorInfo = data.error || {};
    throw new ApiError(
      errorInfo.message || `Request failed with status ${response.status}`,
      errorInfo.code || 'UNKNOWN_ERROR',
      response.status,
      errorInfo.details
    );
  }

  return data;
}
