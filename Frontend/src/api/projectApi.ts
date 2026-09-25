import { workspaceFetch } from './client';
import { ProjectRecord, ProjectCreatePayload, ProjectUpdatePayload, ProjectWorkspaceResponse } from '../types/project';

export const projectApi = {
  getProjects: async (limit: number = 50): Promise<ProjectRecord[]> => {
    return workspaceFetch(`/api/projects?limit=${limit}`);
  },

  getProject: async (projectId: string): Promise<ProjectRecord> => {
    return workspaceFetch(`/api/projects/${projectId}`);
  },

  createProject: async (payload: ProjectCreatePayload): Promise<ProjectRecord> => {
    return workspaceFetch('/api/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  updateProject: async (projectId: string, payload: ProjectUpdatePayload): Promise<ProjectRecord> => {
    return workspaceFetch(`/api/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  deleteProject: async (projectId: string): Promise<{ ok: boolean; deleted: string }> => {
    return workspaceFetch(`/api/projects/${projectId}`, {
      method: 'DELETE',
    });
  },

  getWorkspace: async (projectId: string): Promise<ProjectWorkspaceResponse> => {
    return workspaceFetch(`/api/projects/${projectId}/workspace`);
  },

  getOverview: async (projectId: string): Promise<{ ok: boolean; [key: string]: any }> => {
    return workspaceFetch(`/api/projects/${projectId}/overview`);
  },
};
