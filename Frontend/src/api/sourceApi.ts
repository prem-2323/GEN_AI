import { workspaceFetch, workspaceUpload } from './client';
import { SourceFile, SourceUploadResponse, SourceListResponse } from '../types/source';

export const sourceApi = {
  uploadSource: async (projectId: string, file: File): Promise<SourceUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    return workspaceUpload(`/api/projects/${projectId}/upload`, formData);
  },

  createSourceDirect: async (projectId: string, payload: Partial<SourceFile>): Promise<SourceFile> => {
    return workspaceFetch(`/api/projects/${projectId}/sources`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getSources: async (projectId: string): Promise<SourceListResponse> => {
    return workspaceFetch(`/api/projects/${projectId}/sources`);
  },

  getSource: async (sourceId: string): Promise<SourceFile> => {
    return workspaceFetch(`/api/sources/${sourceId}`);
  },

  getSourceInProject: async (projectId: string, sourceId: string): Promise<SourceFile> => {
    return workspaceFetch(`/api/projects/${projectId}/sources/${sourceId}`);
  },

  deleteSource: async (sourceId: string): Promise<{ ok: boolean; deleted: string }> => {
    return workspaceFetch(`/api/sources/${sourceId}`, {
      method: 'DELETE',
    });
  },
};
