import { useState, useEffect, useCallback } from 'react';
import { sourceApi } from '../api/sourceApi';
import { SourceFile } from '../types/source';

export function useSources(projectId?: string) {
  const [sources, setSources] = useState<SourceFile[]>([]);
  const [loading, setLoading] = useState<boolean>(Boolean(projectId));
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    if (!projectId) {
      setSources([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await sourceApi.getSources(projectId);
      setSources(res.sources || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch sources');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const uploadSource = async (file: File): Promise<SourceFile> => {
    if (!projectId) throw new Error('Project ID required to upload source');
    setUploading(true);
    setError(null);
    try {
      const res = await sourceApi.uploadSource(projectId, file);
      const newSource = res.source;
      setSources((prev) => [newSource, ...prev]);
      return newSource;
    } catch (err: any) {
      const msg = err?.message || 'Source upload failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setUploading(false);
    }
  };

  const deleteSource = async (sourceId: string): Promise<boolean> => {
    try {
      await sourceApi.deleteSource(sourceId);
      setSources((prev) => prev.filter((s) => (s.id || s.sourceId) !== sourceId));
      return true;
    } catch (err: any) {
      throw new Error(err?.message || 'Failed to delete source');
    }
  };

  return {
    sources,
    loading,
    uploading,
    error,
    refresh: fetchSources,
    uploadSource,
    deleteSource,
  };
}
