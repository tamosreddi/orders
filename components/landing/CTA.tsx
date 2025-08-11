'use client';

import Link from 'next/link';

export default function CTA() {
  const handleGetStarted = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const emailInput = document.getElementById('demo-email-input');
    if (emailInput) {
      emailInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => {
        (emailInput as HTMLInputElement).focus();
      }, 500);
    }
  };
  return (
    <section id="book-demo" className="bg-green-600 py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl font-light tracking-tight text-white sm:text-4xl">
          Ready to save hours every week?
        </h2>
        <p className="mt-4 text-lg text-green-100 max-w-2xl mx-auto font-light">
          Book a demo and see how Reddi can transform your order workflow.
        </p>
        <div className="mt-8">
          <Link
            href="#"
            onClick={handleGetStarted}
            className="inline-flex items-center justify-center rounded-md bg-white px-8 py-3 text-base font-semibold text-green-600 shadow-sm hover:bg-green-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            Get Started
          </Link>
        </div>
      </div>
    </section>
  );
}