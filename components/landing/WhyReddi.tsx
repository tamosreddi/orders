export default function WhyReddi() {
  const benefits = [
    {
      title: 'Faster order intake',
      description: 'from message → validated order in seconds.',
      icon: '⚡',
    },
    {
      title: 'Fewer errors',
      description: 'structured items, quantities, and confirmations.',
      icon: '✓',
    },
    {
      title: 'Works with your tools',
      description: 'export to CSV/ERP or simple web dashboard.',
      icon: '🔧',
    },
  ];

  return (
    <section id="why-reddi" className="bg-white py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-light tracking-tight text-gray-900 sm:text-4xl">
            Why Reddi
          </h2>
          <p className="mt-4 text-lg text-gray-600 max-w-3xl mx-auto font-light">
            Food distribution is complex. Orders arrive in multiple formats and your sales reps spend over 60% of their time on manual work. 
            Reddi&apos;s AI agents eliminate repetitive tasks so your team can focus on growth.
          </p>
        </div>
        
        <div className="mt-16 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {benefits.map((benefit, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-8">
              <div className="text-4xl mb-4">{benefit.icon}</div>
              <h3 className="text-xl font-medium text-gray-900">{benefit.title}</h3>
              <p className="mt-2 text-base text-gray-600 font-light">{benefit.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}