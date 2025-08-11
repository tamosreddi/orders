import Header from '@/components/landing/Header';
import Hero from '@/components/landing/Hero';
import HowItWorks from '@/components/landing/HowItWorks';
import WhyReddi from '@/components/landing/WhyReddi';
import CTA from '@/components/landing/CTA';
import Footer from '@/components/landing/Footer';

export default function HomePage() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <HowItWorks />
        <WhyReddi />
        <CTA />
      </main>
      <Footer />
    </>
  );
}