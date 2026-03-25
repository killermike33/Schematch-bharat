import React from 'react'
import SchemeCard from './SchemeCard'

/* ── Loading skeleton ───────────────────── */
function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-6 animate-pulse">
      <div className="flex gap-3 mb-4">
        <div className="w-7 h-7 rounded-full bg-gray-200 flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-100 rounded w-1/2" />
        </div>
        <div className="w-16 h-5 bg-gray-200 rounded-full" />
      </div>
      <div className="h-px bg-gray-100 mb-4" />
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="h-3 bg-gray-100 rounded w-1/3" />
          <div className="h-3 bg-gray-200 rounded w-full" />
          <div className="h-3 bg-gray-200 rounded w-4/5" />
          <div className="h-3 bg-gray-200 rounded w-3/5" />
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-gray-100 rounded w-1/3" />
          <div className="h-3 bg-gray-200 rounded w-full" />
          <div className="h-3 bg-gray-200 rounded w-5/6" />
        </div>
      </div>
    </div>
  )
}

/* ── Empty state ────────────────────────── */
function EmptyState({ query }) {
  return (
    <div className="text-center py-16">
      <div className="text-5xl mb-4">🔍</div>
      <h3 className="font-display font-semibold text-gray-700 text-lg mb-2">
        No matching schemes found
      </h3>
      <p className="text-gray-500 text-sm max-w-md mx-auto">
        We could not find schemes matching <em>"{query}"</em>. Try adding more details
        like your state, disability status, category, or income level.
      </p>
    </div>
  )
}

/* ── Error state ────────────────────────── */
function ErrorState({ message }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
      <div className="text-3xl mb-3">⚠️</div>
      <h3 className="font-semibold text-red-700 mb-1">Something went wrong</h3>
      <p className="text-sm text-red-600">{message}</p>
      <p className="text-xs text-red-400 mt-2">
        Ensure the backend API is running on port 8000
      </p>
    </div>
  )
}

/* ── Main Results Panel ─────────────────── */
export default function ResultsPanel({ query, results, loading, error }) {
  return (
    <section className="max-w-3xl mx-auto px-4 pb-16">

      {/* Results header */}
      {!loading && !error && (
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="font-display font-semibold text-gray-800 text-lg">
              {results.length > 0
                ? `${results.length} Scheme${results.length > 1 ? 's' : ''} Found`
                : 'Search Results'
              }
            </h2>
            {query && (
              <p className="text-xs text-gray-400 mt-0.5">
                For: "<span className="text-gray-600">{query}</span>"
              </p>
            )}
          </div>

          {results.length > 0 && (
            <div className="text-xs bg-green-50 text-green-700 border border-green-200
                            px-3 py-1 rounded-full font-medium">
              ✓ Results ranked by relevance
            </div>
          )}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
            <svg className="w-4 h-4 animate-spin text-saffron-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z" />
            </svg>
            Searching government scheme database…
          </div>
          {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Error state */}
      {!loading && error && <ErrorState message={error} />}

      {/* Empty state */}
      {!loading && !error && results.length === 0 && query && (
        <EmptyState query={query} />
      )}

      {/* Results list */}
      {!loading && !error && results.length > 0 && (
        <div className="space-y-4">
          {results.map((scheme, i) => (
            <SchemeCard key={scheme.scheme_id || i} scheme={scheme} rank={i + 1} />
          ))}

          {/* Disclaimer */}
          <div className="mt-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
            <p className="text-xs text-amber-700 leading-relaxed">
              <span className="font-semibold">Disclaimer:</span> These results are AI-generated suggestions
              based on official government scheme documents. Always verify eligibility on the official portal
              before applying. Scheme rules may change over time.
            </p>
          </div>
        </div>
      )}
    </section>
  )
}
