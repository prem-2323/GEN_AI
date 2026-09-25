import { authenticatedFetch } from './client';
import { JobRecord } from '../types/job';

export interface StartJobPayload {
  sourceId: string;
  type?: string;
  outputs?: string[];
  config?: any;
}

export const jobApi = {
  startJob: async (
    projectId: string,
    payload: StartJobPayload
  ): Promise<{ ok: boolean; job: JobRecord }> => {
    return authenticatedFetch(`/api/projects/${projectId}/jobs`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getJob: async (jobId: string): Promise<{ ok: boolean; job: JobRecord }> => {
    return authenticatedFetch(`/api/jobs/${jobId}`);
  },

  listJobs: async (projectId: string): Promise<{ ok: boolean; jobs: JobRecord[] }> => {
    return authenticatedFetch(`/api/projects/${projectId}/jobs`);
  },
};
