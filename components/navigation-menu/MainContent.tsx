'use client';

import { useNavigation } from './NavigationContext';

interface MainContentProps {
  children: React.ReactNode;
}

export function MainContent({ children }: MainContentProps) {
  const { navigationState } = useNavigation();

  return (
    <main className={`
      transition-all duration-medium ease-standard
      ${navigationState.isCollapsed ? 'md:ml-16' : 'md:ml-64'}
    `}>
      {children}
    </main>
  );
}