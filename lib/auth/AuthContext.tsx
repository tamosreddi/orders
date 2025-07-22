'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../supabase/client';
import type { User } from '@supabase/supabase-js';

interface AuthContextType {
  user: User | null;
  distributorId: string | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  distributorId: null,
  loading: true,
  signOut: async () => {}
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [distributorId, setDistributorId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Error getting session:', error);
        } else if (session?.user) {
          setUser(session.user);
          // For now, use a default distributor ID
          // TODO: Fetch actual distributor_id from user_profiles table
          setDistributorId('default-distributor-id');
        }
      } catch (error) {
        console.error('Error in getInitialSession:', error);
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state change:', event, session?.user?.id);
        
        if (session?.user) {
          setUser(session.user);
          // TODO: Fetch actual distributor_id from user_profiles table
          setDistributorId('default-distributor-id');
        } else {
          setUser(null);
          setDistributorId(null);
        }
        
        setLoading(false);
      }
    );

    return () => {
      subscription?.unsubscribe();
    };
  }, []);

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      distributorId,
      loading,
      signOut
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook to get the current distributor ID
 * For now returns a default value, but will be enhanced with proper auth
 */
export function useDistributorId(): string {
  const { distributorId } = useAuth();
  // Return default for now, but this should come from authenticated user's profile
  return distributorId || 'default-distributor-id';
}