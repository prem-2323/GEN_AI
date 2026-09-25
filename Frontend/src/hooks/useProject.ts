import { useState, useEffect, useCallback } from 'react';
import { projectApi } from '../api/projectApi';
import { ProjectRecord, ProjectWorkspaceResponse } from '../types/project';

export function useProject(projectId?: string) {
  const [project, setProject] = useState<ProjectRecord | null>(null);
  const [workspace, setWorkspace] = useState<ProjectWorkspaceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(projectId));
  const [error, setError] = useState<string | null>(null);

  const fetchProjectAndWorkspace = useCallback(async () => {
    if (!projectId) {
      setProject(null);
      setWorkspace(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [projData, wsData] = await Promise.all([
        projectApi.getProject(projectId).catch(() => null),
        projectApi.getWorkspace(projectId).catch(() => null),
      ]);
      if (projData) setProject(projData);
      if (wsData) setWorkspace(wsData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load project');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProjectAndWorkspace();
  }, [fetchProjectAndWorkspace]);

  return {
    project,
    workspace,
    loading,
    error,
    refresh: fetchProjectAndWorkspace,
  };
}
