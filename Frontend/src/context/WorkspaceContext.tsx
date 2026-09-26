import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { backendApi, checkBackendHealth } from '../services/backendService';
import { TransformationProject } from '../types';

const STORAGE_KEY = 'contentforge_workspace_projects';

interface WorkspaceContextType {
  projects: TransformationProject[];
  isSyncing: boolean;
  backendOnline: boolean | null;
  saveProject: (project: TransformationProject) => Promise<boolean>;
  deleteProject: (projectId: string) => Promise<boolean>;
  refreshProjects: () => Promise<void>;
  checkBackend: () => Promise<boolean>;
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
      ? (raw.selectedOutputs as TransformationProject['selectedOutputs'])
      : [],
  };
}

function getStoredProjects(): TransformationProject[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(mapProject) : [];
  } catch {
    return [];
  }
}

function setStoredProjects(projects: TransformationProject[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
  } catch (err) {
    console.warn('Could not write projects to localStorage:', err);
  }
}

export const WorkspaceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<TransformationProject[]>(() => getStoredProjects());
  const [isSyncing, setIsSyncing] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  const checkBackend = useCallback(async (): Promise<boolean> => {
    const isHealthy = await checkBackendHealth(true);
    setBackendOnline(isHealthy);
    return isHealthy;
  }, []);

  const loadProjects = useCallback(async () => {
    // 1. Instantly use cached local storage data
    const local = getStoredProjects();
    if (local.length > 0) {
      setProjects(local);
    }

    // 2. Check backend connectivity
    try {
      const isHealthy = await checkBackendHealth();
      setBackendOnline(isHealthy);

      if (isHealthy) {
        const raw = (await backendApi.listProjects().catch(() => null)) as Record<string, unknown>[] | null;
        if (Array.isArray(raw)) {
          const backendList = raw.map(mapProject);

          // Merge: backend list + any local-only projects
          const mergedMap = new Map<string, TransformationProject>();
          for (const p of local) mergedMap.set(p.id, p);
          for (const p of backendList) mergedMap.set(p.id, p);

          const merged = Array.from(mergedMap.values());
          setProjects(merged);
          setStoredProjects(merged);
        }
      }
    } catch {
      setBackendOnline(false);
    }
  }, []);

  useEffect(() => {
    void loadProjects();

    // Check health on window focus or periodically
    const handleFocus = () => {
      void checkBackendHealth(true).then((online) => setBackendOnline(online));
    };
    window.addEventListener('focus', handleFocus);

    const interval = setInterval(() => {
      void checkBackendHealth().then((online) => setBackendOnline(online));
    }, 15000);

    return () => {
      window.removeEventListener('focus', handleFocus);
      clearInterval(interval);
    };
  }, [loadProjects]);

  const saveProject = async (project: TransformationProject): Promise<boolean> => {
    setIsSyncing(true);
    const normalized = mapProject(project as unknown as Record<string, unknown>);

    // 1. Immediately save to localStorage and React state so data is NEVER lost
    setProjects((prev) => {
      const idx = prev.findIndex((p) => p.id === normalized.id);
      const updated = idx >= 0 ? prev.map((p, i) => (i === idx ? normalized : p)) : [normalized, ...prev];
      setStoredProjects(updated);
      return updated;
    });

    // 2. Attempt backend persistence if available
    try {
      const isHealthy = await checkBackendHealth();
      setBackendOnline(isHealthy);
      if (isHealthy) {
        const payload = { ...normalized, userId: 'local-workspace' };
        const existsOnBackend = projects.some((saved) => saved.id === normalized.id);
        if (existsOnBackend) {
          await backendApi.updateProject(normalized.id, payload).catch(() => null);
        } else {
          await backendApi.createProject(payload).catch(() => null);
        }
      }
      return true;
    } catch (error) {
      console.warn('Backend sync deferred (saved to local workspace):', error);
      return true; // Still true because project is saved locally in browser!
    } finally {
      setIsSyncing(false);
    }
  };

  const deleteProject = async (projectId: string): Promise<boolean> => {
    // 1. Remove from local state and storage
    setProjects((prev) => {
      const updated = prev.filter((p) => p.id !== projectId);
      setStoredProjects(updated);
      return updated;
    });

    // 2. Delete on backend if online
    try {
      const isHealthy = await checkBackendHealth();
      setBackendOnline(isHealthy);
      if (isHealthy) {
        await backendApi.deleteProject(projectId).catch(() => null);
      }
      return true;
    } catch (error) {
      console.warn('Backend delete error:', error);
      return true;
    }
  };

  return (
    <WorkspaceContext.Provider
      value={{
        projects,
        isSyncing,
        backendOnline,
        saveProject,
        deleteProject,
        refreshProjects: loadProjects,
        checkBackend,
      }}
    >
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