import { create } from 'zustand';
import type { Seller, TokenData } from '../types/auth';

type SessionStatus = 'initializing' | 'authenticated' | 'anonymous' | 'error';

interface SessionState {
  status: SessionStatus;
  accessToken: string | null;
  user: Seller | null;
  revision: number;
  accept: (data: TokenData) => void;
  clear: () => void;
  fail: () => void;
}

// Deliberately no persistence middleware: access tokens stay in this tab's memory.
export const useSession = create<SessionState>((set) => ({
  status: 'initializing',
  accessToken: null,
  user: null,
  revision: 0,
  accept: (data) => set((s) => ({
    status: 'authenticated', accessToken: data.access_token, user: data.user, revision: s.revision + 1,
  })),
  clear: () => set((s) => ({
    status: 'anonymous', accessToken: null, user: null, revision: s.revision + 1,
  })),
  fail: () => set((s) => ({
    status: 'error', accessToken: null, user: null, revision: s.revision + 1,
  })),
}));
