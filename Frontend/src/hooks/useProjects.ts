import { useState, useEffect, useCallback } from 'react';
import { projectApi } from '../api/projectApi';
import { ProjectRecord, ProjectCreatePayload } from '../types/project';

export function useProjects() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await projectApi.getProjects();
      setProjects(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch projects');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const createProject = async (payload: ProjectCreatePayload): Promise<ProjectRecord> => {
    try {
      const newProj = await projectApi.createProject(payload);
      setProjects((prev) => [newProj, ...prev]);
      return newProj;
    } catch (err: any) {
      throw new Error(err?.message || 'Failed to create project');
    }
  };

  const deleteProject = async (projectId: string): Promise<boolean> => {
    try {
      await projectApi.deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => (p.id || p.projectId) !== projectId));
      return true;
    } catch (err: any) {
      throw new Error(err?.message || 'Failed to delete project');
    }
  };

  return {
    projects,
    loading,
    error,
    refresh: fetchProjects,
    createProject,
    deleteProject,
  };
}
