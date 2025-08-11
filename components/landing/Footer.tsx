import Image from 'next/image';
import Link from 'next/link';

export default function Footer() {
  const currentYear = new Date().getFullYear();
  
  const companyLinks = [
    { name: 'Home', href: '/' },
    { name: 'About', href: '/about' },
    { name: 'Contact', href: '/contact' },
  ];

  const productLinks = [
    { name: 'Features', href: '/products' },
    { name: 'Pricing', href: '/products' },
    { name: 'Integrations', href: '/products' },
    { name: 'API Docs', href: '/products' },
    { name: 'Status', href: '/products' },
  ];

  const legalLinks = [
    { name: 'Privacy Policy', href: '#' },
    { name: 'Terms of Service', href: '#' },
    { name: 'Cookie Policy', href: '#' },
    { name: 'GDPR', href: '#' },
  ];

  const socialLinks = [
    { name: 'LinkedIn', href: 'https://linkedin.com/company/reddi-ai' },
  ];

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {/* Logo and description */}
          <div className="col-span-2 md:col-span-1">
            <Image
              src="/design/logos/Reddi_green_name.png"
              alt="Reddi"
              width={120}
              height={48}
              className="h-12 w-auto brightness-0 invert"
            />
            <p className="mt-4 text-sm text-gray-400">
              AI-powered order processing for food distributors.
            </p>
          </div>

          {/* Company links */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
              Company
            </h3>
            <ul className="space-y-3">
              {companyLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-300 hover:text-white transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Product links */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
              Product
            </h3>
            <ul className="space-y-3">
              {productLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-300 hover:text-white transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal links */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
              Legal
            </h3>
            <ul className="space-y-3">
              {legalLinks.map((link) => (
                <li key={link.name}>
                  <span className="text-sm text-gray-300 cursor-default">
                    {link.name}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Social links */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
              Connect
            </h3>
            <ul className="space-y-3">
              {socialLinks.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-gray-300 hover:text-white transition-colors"
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 border-t border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-400">
              © {currentYear} Reddi AI, Inc. All rights reserved.
            </p>
            <div className="mt-4 md:mt-0 flex items-center space-x-6">
              <Link
                href="/security"
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                Security
              </Link>
              <Link
                href="/sitemap"
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                Sitemap
              </Link>
              <span className="text-sm text-gray-400">
                Made with ❤️ in San Francisco
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}