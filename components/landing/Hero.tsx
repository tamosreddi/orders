import Image from 'next/image';
import Link from 'next/link';

export default function Hero() {
  return (
    <section className="bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center lg:pt-32">
        <div className="mx-auto max-w-4xl">
          <p className="text-sm font-bold leading-7 text-green-600 tracking-wide uppercase">
            Built for Food Distributors
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-gray-900 sm:text-6xl">
            AI Agents to streamline
            <span className="block">Order Processing</span>
          </h1>
          <p className="mt-6 text-xl leading-8 text-gray-600 max-w-2xl mx-auto font-light">
            Automate manual work and focus on growing your business.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Link
              href="#book-demo"
              className="rounded-md bg-green-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
            >
              Book a Demo
            </Link>
            <Link href="#how-it-works" className="text-base font-semibold leading-6 text-gray-900 flex items-center">
              See how it works
              <span aria-hidden="true" className="ml-2">→</span>
            </Link>
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