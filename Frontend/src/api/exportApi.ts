import { authenticatedFetch, getApiBaseUrl } from './client';
import { ExportRecord, ExportRequestPayload } from '../types/export';
import { auth } from '../lib/firebase';

export const exportApi = {
  exportDeliverable: async (
    projectId: string,
    deliverableId: string,
    payload: ExportRequestPayload
  ): Promise<{ ok: boolean; export: ExportRecord }> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables/${deliverableId}/export`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listExports: async (
    projectId: string
  ): Promise<{ ok: boolean; exports: ExportRecord[]; count: number }> => {
    return authenticatedFetch(`/api/projects/${projectId}/exports`);
  },

  getExport: async (
    projectId: string,
    exportId: string
  ): Promise<{ ok: boolean; export: ExportRecord }> => {
    return authenticatedFetch(`/api/projects/${projectId}/exports/${exportId}`);
  },

  downloadExportBlob: async (
    projectId: string,
    exportId: string
  ): Promise<{ blob: Blob; filename: string }> => {
    const user = auth.currentUser;
    const token = user ? await user.getIdToken().catch(() => '') : '';
    const uid = user?.uid || 'guest-user';
    const baseUrl = getApiBaseUrl();

    const headers: HeadersInit = {
      'X-User-Uid': uid,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${baseUrl}/api/projects/${projectId}/exports/${exportId}/download`, {
      headers,
    });

    if (!res.ok) {
      throw new Error(`Download failed with status ${res.status}`);
    }

    let filename = 'export.bin';
    const disposition = res.headers.get('content-disposition');
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) filename = match[1];
    }

    const blob = await res.blob();
    return { blob, filename };
  },

  downloadFileBlob: async (
    projectId: string,
    fileId: string
  ): Promise<{ blob: Blob; filename: string }> => {
    const user = auth.currentUser;
    const token = user ? await user.getIdToken().catch(() => '') : '';
    const uid = user?.uid || 'guest-user';
    const baseUrl = getApiBaseUrl();

    const headers: HeadersInit = {
      'X-User-Uid': uid,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${baseUrl}/api/projects/${projectId}/files/${fileId}/download`, {
      headers,
    });

    if (!res.ok) {
      throw new Error(`Download failed with status ${res.status}`);
    }

    let filename = 'download.bin';
    const disposition = res.headers.get('content-disposition');
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) filename = match[1];
    }

    const blob = await res.blob();
    return { blob, filename };
  },
};
