import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { backendApi } from '../services/backendService';
import { TransformationProject } from '../types';

interface WorkspaceContextType {
  projects: TransformationProject[];
  isSyncing: boolean;
  saveProject: (project: TransformationProject) => Promise<boolean>;
  deleteProject: (projectId: string) => Promise<boolean>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

function mapProject(raw: Record<string, unknown>): TransformationProject {
  return {
    ...(raw as unknown as TransformationProject),
    id: String(raw.id || raw.projectId || `proj-${Date.now()}`),
    title: String(raw.title || raw.projectName || raw.name || 'Untitled Project'),
    description: String(raw.description || ''),
    source: (raw.source ?? raw.sourceFile) as TransformationProject['source'],
    selectedOutputs: Array.isArray(raw.selectedOutputs)
      ? raw.selectedOutputs as TransformationProject['selectedOutputs']
      : [],
  };
}

export const WorkspaceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<TransformationProject[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  const loadProjects = useCallback(async () => {
    try {
      const raw = await backendApi.listProjects() as Record<string, unknown>[];
      setProjects((Array.isArray(raw) ? raw : []).map(mapProject));
    } catch (error) {
      console.warn('Local workspace project load failed:', error);
    }
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  const saveProject = async (project: TransformationProject): Promise<boolean> => {
    setIsSyncing(true);
    try {
      const payload = { ...project, userId: 'local-workspace' };
      if (projects.some((saved) => saved.id === project.id)) {
        await backendApi.updateProject(project.id, payload);
      } else {
        await backendApi.createProject(payload);
      }
      await loadProjects();
      return true;
    } catch (error) {
      console.warn('Local workspace project save failed:', error);
      return false;
    } finally {
      setIsSyncing(false);
    }
  };

  const deleteProject = async (projectId: string): Promise<boolean> => {
    try {
      await backendApi.deleteProject(projectId);
      await loadProjects();
      return true;
    } catch (error) {
      console.warn('Local workspace project delete failed:', error);
      return false;
    }
  };

  return (
    <WorkspaceContext.Provider value={{ projects, isSyncing, saveProject, deleteProject }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = (): WorkspaceContextType => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};