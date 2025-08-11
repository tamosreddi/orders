'use client';

import Image from 'next/image';
import { useState } from 'react';

export default function Hero() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/demo-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setSubmitted(true);
        setEmail('');
      }
    } catch (error) {
      console.error('Error submitting demo request:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-16 text-center lg:pt-32">
        <div className="mx-auto max-w-4xl">
          <p className="text-sm font-bold leading-7 text-green-600 tracking-wide uppercase">
            Built for Food Distributors
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-gray-900 sm:text-6xl">
            AI Agents to streamline
            <span className="block">Order Processing</span>
          </h1>
          <p className="mt-6 text-xl leading-8 text-gray-600 max-w-2xl mx-auto font-light">
            Automate manual work for Sales Teams so they can focus on growing your business.
          </p>
          
          {/* Email Capture Form */}
          <div className="mt-10 max-w-lg mx-auto">
            {submitted ? (
              <div className="rounded-md bg-green-50 p-4">
                <p className="text-sm font-medium text-green-800">
                  Thanks! We&apos;ll be in touch soon to schedule your demo.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
                <input
                  id="demo-email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="flex-1 min-w-0 sm:min-w-[280px] rounded-md border border-gray-300 px-4 py-3 text-base placeholder-gray-500 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
                  required
                />
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-md bg-green-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Submitting...' : 'Schedule a Demo'}
                </button>
              </form>
            )}
          </div>

          <p className="mt-10 text-base text-gray-600">
            The simplest way to get orders into your ERP or CRM.
          </p>
          
          <div className="mt-16 flex justify-center">
            <div className="relative w-32 h-32">
              <Image
                src="/design/logos/yellow-cohete.png"
                alt="Reddi Rocket"
                width={128}
                height={128}
                className="object-contain"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}