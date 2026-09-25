import { authenticatedFetch } from './client';
import { DeliverableQualityReport } from '../types/quality';

export const qualityApi = {
  approveDeliverable: async (
    projectId: string,
    deliverableId: string
  ): Promise<{ ok: boolean; deliverable: any; message?: string }> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables/${deliverableId}/approve`, {
      method: 'POST',
    });
  },

  getQualityReport: async (
    projectId: string,
    deliverableId: string
  ): Promise<DeliverableQualityReport> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables/${deliverableId}/quality`);
  },
};
