import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { 
  User, 
  signInWithPopup, 
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
import { TransformationProject } from '../types';

interface FirebaseContextType {
  user: User | null;
  authLoading: boolean;
  signInWithGoogle: () => Promise<boolean>;
  signOutUser: () => Promise<void>;
  cloudProjects: TransformationProject[];
  isSyncing: boolean;
  saveProjectToCloud: (project: TransformationProject) => Promise<boolean>;
  deleteProjectFromCloud: (projectId: string) => Promise<boolean>;
}

const FirebaseContext = createContext<FirebaseContextType | undefined>(undefined);

export const FirebaseProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [cloudProjects, setCloudProjects] = useState<TransformationProject[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // Monitor Auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      setAuthLoading(false);

      if (currentUser) {
        // Sync or update user document in firestore
        const userPath = `users/${currentUser.uid}`;
        try {
          await setDoc(
            doc(db, 'users', currentUser.uid),
            {
              userId: currentUser.uid,
              email: currentUser.email || '',
              displayName: currentUser.displayName || 'Authorized User',
              photoURL: currentUser.photoURL || '',
              createdAt: new Date().toISOString()
            },
            { merge: true }
          );
        } catch (error) {
          handleFirestoreError(error, OperationType.WRITE, userPath);
        }
      } else {
        setCloudProjects([]);
      }
    });

    return () => unsubscribe();
  }, []);

  // Listen to projects realtime updates when user is authenticated
  useEffect(() => {
    if (!user) {
      setCloudProjects([]);
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
  }, [user]);

  const signInWithGoogle = async (): Promise<boolean> => {
    try {
      await signInWithPopup(auth, googleAuthProvider);
      return true;
    } catch (error: any) {
      const errorCode = error?.code || '';
      // Normal user dismissal of popup or concurrent request cancellation
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
      return false;
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
