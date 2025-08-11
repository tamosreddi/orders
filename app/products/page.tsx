import Image from 'next/image';
import Link from 'next/link';

export default function ProductsPage() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="relative w-32 h-32 mx-auto mb-12">
          <Image
            src="/design/logos/yellow-cohete.png"
            alt="Coming Soon"
            width={128}
            height={128}
            className="object-contain"
          />
        </div>
        <h1 className="text-4xl font-light text-gray-900 mb-4">Coming Soon</h1>
        <p className="text-lg text-gray-600 mb-8">We&apos;re working on something exciting!</p>
        <Link
          href="/"
          className="inline-flex items-center text-green-600 hover:text-green-700 font-medium transition-colors"
        >
          ← Back to Home
        </Link>
      </div>
    </div>
  );
}