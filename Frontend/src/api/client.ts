export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export function getApiBaseUrl(): string {
  const env = (import.meta as unknown as { env?: Record<string, string | undefined> }).env;
  return (
    env?.VITE_BACKEND_URL ||
    env?.VITE_API_URL ||
    'http://127.0.0.1:8000'
  ).replace(/\/+$/, '');
}

/**
 * Standard unauthenticated fetch helper
 */
export async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `API error: ${response.status} ${response.statusText}`;
    let errorData: any = null;
    try {
      errorData = await response.json();
      if (errorData?.detail) {
        errorDetail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData?.message) {
        errorDetail = errorData.message;
      }
    } catch {
      // Non-json response
    }
    throw new ApiError(response.status, errorDetail, errorData);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

/**
 * Send API requests under the local, anonymous workspace identity.
 */
export async function workspaceFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `API error: ${response.status} ${response.statusText}`;
    let errorData: any = null;
    try {
      errorData = await response.json();
      if (errorData?.detail) {
        errorDetail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData?.message) {
        errorDetail = errorData.message;
      }
    } catch {
      // Non-json response
    }
    throw new ApiError(response.status, errorDetail, errorData);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

/**
 * Upload FormData files under the local workspace identity.
 */
export async function workspaceUpload<T = any>(
  path: string,
  formData: FormData,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  // Do NOT set Content-Type header so browser calculates multipart boundary

  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...options,
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Upload error: ${response.status} ${response.statusText}`;
    let errorData: any = null;
    try {
      errorData = await response.json();
      if (errorData?.detail) {
        errorDetail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Non-json response
    }
    throw new ApiError(response.status, errorDetail, errorData);
  }

  return (await response.json()) as T;
}
