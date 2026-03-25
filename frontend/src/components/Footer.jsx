import React from 'react'

export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto no-print">
      {/* Tricolor bottom bar */}
      <div className="tricolor-bar w-full" />

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid md:grid-cols-3 gap-8">

          {/* About */}
          <div>
            <h4 className="font-display font-semibold text-gray-800 mb-2">
              SchemeMatch Bharat
            </h4>
            <p className="text-sm text-gray-500 leading-relaxed">
              An AI-powered civic tool to help Indian citizens discover
              government schemes, scholarships, and fellowships they qualify for.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-3">
              Official Portals
            </h4>
            <ul className="space-y-1.5 text-sm">
              {[
                { label: 'National Scholarship Portal', href: 'https://www.scholarships.gov.in' },
                { label: 'DEPwD – Disability Schemes',  href: 'https://depwd.gov.in' },
                { label: 'UGC Scholarships',            href: 'https://www.ugc.ac.in' },
                { label: 'AICTE Pragati Scheme',        href: 'https://www.aicte-india.org' },
                { label: 'India.gov.in',                href: 'https://www.india.gov.in' },
              ].map(link => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-500 hover:text-navy-500 transition-colors"
                    style={{ '--tw-text-opacity': 1 }}
                  >
                    ↗ {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Disclaimer */}
          <div>
            <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-3">
              Important Note
            </h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              This platform is for informational purposes only. Scheme data is
              sourced from official government documents. Always verify eligibility
              directly on the official portal before applying.
              <br /><br />
              Data sourced from: Ministry of Social Justice & Empowerment,
              UGC, AICTE, Ministry of Education — Government of India.
            </p>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-100 mt-8 pt-4 flex flex-col md:flex-row
                        items-center justify-between gap-2 text-xs text-gray-400">
          <span>© {year} SchemeMatch Bharat · Built with ❤️ for Indian Citizens</span>
          <span className="flex items-center gap-1">
            <span className="text-orange-500">◼</span>
            <span className="text-white bg-gray-300 px-0.5">◼</span>
            <span className="text-green-600">◼</span>
            Data sourced from official Government of India documents
          </span>
        </div>
      </div>
    </footer>
  )
}
