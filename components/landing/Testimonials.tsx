export default function Testimonials() {
  const testimonials = [
    {
      quote: "Before Reddi, we were drowning in WhatsApp orders. Now the team spends the day closing deals, not typing orders.",
      author: "Distributor CEO",
    },
    {
      quote: "Setup took minutes. The agents just work in the background and keep our warehouse synced.",
      author: "Operations Lead",
    },
  ];

  return (
    <section className="bg-gray-50 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            What partners say
          </h2>
        </div>
        
        <div className="mt-16 grid grid-cols-1 gap-8 lg:grid-cols-2">
          {testimonials.map((testimonial, index) => (
            <div key={index} className="bg-white rounded-lg p-8 shadow-sm">
              <blockquote>
                <p className="text-lg text-gray-600 italic">
                  "{testimonial.quote}"
                </p>
                <footer className="mt-4">
                  <p className="text-base font-semibold text-gray-900">
                    — {testimonial.author}
                  </p>
                </footer>
              </blockquote>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}