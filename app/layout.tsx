import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { NavigationProvider } from '../components/navigation-menu/NavigationContext';
import { NavigationMenu } from '../components/navigation-menu/NavigationMenu';
import { MainContent } from '../components/navigation-menu/MainContent';
import { AuthProvider } from '../lib/auth/AuthContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Reddi Orders Dashboard',
  description: 'Manage your orders efficiently with the Reddi dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} font-antialiased`}>
        <AuthProvider>
          <NavigationProvider>
            <div className="min-h-screen bg-surface-0">
              <NavigationMenu />
              <MainContent>
                {children}
              </MainContent>
            </div>
          </NavigationProvider>
        </AuthProvider>
      </body>
    </html>
  );
}