import { useState, useEffect, useCallback } from 'react';
import { uckrApi } from '../api/uckrApi';
import { UckrKnowledgeBase, UckrVersionSummary } from '../types/uckr';

export function useUCKR(projectId?: string, sourceId?: string) {
  const [uckr, setUckr] = useState<UckrKnowledgeBase | null>(null);
  const [versions, setVersions] = useState<UckrVersionSummary[]>([]);
  const [currentVersion, setCurrentVersion] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUckr = useCallback(async () => {
    if (!projectId) {
      setUckr(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      let res;
      if (sourceId) {
        res = await uckrApi.getSourceUckr(projectId, sourceId);
      } else {
        res = await uckrApi.getProjectUckr(projectId);
      }
      if (res.uckr) {
        setUckr(res.uckr);
        setCurrentVersion(res.uckr.version || 1);
      }
      // Load versions
      const verRes = await uckrApi.listUckrVersions(projectId, sourceId).catch(() => ({ versions: [] }));
      setVersions(verRes.versions || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load UCKR knowledge base');
    } finally {
      setLoading(false);
    }
  }, [projectId, sourceId]);

  useEffect(() => {
    if (projectId) {
      fetchUckr();
    }
  }, [projectId, sourceId, fetchUckr]);

  const selectVersion = async (version: number) => {
    if (!projectId || !sourceId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await uckrApi.getUckrVersion(projectId, sourceId, version);
      if (res.uckr) {
        setUckr(res.uckr);
        setCurrentVersion(version);
      }
    } catch (err: any) {
      setError(err?.message || `Failed to load UCKR version ${version}`);
    } finally {
      setLoading(false);
    }
  };

  const buildUckr = async (): Promise<UckrKnowledgeBase> => {
    if (!projectId || !sourceId) throw new Error('Project ID and Source ID required');
    setLoading(true);
    setError(null);
    try {
      const res = await uckrApi.buildUckr(projectId, sourceId);
      setUckr(res.uckr);
      setCurrentVersion(res.version || 1);
      return res.uckr;
    } catch (err: any) {
      const msg = err?.message || 'Failed to build UCKR';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const rebuildUckr = async (): Promise<UckrKnowledgeBase> => {
    if (!projectId || !sourceId) throw new Error('Project ID and Source ID required');
    setLoading(true);
    setError(null);
    try {
      const res = await uckrApi.rebuildUckr(projectId, sourceId);
      setUckr(res.uckr);
      setCurrentVersion(res.version || 1);
      await fetchUckr();
      return res.uckr;
    } catch (err: any) {
      const msg = err?.message || 'Failed to rebuild UCKR';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  return {
    uckr,
    versions,
    currentVersion,
    loading,
    error,
    refresh: fetchUckr,
    selectVersion,
    buildUckr,
    rebuildUckr,
  };
}
