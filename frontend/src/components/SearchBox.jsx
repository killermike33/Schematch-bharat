import React, { useState, useRef } from 'react'

const SearchIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
  </svg>
)

const SpinnerIcon = () => (
  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10"
      stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor"
      d="M4 12a8 8 0 0 1 8-8V0C5.37 0 0 5.37 0 12h4z" />
  </svg>
)

export default function SearchBox({ onSearch, loading, onReset }) {
  const [input, setInput] = useState('')
  const textareaRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !loading) {
      onSearch(input.trim())
    }
  }

  const handleKeyDown = (e) => {
    // Submit on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e)
    }
  }

  return (
    <div className="mt-6">
      <form onSubmit={handleSubmit}>
        <div className="bg-white rounded-2xl border border-gray-200 shadow-card overflow-hidden
                        focus-within:border-saffron-400 focus-within:shadow-card-hover transition-all duration-200">

          {/* Label */}
          <label htmlFor="user-query" className="block px-5 pt-4 text-xs font-semibold text-gray-400 uppercase tracking-widest">
            Describe your situation
          </label>

          {/* Textarea */}
          <textarea
            id="user-query"
            ref={textareaRef}
            rows={3}
            className="search-input w-full px-5 py-3 text-gray-800 font-body text-base
                       bg-transparent border-0 resize-none placeholder-gray-300
                       focus:outline-none"
            placeholder="e.g. I am a girl student from Nagaland pursuing BTech at NIT. Family income is 3 lakh per year..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            maxLength={500}
          />

          {/* Footer row */}
          <div className="px-5 pb-4 flex items-center justify-between">
            <span className="text-xs text-gray-300">
              {input.length}/500 · Press Ctrl+Enter to search
            </span>

            <div className="flex gap-2">
              {onReset && (
                <button
                  type="button"
                  onClick={() => { setInput(''); onReset() }}
                  className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700
                             border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
                >
                  Clear
                </button>
              )}

              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white
                           bg-navy-500 hover:bg-navy-600 disabled:bg-gray-300 disabled:cursor-not-allowed
                           rounded-xl transition-colors shadow-sm"
                style={{ backgroundColor: loading || !input.trim() ? undefined : '#002366' }}
              >
                {loading ? (
                  <>
                    <SpinnerIcon />
                    Searching…
                  </>
                ) : (
                  <>
                    <SearchIcon />
                    Check Eligibility
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Helper text */}
      <p className="mt-2 text-xs text-center text-gray-400">
        Include: disability status · caste category · state · income · course level
      </p>
    </div>
  )
}
