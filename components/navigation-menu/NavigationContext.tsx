'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { NavigationState } from './types';

interface NavigationContextType {
  navigationState: NavigationState;
  setNavigationState: (state: NavigationState) => void;
  toggleCollapsed: () => void;
  toggleMobileMenu: () => void;
  closeMobileMenu: () => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export function NavigationProvider({ children }: { children: ReactNode }) {
  const [navigationState, setNavigationState] = useState<NavigationState>({
    isCollapsed: false,
    isMobileMenuOpen: false
  });

  // Load collapsed state from localStorage on mount
  useEffect(() => {
    const savedCollapsedState = localStorage.getItem('nav-collapsed');
    if (savedCollapsedState) {
      setNavigationState(prev => ({
        ...prev,
        isCollapsed: JSON.parse(savedCollapsedState)
      }));
    }
  }, []);

  const toggleCollapsed = () => {
    const newCollapsedState = !navigationState.isCollapsed;
    setNavigationState(prev => ({
      ...prev,
      isCollapsed: newCollapsedState
    }));
    localStorage.setItem('nav-collapsed', JSON.stringify(newCollapsedState));
  };

  const toggleMobileMenu = () => {
    setNavigationState(prev => ({
      ...prev,
      isMobileMenuOpen: !prev.isMobileMenuOpen
    }));
  };

  const closeMobileMenu = () => {
    setNavigationState(prev => ({
      ...prev,
      isMobileMenuOpen: false
    }));
  };

  return (
    <NavigationContext.Provider value={{
      navigationState,
      setNavigationState,
      toggleCollapsed,
      toggleMobileMenu,
      closeMobileMenu
    }}>
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation() {
  const context = useContext(NavigationContext);
  if (context === undefined) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
}