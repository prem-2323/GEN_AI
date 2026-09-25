import { workspaceFetch } from './client';
import { DeliverablesState, DeliverableRecord, OutputType } from '../types/deliverable';

export interface TransformRequestPayload {
  types?: OutputType[] | string[];
  outputTypes?: OutputType[] | string[];
  sourceId?: string;
  uckrVersion?: number;
  config?: any;
  configuration?: any;
}

function normalizeTransformPayload(payload: TransformRequestPayload) {
  const requestedTypes = payload.outputTypes || payload.types || ['linkedin'];
  const outputTypes = requestedTypes.map((type) => {
    if (type === 'twitter') return 'x';
    if (type === 'video') return 'video_script';
    return type;
  });
  const config = payload.configuration || payload.config || {};

  return {
    sourceId: payload.sourceId,
    uckrVersion: payload.uckrVersion,
    outputTypes,
    configuration: {
      audience: String(config.audience || config.targetAudience || 'executive').toLowerCase(),
      tone: String(config.tone || 'professional').toLowerCase(),
      language: config.language || 'English',
      detailLevel: String(config.detailLevel || config.levelOfDetail || 'medium').toLowerCase(),
      objective: String(config.objective || 'awareness').toLowerCase().replace(/\s+/g, '_'),
    },
  };
}

export const transformationApi = {
  transform: async (
    projectId: string,
    payload: TransformRequestPayload
  ): Promise<{ ok: boolean; projectId: string; deliverables: DeliverableRecord[]; count: number }> => {
    return workspaceFetch(`/api/projects/${projectId}/transform`, {
      method: 'POST',
      body: JSON.stringify(normalizeTransformPayload(payload)),
    });
  },

  listDeliverables: async (
    projectId: string
  ): Promise<{ ok: boolean; deliverables: DeliverableRecord[]; count: number }> => {
    return workspaceFetch(`/api/projects/${projectId}/deliverables`);
  },

  getDeliverable: async (
    projectId: string,
    deliverableId: string
  ): Promise<{ ok: boolean; deliverable: DeliverableRecord }> => {
    return workspaceFetch(`/api/projects/${projectId}/deliverables/${deliverableId}`);
  },

  deleteDeliverable: async (
    projectId: string,
    deliverableId: string
  ): Promise<{ ok: boolean; deleted: string }> => {
    return workspaceFetch(`/api/projects/${projectId}/deliverables/${deliverableId}`, {
      method: 'DELETE',
    });
  },
};
