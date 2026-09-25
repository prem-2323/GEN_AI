import { useState, useEffect, useCallback } from 'react';
import { qualityApi } from '../api/qualityApi';
import { DeliverableQualityReport } from '../types/quality';

export function useQuality(projectId?: string, deliverableId?: string) {
  const [report, setReport] = useState<DeliverableQualityReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [approving, setApproving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuality = useCallback(async () => {
    if (!projectId || !deliverableId) {
      setReport(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await qualityApi.getQualityReport(projectId, deliverableId);
      setReport(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load quality report');
    } finally {
      setLoading(false);
    }
  }, [projectId, deliverableId]);

  useEffect(() => {
    if (projectId && deliverableId) {
      fetchQuality();
    }
  }, [projectId, deliverableId, fetchQuality]);

  const approve = async (): Promise<boolean> => {
    if (!projectId || !deliverableId) throw new Error('Project ID and Deliverable ID required');
    setApproving(true);
    setError(null);
    try {
      await qualityApi.approveDeliverable(projectId, deliverableId);
      if (report) {
        setReport({ ...report, approved: true, approvedAt: new Date().toISOString() });
      }
      return true;
    } catch (err: any) {
      const msg = err?.message || 'Approval failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setApproving(false);
    }
  };

  return {
    report,
    loading,
    approving,
    error,
    refresh: fetchQuality,
    approve,
  };
}
