import React from 'react'

/* Ashoka Chakra SVG – 24 spokes */
const AshokaChakra = ({ size = 40, spin = false }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 100 100"
    className={spin ? 'chakra-spin' : ''}
    aria-hidden="true"
  >
    <circle cx="50" cy="50" r="46" fill="none" stroke="#000080" strokeWidth="3" />
    <circle cx="50" cy="50" r="6" fill="#000080" />
    {Array.from({ length: 24 }).map((_, i) => {
      const angle = (i * 360) / 24
      const rad = (angle * Math.PI) / 180
      const x1 = 50 + 6 * Math.cos(rad)
      const y1 = 50 + 6 * Math.sin(rad)
      const x2 = 50 + 43 * Math.cos(rad)
      const y2 = 50 + 43 * Math.sin(rad)
      return (
        <line
          key={i}
          x1={x1} y1={y1}
          x2={x2} y2={y2}
          stroke="#000080"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
      )
    })}
  </svg>
)

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm no-print">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo + Title */}
        <div className="flex items-center gap-3">
          <AshokaChakra size={42} spin={false} />
          <div>
            <div className="font-display font-bold text-xl text-navy-500 leading-tight">
              SchemeMatch Bharat
            </div>
            <div className="text-xs text-gray-500 font-body tracking-wide">
              Government Scheme Finder · भारत सरकार
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-body">
          <a
            href="https://www.india.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-navy-500 transition-colors"
          >
            India.gov.in
          </a>
          <a
            href="https://www.scholarships.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-navy-500 transition-colors"
          >
            NSP Portal
          </a>
          <span className="text-xs bg-saffron-100 text-saffron-700 px-2 py-0.5 rounded-full font-medium">
            Beta
          </span>
        </nav>
      </div>
    </header>
  )
}
