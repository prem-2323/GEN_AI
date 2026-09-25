import { authenticatedFetch } from './client';
import { AnalysisRecord } from '../types/analysis';

export interface AnalysisStartRequest {
  extractedText?: string;
  extractedImages?: any[];
  forceRefresh?: boolean;
}

export const analysisApi = {
  startAnalysis: async (
    projectId: string,
    sourceId: string,
    payload?: AnalysisStartRequest
  ): Promise<AnalysisRecord> => {
    return authenticatedFetch(`/api/projects/${projectId}/sources/${sourceId}/analysis`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  },

  getAnalysis: async (projectId: string, sourceId: string): Promise<AnalysisRecord> => {
    return authenticatedFetch(`/api/projects/${projectId}/sources/${sourceId}/analysis`);
  },

  getAnalysisStatus: async (
    projectId: string,
    sourceId: string
  ): Promise<{ status: string; stage?: string; progress?: number; provider?: string }> => {
    return authenticatedFetch(`/api/projects/${projectId}/sources/${sourceId}/analysis/status`);
  },

  retryAnalysis: async (
    projectId: string,
    sourceId: string,
    payload?: AnalysisStartRequest
  ): Promise<AnalysisRecord> => {
    return authenticatedFetch(`/api/projects/${projectId}/sources/${sourceId}/analysis/retry`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  },
};
