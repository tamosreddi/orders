import type { Metadata } from 'next';
import { Inter, Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '../lib/auth/AuthContext';
import { ConditionalLayout } from '../components/ConditionalLayout';

const inter = Inter({ subsets: ['latin'] });
const plusJakarta = Plus_Jakarta_Sans({ 
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-plus-jakarta'
});

export const metadata: Metadata = {
  title: 'Reddi - AI Order Processing for Food Distributors',
  description: 'Automate order processing with AI agents. Save time and grow your food distribution business.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={plusJakarta.variable}>
      <body className={`${plusJakarta.className} font-antialiased`}>
        <AuthProvider>
          <ConditionalLayout>
            {children}
          </ConditionalLayout>
        </AuthProvider>
      </body>
    </html>
  );
}