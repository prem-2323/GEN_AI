import { workspaceFetch } from './client';
import { UckrKnowledgeBase, UckrVersionSummary } from '../types/uckr';

export const uckrApi = {
  buildUckr: async (
    projectId: string,
    sourceId: string
  ): Promise<{ ok: boolean; uckrId: string; version: number; status: string; statistics: any; uckr: UckrKnowledgeBase }> => {
    return workspaceFetch(`/api/projects/${projectId}/sources/${sourceId}/uckr`, {
      method: 'POST',
    });
  },

  getSourceUckr: async (
    projectId: string,
    sourceId: string
  ): Promise<{ ok: boolean; uckr: UckrKnowledgeBase }> => {
    return workspaceFetch(`/api/projects/${projectId}/sources/${sourceId}/uckr`);
  },

  getProjectUckr: async (
    projectId: string,
    sourceId?: string
  ): Promise<{ ok: boolean; uckr: UckrKnowledgeBase }> => {
    const query = sourceId ? `?sourceId=${encodeURIComponent(sourceId)}` : '';
    return workspaceFetch(`/api/projects/${projectId}/uckr${query}`);
  },

  rebuildUckr: async (
    projectId: string,
    sourceId: string
  ): Promise<{ ok: boolean; uckrId: string; version: number; status: string; statistics: any; uckr: UckrKnowledgeBase }> => {
    return workspaceFetch(`/api/projects/${projectId}/sources/${sourceId}/uckr/rebuild`, {
      method: 'POST',
    });
  },

  getUckrVersion: async (
    projectId: string,
    sourceId: string,
    version: number
  ): Promise<{ ok: boolean; uckr: UckrKnowledgeBase }> => {
    return workspaceFetch(`/api/projects/${projectId}/sources/${sourceId}/uckr/${version}`);
  },

  listUckrVersions: async (
    projectId: string,
    sourceId?: string
  ): Promise<{ ok: boolean; versions: UckrVersionSummary[] }> => {
    const query = sourceId ? `?sourceId=${encodeURIComponent(sourceId)}` : '';
    return workspaceFetch(`/api/projects/${projectId}/uckr/versions${query}`);
  },

  getUckrValidation: async (
    projectId: string,
    sourceId: string
  ): Promise<{ ok: boolean; validation: any }> => {
    return workspaceFetch(`/api/projects/${projectId}/sources/${sourceId}/uckr/validation`);
  },
};
