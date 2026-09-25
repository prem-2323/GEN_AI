import { useState, useEffect, useCallback } from 'react';
import { transformationApi, TransformRequestPayload } from '../api/transformationApi';
import { DeliverableRecord, DeliverablesState, OutputType } from '../types/deliverable';

export function useDeliverables(projectId?: string) {
  const [deliverables, setDeliverables] = useState<DeliverablesState>({});
  const [records, setRecords] = useState<DeliverableRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDeliverables = useCallback(async () => {
    if (!projectId) {
      setDeliverables({});
      setRecords([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await transformationApi.listDeliverables(projectId);
      const items = res.deliverables || [];
      setRecords(items);

      // Map array into DeliverablesState keyed by output type
      const stateMap: DeliverablesState = {};
      items.forEach((item) => {
        const key = item.type as keyof DeliverablesState;
        if (key && item.content) {
          (stateMap as any)[key] = item.content;
        }
      });
      setDeliverables(stateMap);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch deliverables');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      fetchDeliverables();
    }
  }, [projectId, fetchDeliverables]);

  const transform = async (payload: TransformRequestPayload): Promise<DeliverableRecord[]> => {
    if (!projectId) throw new Error('Project ID required to run transformation');
    setGenerating(true);
    setError(null);
    try {
      const res = await transformationApi.transform(projectId, payload);
      await fetchDeliverables();
      return res.deliverables;
    } catch (err: any) {
      const msg = err?.message || 'Transformation failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setGenerating(false);
    }
  };

  const deleteDeliverable = async (deliverableId: string): Promise<boolean> => {
    if (!projectId) return false;
    try {
      await transformationApi.deleteDeliverable(projectId, deliverableId);
      await fetchDeliverables();
      return true;
    } catch (err: any) {
      throw new Error(err?.message || 'Failed to delete deliverable');
    }
  };

  return {
    deliverables,
    records,
    loading,
    generating,
    error,
    refresh: fetchDeliverables,
    transform,
    deleteDeliverable,
  };
}
