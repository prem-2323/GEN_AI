import { authenticatedFetch } from './client';
import { ConsistencyValidationReport, DeliverableValidationResult } from '../types/validation';

export const validationApi = {
  validateSource: async (
    projectId: string,
    sourceId: string,
    payload?: any
  ): Promise<ConsistencyValidationReport> => {
    return authenticatedFetch(`/api/projects/${projectId}/sources/${sourceId}/validate`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  },

  getSourceValidation: async (
    projectId: string,
    sourceId: string
  ): Promise<ConsistencyValidationReport> => {
    return authenticatedFetch(`/api/projects/${projectId}/sources/${sourceId}/validation`);
  },

  validateDeliverable: async (
    projectId: string,
    deliverableId: string
  ): Promise<{ ok: boolean; result: DeliverableValidationResult }> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables/${deliverableId}/validate`, {
      method: 'POST',
    });
  },

  regenerateDeliverable: async (
    projectId: string,
    deliverableId: string,
    payload?: any
  ): Promise<any> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables/${deliverableId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  },

  validateProject: async (
    projectId: string
  ): Promise<{ ok: boolean; validation: any }> => {
    return authenticatedFetch(`/api/projects/${projectId}/validate`, {
      method: 'POST',
    });
  },
};
