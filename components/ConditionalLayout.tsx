'use client';

import { usePathname } from 'next/navigation';
import { NavigationProvider } from './navigation-menu/NavigationContext';
import { NavigationMenu } from './navigation-menu/NavigationMenu';
import { MainContent } from './navigation-menu/MainContent';

export function ConditionalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLandingPage = pathname === '/' || pathname === '/products';

  if (isLandingPage) {
    return <>{children}</>;
  }

  return (
    <NavigationProvider>
      <div className="min-h-screen bg-surface-0">
        <NavigationMenu />
        <MainContent>
          {children}
        </MainContent>
      </div>
    </NavigationProvider>
  );
}