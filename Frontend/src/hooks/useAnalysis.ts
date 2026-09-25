import { useState, useEffect, useCallback } from 'react';
import { analysisApi, AnalysisStartRequest } from '../api/analysisApi';
import { AnalysisRecord } from '../types/analysis';

export function useAnalysis(projectId?: string, sourceId?: string) {
  const [analysis, setAnalysis] = useState<AnalysisRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    if (!projectId || !sourceId) {
      setAnalysis(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await analysisApi.getAnalysis(projectId, sourceId);
      setAnalysis(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch AI analysis');
    } finally {
      setLoading(false);
    }
  }, [projectId, sourceId]);

  useEffect(() => {
    if (projectId && sourceId) {
      fetchAnalysis();
    }
  }, [projectId, sourceId, fetchAnalysis]);

  const startAnalysis = async (payload?: AnalysisStartRequest): Promise<AnalysisRecord> => {
    if (!projectId || !sourceId) throw new Error('Project ID and Source ID required');
    setLoading(true);
    setError(null);
    try {
      const res = await analysisApi.startAnalysis(projectId, sourceId, payload);
      setAnalysis(res);
      return res;
    } catch (err: any) {
      const msg = err?.message || 'Failed to start AI analysis';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const retryAnalysis = async (payload?: AnalysisStartRequest): Promise<AnalysisRecord> => {
    if (!projectId || !sourceId) throw new Error('Project ID and Source ID required');
    setLoading(true);
    setError(null);
    try {
      const res = await analysisApi.retryAnalysis(projectId, sourceId, payload);
      setAnalysis(res);
      return res;
    } catch (err: any) {
      const msg = err?.message || 'Failed to retry AI analysis';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  return {
    analysis,
    loading,
    error,
    refresh: fetchAnalysis,
    startAnalysis,
    retryAnalysis,
  };
}
