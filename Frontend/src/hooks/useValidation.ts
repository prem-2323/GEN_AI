import { useState, useEffect, useCallback } from 'react';
import { validationApi } from '../api/validationApi';
import { ConsistencyValidationReport, DeliverableValidationResult } from '../types/validation';

export function useValidation(projectId?: string, sourceId?: string) {
  const [report, setReport] = useState<ConsistencyValidationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchValidation = useCallback(async () => {
    if (!projectId || !sourceId) {
      setReport(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await validationApi.getSourceValidation(projectId, sourceId);
      setReport(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load validation report');
    } finally {
      setLoading(false);
    }
  }, [projectId, sourceId]);

  useEffect(() => {
    if (projectId && sourceId) {
      fetchValidation();
    }
  }, [projectId, sourceId, fetchValidation]);

  const runValidation = async (): Promise<ConsistencyValidationReport> => {
    if (!projectId || !sourceId) throw new Error('Project ID and Source ID required');
    setLoading(true);
    setError(null);
    try {
      const res = await validationApi.validateSource(projectId, sourceId);
      setReport(res);
      return res;
    } catch (err: any) {
      const msg = err?.message || 'Validation failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const validateDeliverable = async (deliverableId: string): Promise<DeliverableValidationResult> => {
    if (!projectId) throw new Error('Project ID required');
    try {
      const res = await validationApi.validateDeliverable(projectId, deliverableId);
      return res.result;
    } catch (err: any) {
      throw new Error(err?.message || 'Deliverable validation failed');
    }
  };

  return {
    report,
    loading,
    error,
    refresh: fetchValidation,
    runValidation,
    validateDeliverable,
  };
}
