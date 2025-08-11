'use client';

import Image from 'next/image';
import Link from 'next/link';
import LoginButton from '@/components/auth/LoginButton';

export default function Header() {
  const handleBookDemo = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const emailInput = document.getElementById('demo-email-input');
    if (emailInput) {
      emailInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => {
        (emailInput as HTMLInputElement).focus();
      }, 500);
    }
  };
  const navigation = [
    { name: 'How it works', href: '#how-it-works' },
    { name: 'Why Reddi', href: '#why-reddi' },
  ];

  return (
    <header className="bg-white fixed top-0 w-full z-50 shadow-sm">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Top">
        <div className="flex w-full items-center justify-between py-4">
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <Image
                src="/design/logos/Reddi_green_name.png"
                alt="Reddi"
                width={100}
                height={40}
                className="h-10 w-auto"
              />
            </Link>
          </div>
          <div className="hidden md:flex md:items-center md:space-x-8">
            {navigation.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="text-base font-medium text-gray-700 hover:text-green-600"
              >
                {link.name}
              </Link>
            ))}
            <Link
              href="#book-demo"
              onClick={handleBookDemo}
              className="inline-flex items-center justify-center rounded-md bg-green-600 px-4 py-2 text-base font-medium text-white hover:bg-green-500"
            >
              Book a Demo
            </Link>
            <LoginButton />
          </div>
          <div className="md:hidden flex items-center space-x-2">
            <Link
              href="#book-demo"
              onClick={handleBookDemo}
              className="inline-flex items-center justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-500"
            >
              Book Demo
            </Link>
            <LoginButton />
          </div>
        </div>
      </nav>
    </header>
  );
}