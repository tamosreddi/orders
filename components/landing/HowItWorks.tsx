import Image from 'next/image';

export default function HowItWorks() {
  const steps = [
    {
      number: '01',
      icon: '/logos/ventas-perdidas.png',
      title: 'Centralize orders',
      description: 'Consolidate all orders from WhatsApp, email, phone, voicemail, and more into one simple dashboard.',
      color: 'from-green-400 to-green-600',
    },
    {
      number: '02',
      icon: '/logos/bot.png',
      title: 'Automate processing',
      description: 'AI agents read messages, extract items, confirm availability, and generate orders in your ERP or CRM.',
      color: 'from-green-500 to-green-700',
    },
    {
      number: '03',
      icon: '/logos/manita.png',
      title: 'Save time, grow sales',
      description: 'Your team spends less time on admin and more time selling and winning new accounts.',
      color: 'from-green-600 to-green-800',
    },
  ];

  return (
    <section id="how-it-works" className="bg-white py-24 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-light tracking-tight text-gray-900 sm:text-4xl">
            How it works
          </h2>
        </div>
        
        <div className="mt-20 relative">
          {/* Desktop staggered layout */}
          <div className="hidden lg:block">
            {steps.map((step, index) => (
              <div key={step.number} className="relative">
                {/* Connecting line */}
                {index < steps.length - 1 && (
                  <div 
                    className={`absolute top-32 ${
                      index % 2 === 0 ? 'left-1/2' : 'right-1/2'
                    } w-96 h-0.5 bg-gradient-to-r ${step.color} opacity-30`}
                    style={{
                      transform: index % 2 === 0 ? 'rotate(-15deg)' : 'rotate(15deg)',
                      transformOrigin: index % 2 === 0 ? 'left center' : 'right center',
                    }}
                  />
                )}
                
                {/* Card */}
                <div 
                  className={`relative max-w-md mx-auto ${
                    index === 1 ? 'lg:ml-auto lg:mr-0' : ''
                  } ${index > 0 ? 'mt-16' : ''}`}
                >
                  <div className="bg-white rounded-2xl shadow-xl p-8 hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-center justify-between mb-6">
                      <div className="relative w-16 h-16">
                        <Image
                          src={step.icon}
                          alt={step.title}
                          width={64}
                          height={64}
                          className="object-contain"
                        />
                      </div>
                      <span className={`text-6xl font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent opacity-20`}>
                        {step.number}
                      </span>
                    </div>
                    <h3 className="text-2xl font-medium text-gray-900 mb-4">{step.title}</h3>
                    <p className="text-base text-gray-600 font-light leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Mobile/Tablet layout */}
          <div className="lg:hidden space-y-8">
            {steps.map((step, index) => (
              <div key={step.number} className="relative">
                {index > 0 && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 w-0.5 h-8 bg-gradient-to-b from-transparent via-green-300 to-transparent" />
                )}
                <div className="bg-white rounded-2xl shadow-xl p-6 hover:shadow-2xl transition-shadow">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="relative w-12 h-12">
                      <Image
                        src={step.icon}
                        alt={step.title}
                        width={48}
                        height={48}
                        className="object-contain"
                      />
                    </div>
                    <span className={`text-3xl font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent`}>
                      {step.number}
                    </span>
                  </div>
                  <h3 className="text-xl font-medium text-gray-900 mb-3">{step.title}</h3>
                  <p className="text-base text-gray-600 font-light">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}