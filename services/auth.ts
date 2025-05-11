import { create } from 'zustand';
import { supabase } from './supabase';
import { Session } from '@supabase/supabase-js';

interface AuthState {
  user: any;
  session: Session | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  loading: true,
  error: null,
  login: async (email: string, password: string) => {
    try {
      set({ loading: true, error: null });
      const { data, error } = await supabase?.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
      set({ user: data.user, session: data.session, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  signup: async (email: string, password: string, name: string) => {
    try {
      set({ loading: true, error: null });
      const { data, error } = await supabase?.auth.signUp({
        email,
        password,
        options: {
          data: {
            name: name
          }
        }
      });
      if (error) throw error;
      set({ user: data.user, session: data.session, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  logout: async () => {
    try {
      set({ loading: true, error: null });
      const { error } = await supabase?.auth.signOut();
      if (error) throw error;
      set({ user: null, session: null, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
  checkSession: async () => {
    try {
      set({ loading: true, error: null });
      const { data: { session }, error } = await supabase?.auth.getSession();
      if (error) throw error;
      set({ session, user: session?.user ?? null, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
})); 