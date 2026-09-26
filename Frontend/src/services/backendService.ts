/**
 * FastAPI client for the local JSON repository and filesystem storage.
 */

const BASE = (import.meta as unknown as { env?: Record<string, string | undefined> }).env
  ?.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

export const backendEnabled = true;

let _isBackendReachableCache: boolean | null = null;
let _lastCheckTime = 0;

export function getBackendUrl(): string {
  return BASE;
}

export async function checkBackendHealth(forceRefresh: boolean = false): Promise<boolean> {
  const now = Date.now();
  if (!forceRefresh && _isBackendReachableCache !== null && now - _lastCheckTime < 3000) {
    return _isBackendReachableCache;
  }
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${BASE}/health`, {
      method: 'GET',
      signal: controller.signal,
    }).catch(() => null);
    clearTimeout(timeoutId);
    _isBackendReachableCache = Boolean(res && res.ok);
    _lastCheckTime = Date.now();
    return _isBackendReachableCache;
  } catch {
    _isBackendReachableCache = false;
    _lastCheckTime = Date.now();
    return false;
  }
}

async function headers(): Promise<HeadersInit> {
  return {
    'Content-Type': 'application/json',
  };
}

async function uploadHeaders(): Promise<HeadersInit> {
  return {};
}

async function req(path: string, init?: RequestInit) {
  if (!BASE) throw new Error('VITE_BACKEND_URL is not set.');
  const h = await headers();
  try {
    const res = await fetch(`${BASE}${path}`, { ...init, headers: { ...h, ...(init?.headers || {}) } });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Backend ${res.status}: ${text || res.statusText}`);
    }
    _isBackendReachableCache = true;
    _lastCheckTime = Date.now();
    return res.json().catch(() => ({}));
  } catch (err) {
    _isBackendReachableCache = false;
    _lastCheckTime = Date.now();
    if (err instanceof Error && err.message.startsWith('Backend ')) {
      throw err;
    }
    throw new Error(`Backend server unavailable at ${BASE}`);
  }
}

async function uploadReq(path: string, file: File) {
  if (!BASE) throw new Error('VITE_BACKEND_URL is not set.');
  const h = await uploadHeaders();
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: h, body: form });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Backend ${res.status}: ${text || res.statusText}`);
    }
    _isBackendReachableCache = true;
    _lastCheckTime = Date.now();
    return res.json().catch(() => ({}));
  } catch (err) {
    _isBackendReachableCache = false;
    _lastCheckTime = Date.now();
    if (err instanceof Error && err.message.startsWith('Backend ')) {
      throw err;
    }
    throw new Error(`Backend server unavailable at ${BASE}`);
  }
}

export const backendApi = {
  listProjects: () => req('/api/projects'),
  getProject: (id: string) => req(`/api/projects/${id}`),
  createProject: (body: unknown) =>
    req('/api/projects', { method: 'POST', body: JSON.stringify(body) }),
  updateProject: (id: string, body: unknown) =>
    req(`/api/projects/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteProject: (id: string) => req(`/api/projects/${id}`, { method: 'DELETE' }),
  // Phase 9 dashboard bundle: project + sources + UCKR + deliverables + validations + jobs
  getOverview: (id: string) => req(`/api/projects/${id}/overview`),
  // Phase 2: file upload + sources
  uploadSource: (projectId: string, file: File) =>
    uploadReq(`/api/projects/${projectId}/upload`, file),
  listSources: (projectId: string) => req(`/api/projects/${projectId}/sources`),
  getSource: (sourceId: string) => req(`/api/sources/${sourceId}`),
  // Phase 3: AI Content Understanding (Qwen + Gemma)
  startPhase3Analysis: (projectId: string, sourceId: string, forceRefresh: boolean = false, extractedText?: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/analysis`, {
      method: 'POST',
      body: JSON.stringify({ forceRefresh, extractedText }),
    }),
  analyzeDocLink: (projectId: string, sourceId: string) =>
    req('/api/doclink/analyze', {
      method: 'POST',
      body: JSON.stringify({ document_id: sourceId, projectId, useLlm: true }),
    }),
  getPhase3Analysis: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/analysis`),
  getPhase3Status: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/analysis/status`),
  retryPhase3Analysis: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/analysis/retry`, { method: 'POST' }),

  // Phase 4: Real UCKR Engine
  buildUckr: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/uckr`, { method: 'POST' }),
  getSourceUckr: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/uckr`),
  getUckrValidation: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/uckr/validation`),
  rebuildUckr: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/uckr/rebuild`, { method: 'POST' }),
  getUckrVersion: (projectId: string, sourceId: string, version: number) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/uckr/${version}`),
  listUckrVersions: (projectId: string, sourceId?: string) =>
    req(`/api/projects/${projectId}/uckr/versions${sourceId ? `?sourceId=${sourceId}` : ''}`),

  // Phases 3-6: analyze -> UCKR -> transform -> validate
  analyzeSource: (projectId: string, sourceId: string) =>
    req(`/api/projects/${projectId}/sources/${sourceId}/uckr`, { method: 'POST' }),
  getUckr: (projectId: string, sourceId?: string) =>
    req(`/api/projects/${projectId}/uckr${sourceId ? `?sourceId=${sourceId}` : ''}`),
  transform: (projectId: string, types: string[], config?: Record<string, unknown>, sourceId?: string) =>
    req(`/api/projects/${projectId}/transform`, {
      method: 'POST',
      body: JSON.stringify({
        sourceId,
        outputTypes: types.map((type) => type === 'twitter' ? 'x' : type === 'video' ? 'video_script' : type),
        configuration: {
          audience: String(config?.audience || config?.targetAudience || 'executive').toLowerCase(),
          tone: String(config?.tone || 'professional').toLowerCase(),
          language: config?.language || 'English',
          detailLevel: String(config?.detailLevel || config?.levelOfDetail || 'medium').toLowerCase(),
          objective: String(config?.objective || 'awareness').toLowerCase().replace(/\s+/g, '_'),
        },
      }),
    }),
  listDeliverables: (projectId: string) => req(`/api/projects/${projectId}/deliverables`),
  validateProject: (projectId: string) =>
    req(`/api/projects/${projectId}/validate`, { method: 'POST' }),
  // Phase 7: background jobs
  startJob: (projectId: string, sourceId: string, outputs?: string[]) =>
    req(`/api/projects/${projectId}/jobs`, { method: 'POST', body: JSON.stringify({ sourceId, outputs }) }),
  getJob: (jobId: string) => req(`/api/jobs/${jobId}`),
  // Phase 10: exports (returns { storagePath, ... }; download via backend static or storage)
  exportDeliverable: (deliverableId: string, format: 'md' | 'json' | 'pptx' = 'md') =>
    req(`/api/deliverables/${deliverableId}/export?format=${format}`, { method: 'POST' }),
  // Phase 11: search own content
  search: (q: string, kind: 'all' | 'project' | 'source' = 'all') =>
    req(`/api/search?q=${encodeURIComponent(q)}&kind=${kind}`),
};
