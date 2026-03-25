import React from 'react'

const EXAMPLE_QUERIES = [
  'Girl student in engineering college with family income below 5 lakh',
  'Person with 60% disability wanting to pursue PhD',
  'OBC student admitted to IIT for BTech',
  'Student from Assam pursuing first year graduation',
  'Class 10 passed student with visual impairment',
]

export default function Hero({ searched }) {
  if (searched) {
    // Compact header when results are showing
    return (
      <div className="bg-white border-b border-gray-100 py-4">
        <div className="max-w-3xl mx-auto px-4">
          <h1 className="font-display font-semibold text-lg text-navy-500">
            Find Your Matching Schemes
          </h1>
        </div>
      </div>
    )
  }

  return (
    <section className="bg-white py-12 md:py-16 border-b border-gray-100">
      <div className="max-w-3xl mx-auto px-4 text-center">

        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-saffron-50 border border-saffron-200 text-saffron-700 text-xs font-medium px-3 py-1 rounded-full mb-6">
          <span className="text-base">🇮🇳</span>
          Government of India · AI-Powered Scheme Finder
        </div>

        {/* Headline */}
        <h1 className="font-display font-bold text-3xl md:text-4xl text-gray-900 leading-tight mb-3">
          Find the Government Schemes{' '}
          <span className="text-navy-500">You Are Eligible For</span>
        </h1>

        {/* Hindi subtitle */}
        <p className="font-body text-gray-500 text-base mb-2" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
          अपनी पात्रता के अनुसार सरकारी योजनाएं खोजें
        </p>

        <p className="font-body text-gray-500 text-sm mb-8 max-w-xl mx-auto">
          Describe your background in plain language — our AI matches you to
          scholarships, fellowships, and schemes from official government sources.
        </p>

        {/* Example chips */}
        <div className="text-left">
          <p className="text-xs font-medium text-gray-400 mb-2 text-center">
            EXAMPLE SEARCHES
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {EXAMPLE_QUERIES.map((q, i) => (
              <span
                key={i}
                className="text-xs bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full border border-gray-200 hover:bg-saffron-50 hover:border-saffron-200 hover:text-saffron-700 transition-colors cursor-default"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
