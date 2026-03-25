import React, { useState } from 'react'

/* ── Category color mapping ─────────────── */
const CATEGORY_COLORS = {
  'Disability':           { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200' },
  'OBC/EBC/DNT':          { bg: 'bg-orange-50',  text: 'text-orange-700', border: 'border-orange-200' },
  'North Eastern Region': { bg: 'bg-green-50',   text: 'text-green-700',  border: 'border-green-200' },
  'Women/Girls':          { bg: 'bg-pink-50',    text: 'text-pink-700',   border: 'border-pink-200' },
  'Merit-Based / General':{ bg: 'bg-purple-50',  text: 'text-purple-700', border: 'border-purple-200' },
}

const DEFAULT_COLORS = { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' }

/* ── Small icons ────────────────────────── */
const DocIcon = () => (
  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0121 9.414V19a2 2 0 01-2 2z" />
  </svg>
)

const OfficeIcon = () => (
  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
  </svg>
)

const LinkIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
)

const ChevronIcon = ({ open }) => (
  <svg
    className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`}
    fill="none" stroke="currentColor" viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
)

/* ── Relevance badge ────────────────────── */
function RelevanceBadge({ score }) {
  const pct = Math.round(score * 100)
  let cls = 'relevance-low'
  if (pct >= 70) cls = 'relevance-high'
  else if (pct >= 40) cls = 'relevance-medium'

  return (
    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${cls}`}>
      {pct}% match
    </span>
  )
}

/* ── Main Card ──────────────────────────── */
export default function SchemeCard({ scheme, rank }) {
  const [expanded, setExpanded] = useState(false)
  const colors = CATEGORY_COLORS[scheme.category] || DEFAULT_COLORS

  const docs = Array.isArray(scheme.required_documents) ? scheme.required_documents : []
  const eligibility = Array.isArray(scheme.eligibility_conditions) ? scheme.eligibility_conditions : []
  const financial = scheme.financial_assistance && typeof scheme.financial_assistance === 'object'
    ? scheme.financial_assistance : {}

  return (
    <div className="scheme-card bg-white rounded-2xl border border-gray-200 shadow-card
                    hover:shadow-card-hover hover:-translate-y-0.5
                    transition-all duration-200 overflow-hidden">

      {/* ── Card Header ───────────────────── */}
      <div className="px-6 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3">
          {/* Rank + Name */}
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-navy-50 text-navy-500
                             flex items-center justify-center text-xs font-bold border border-navy-100"
                  style={{ color: '#002366', backgroundColor: '#eef2ff', borderColor: '#c7d2fe' }}>
              {rank}
            </span>
            <div className="min-w-0">
              <h3 className="font-display font-semibold text-gray-900 text-base leading-snug line-clamp-2">
                {scheme.scheme_name}
              </h3>
              {scheme.issuing_body && (
                <p className="text-xs text-gray-400 mt-0.5 truncate">{scheme.issuing_body}</p>
              )}
            </div>
          </div>

          {/* Badges */}
          <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
            <RelevanceBadge score={scheme.relevance_score} />
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${colors.bg} ${colors.text} ${colors.border}`}>
              {scheme.category}
            </span>
          </div>
        </div>
      </div>

      {/* ── Divider ───────────────────────── */}
      <div className="h-px bg-gray-100 mx-6" />

      {/* ── Documents & Office ────────────── */}
      <div className="px-6 py-4 grid md:grid-cols-2 gap-4">
        {/* Required Documents */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <DocIcon />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Required Documents
            </span>
          </div>
          {docs.length > 0 ? (
            <ul className="space-y-1">
              {docs.slice(0, 4).map((doc, i) => (
                <li key={i} className="flex items-start gap-1.5 text-sm text-gray-600">
                  <span className="text-saffron-500 mt-0.5 flex-shrink-0">•</span>
                  <span className="line-clamp-2">{doc}</span>
                </li>
              ))}
              {docs.length > 4 && (
                <li className="text-xs text-gray-400 pl-3">
                  +{docs.length - 4} more documents
                </li>
              )}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">See official portal for details</p>
          )}
        </div>

        {/* Office to Visit */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <OfficeIcon />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Where to Apply
            </span>
          </div>
          <p className="text-sm text-gray-600 line-clamp-4">
            {scheme.office_to_visit || 'Refer to official portal'}
          </p>
        </div>
      </div>

      {/* ── Expandable section ────────────── */}
      <div className="border-t border-gray-100">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between px-6 py-3 text-xs font-medium
                     text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <span>
            {expanded ? 'Hide' : 'Show'} eligibility & financial details
          </span>
          <ChevronIcon open={expanded} />
        </button>

        {expanded && (
          <div className="px-6 pb-5 space-y-4 animate-fade-in">
            {/* Eligibility */}
            {eligibility.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Eligibility Conditions
                </p>
                <ul className="space-y-1.5">
                  {eligibility.map((cond, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Financial assistance */}
            {Object.keys(financial).length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Financial Assistance
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(financial).map(([key, val]) => (
                    <div key={key} className="bg-gray-50 rounded-lg px-3 py-2">
                      <div className="text-xs text-gray-400 capitalize">
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="text-sm font-medium text-gray-700">{val}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Footer: Apply button ──────────── */}
      <div className="px-6 pb-5 flex items-center justify-between">
        <span className="text-xs text-gray-400">Scheme ID: {scheme.scheme_id}</span>
        <a
          href={scheme.application_link}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-white
                     rounded-xl transition-colors shadow-sm hover:opacity-90"
          style={{ backgroundColor: '#FF9933' }}
        >
          Apply Now
          <LinkIcon />
        </a>
      </div>
    </div>
  )
}
