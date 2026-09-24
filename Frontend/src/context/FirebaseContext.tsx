import React, { createContext, useContext, useCallback, useEffect, useState, ReactNode } from 'react';
import { 
  User, 
  signInWithPopup, 
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  signOut as firebaseSignOut, 
  onAuthStateChanged 
} from 'firebase/auth';
import { 
  collection, 
  doc, 
  setDoc, 
  deleteDoc, 
  onSnapshot, 
  query, 
  where 
} from 'firebase/firestore';
import { auth, db, googleAuthProvider, handleFirestoreError, OperationType } from '../lib/firebase';
import { backendApi, backendEnabled } from '../services/backendService';
import { TransformationProject } from '../types';

export interface UserProfile {
  userId: string;
  email: string;
  displayName: string;
  photoURL?: string;
  authProvider: string;
  createdAt: string;
  updatedAt: string;
}

interface FirebaseContextType {
  user: User | null;
  authLoading: boolean;
  signInWithGoogle: () => Promise<boolean>;
  signInWithEmail: (email: string, password: string) => Promise<boolean>;
  signUpWithEmail: (name: string, email: string, password: string) => Promise<boolean>;
  signOutUser: () => Promise<void>;
  cloudProjects: TransformationProject[];
  isSyncing: boolean;
  saveProjectToCloud: (project: TransformationProject) => Promise<boolean>;
  deleteProjectFromCloud: (projectId: string) => Promise<boolean>;
}

const FirebaseContext = createContext<FirebaseContextType | undefined>(undefined);

/**
 * Normalize a backend /projects record into the frontend TransformationProject shape.
 */
function mapBackendProject(raw: Record<string, unknown>): TransformationProject {
  const title = (raw.title as string) || (raw.projectName as string) || 'Untitled Project';
  return {
    ...(raw as unknown as TransformationProject),
    id: (raw.id as string) || `proj-${Date.now()}`,
    title,
    description: (raw.description as string) || '',
    source: (raw.source ?? raw.sourceFile) as TransformationProject['source'],
    selectedOutputs: Array.isArray(raw.selectedOutputs)
      ? (raw.selectedOutputs as TransformationProject['selectedOutputs'])
      : []
  };
}

export const FirebaseProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [cloudProjects, setCloudProjects] = useState<TransformationProject[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // Sync user profile to Firestore and MongoDB backend
  const syncUserProfile = useCallback(async (currentUser: User, customName?: string) => {
    const displayName = customName || currentUser.displayName || currentUser.email?.split('@')[0] || 'Authorized User';
    const email = currentUser.email || '';
    const photoURL = currentUser.photoURL || '';
    const authProvider = currentUser.providerData?.[0]?.providerId || 'google.com';
    const now = new Date().toISOString();

    const profileData: UserProfile = {
      userId: currentUser.uid,
      email,
      displayName,
      photoURL,
      authProvider,
      createdAt: now,
      updatedAt: now,
    };

    // 1. Direct Firestore write to users/{uid}
    const userPath = `users/${currentUser.uid}`;
    try {
      await setDoc(
        doc(db, 'users', currentUser.uid),
        profileData,
        { merge: true }
      );
    } catch (error) {
      handleFirestoreError(error, OperationType.WRITE, userPath);
    }

    // 2. Backend sync (which also saves to MongoDB Atlas `users` collection)
    if (backendEnabled) {
      try {
        await backendApi.me();
      } catch (err) {
        console.warn('Backend /auth/me sync warning:', err);
      }
    }
  }, []);

  // Load projects from the FastAPI backend (used when VITE_BACKEND_URL is set)
  const loadBackendProjects = useCallback(async (): Promise<void> => {
    if (!backendEnabled) return;
    try {
      const raw = (await backendApi.listProjects()) as Record<string, unknown>[];
      setCloudProjects((Array.isArray(raw) ? raw : []).map(mapBackendProject));
    } catch (error) {
      console.warn('Backend project sync failed:', error);
    }
  }, []);

  // Monitor Auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      setAuthLoading(false);

      if (currentUser) {
        await syncUserProfile(currentUser);
        if (backendEnabled) {
          await loadBackendProjects();
        }
      } else {
        setCloudProjects([]);
      }
    });

    return () => unsubscribe();
  }, [loadBackendProjects, syncUserProfile]);

  // Listen to projects realtime updates when user is authenticated (Firestore mode)
  useEffect(() => {
    if (!user) {
      setCloudProjects([]);
      return;
    }

    if (backendEnabled) {
      loadBackendProjects();
      return;
    }

    const projectsCollectionPath = 'projects';
    const q = query(
      collection(db, projectsCollectionPath),
      where('userId', '==', user.uid)
    );

    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        const loaded: TransformationProject[] = [];
        snapshot.forEach((docSnap) => {
          const data = docSnap.data() as TransformationProject;
          loaded.push({ ...data, id: docSnap.id });
        });
        setCloudProjects(loaded);
      },
      (error) => {
        handleFirestoreError(error, OperationType.GET, projectsCollectionPath);
      }
    );

    return () => unsubscribe();
  }, [user, loadBackendProjects]);

  const signInWithGoogle = async (): Promise<boolean> => {
    try {
      const result = await signInWithPopup(auth, googleAuthProvider);
      if (result.user) {
        await syncUserProfile(result.user);
      }
      return true;
    } catch (error: any) {
      const errorCode = error?.code || '';
      if (
        errorCode === 'auth/popup-closed-by-user' ||
        errorCode === 'auth/cancelled-popup-request' ||
        errorCode === 'auth/user-cancelled'
      ) {
        return false;
      }
      if (errorCode === 'auth/popup-blocked') {
        console.warn('Google Sign In popup was blocked by the browser.');
        return false;
      }
      console.warn('Google Sign In warning:', error?.message || error);
      throw error;
    }
  };

  const signInWithEmail = async (email: string, password: string): Promise<boolean> => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      if (result.user) {
        await syncUserProfile(result.user);
      }
      return true;
    } catch (error: any) {
      console.warn('Sign In with Email warning:', error?.message || error);
      throw error;
    }
  };

  const signUpWithEmail = async (name: string, email: string, password: string): Promise<boolean> => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password);
      if (result.user) {
        // Update user display name in Firebase Auth
        await updateProfile(result.user, { displayName: name });
        // Store name & profile into Firestore & MongoDB
        await syncUserProfile(result.user, name);
      }
      return true;
    } catch (error: any) {
      console.warn('Sign Up with Email warning:', error?.message || error);
      throw error;
    }
  };

  const signOutUser = async () => {
    try {
      await firebaseSignOut(auth);
    } catch (error) {
      console.warn('Sign out warning:', error);
    }
  };

  const saveProjectToCloud = async (project: TransformationProject): Promise<boolean> => {
    if (!user) return false;
    setIsSyncing(true);

    if (backendEnabled) {
      try {
        const payload = {
          ...project,
          userId: user.uid,
          updatedAt: new Date().toISOString()
        };
        const exists = cloudProjects.some((p) => p.id === project.id);
        if (exists) {
          await backendApi.updateProject(project.id, payload);
        } else {
          try {
            await backendApi.createProject(payload);
          } catch {
            await backendApi.updateProject(project.id, payload);
          }
        }
        await loadBackendProjects();
        return true;
      } catch (error) {
        console.warn('Backend save failed:', error);
        return false;
      } finally {
        setIsSyncing(false);
      }
    }

    const targetDocPath = `projects/${project.id}`;
    try {
      const sanitizedProject = {
        ...project,
        userId: user.uid,
        updatedAt: new Date().toISOString()
      };
      await setDoc(doc(db, 'projects', project.id), sanitizedProject);
      setIsSyncing(false);
      return true;
    } catch (error) {
      setIsSyncing(false);
      handleFirestoreError(error, OperationType.WRITE, targetDocPath);
    }
  };

  const deleteProjectFromCloud = async (projectId: string): Promise<boolean> => {
    if (!user) return false;

    if (backendEnabled) {
      try {
        await backendApi.deleteProject(projectId);
        await loadBackendProjects();
        return true;
      } catch (error) {
        console.warn('Backend delete failed:', error);
        return false;
      }
    }

    const targetDocPath = `projects/${projectId}`;
    try {
      await deleteDoc(doc(db, 'projects', projectId));
      return true;
    } catch (error) {
      handleFirestoreError(error, OperationType.DELETE, targetDocPath);
    }
  };

  return (
    <FirebaseContext.Provider
      value={{
        user,
        authLoading,
        signInWithGoogle,
        signInWithEmail,
        signUpWithEmail,
        signOutUser,
        cloudProjects,
        isSyncing,
        saveProjectToCloud,
        deleteProjectFromCloud
      }}
    >
      {children}
    </FirebaseContext.Provider>
  );
};

export const useFirebase = (): FirebaseContextType => {
  const context = useContext(FirebaseContext);
  if (!context) {
    throw new Error('useFirebase must be used within a FirebaseProvider');
  }
  return context;
};
