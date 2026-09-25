import { authenticatedFetch } from './client';

export interface UserAuthProfile {
  uid: string;
  email?: string;
  displayName?: string;
  photoURL?: string;
  roles?: string[];
}

export const authApi = {
  getMe: async (): Promise<{ ok: boolean; user: UserAuthProfile }> => {
    return authenticatedFetch('/api/me');
  },
};
