import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

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
        <div className="min-h-screen bg-surface-0">
          {children}
        </div>
      </body>
    </html>
  );
}