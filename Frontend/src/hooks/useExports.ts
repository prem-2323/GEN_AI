import { useState, useEffect, useCallback } from 'react';
import { exportApi } from '../api/exportApi';
import { ExportRecord, ExportRequestPayload } from '../types/export';

export function useExports(projectId?: string) {
  const [exports, setExports] = useState<ExportRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [exporting, setExporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExports = useCallback(async () => {
    if (!projectId) {
      setExports([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await exportApi.listExports(projectId);
      setExports(res.exports || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to list exports');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      fetchExports();
    }
  }, [projectId, fetchExports]);

  const exportDeliverable = async (
    deliverableId: string,
    payload: ExportRequestPayload
  ): Promise<ExportRecord> => {
    if (!projectId) throw new Error('Project ID required');
    setExporting(true);
    setError(null);
    try {
      const res = await exportApi.exportDeliverable(projectId, deliverableId, payload);
      await fetchExports();
      return res.export;
    } catch (err: any) {
      const msg = err?.message || 'Export failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setExporting(false);
    }
  };

  const downloadExport = async (exportId: string): Promise<void> => {
    if (!projectId) return;
    try {
      const { blob, filename } = await exportApi.downloadExportBlob(projectId, exportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      throw new Error(err?.message || 'Failed to download export');
    }
  };

  return {
    exports,
    loading,
    exporting,
    error,
    refresh: fetchExports,
    exportDeliverable,
    downloadExport,
  };
}
