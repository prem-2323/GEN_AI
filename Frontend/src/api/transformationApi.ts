import { authenticatedFetch } from './client';
import { DeliverablesState, DeliverableRecord, OutputType } from '../types/deliverable';

export interface TransformRequestPayload {
  types?: OutputType[] | string[];
  outputTypes?: OutputType[] | string[];
  sourceId?: string;
  uckrVersion?: number;
  config?: any;
  configuration?: any;
}

export const transformationApi = {
  transform: async (
    projectId: string,
    payload: TransformRequestPayload
  ): Promise<{ ok: boolean; projectId: string; deliverables: DeliverableRecord[]; count: number }> => {
    return authenticatedFetch(`/api/projects/${projectId}/transform`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listDeliverables: async (
    projectId: string
  ): Promise<{ ok: boolean; deliverables: DeliverableRecord[]; count: number }> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables`);
  },

  getDeliverable: async (
    projectId: string,
    deliverableId: string
  ): Promise<{ ok: boolean; deliverable: DeliverableRecord }> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables/${deliverableId}`);
  },

  deleteDeliverable: async (
    projectId: string,
    deliverableId: string
  ): Promise<{ ok: boolean; deleted: string }> => {
    return authenticatedFetch(`/api/projects/${projectId}/deliverables/${deliverableId}`, {
      method: 'DELETE',
    });
  },
};
