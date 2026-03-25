import React, { useState } from 'react'
import Header from './components/Header'
import Hero from './components/Hero'
import SearchBox from './components/SearchBox'
import ResultsPanel from './components/ResultsPanel'
import Footer from './components/Footer'
import { searchSchemes } from './services/api'

export default function App() {
  const [query, setQuery]       = useState('')
  const [results, setResults]   = useState([])
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (userQuery) => {
    if (!userQuery.trim()) return

    setLoading(true)
    setError(null)
    setSearched(true)
    setResults([])
    setQuery(userQuery)

    try {
      const data = await searchSchemes(userQuery)
      setResults(data.results || [])
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to connect to the server. Please ensure the backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setQuery('')
    setResults([])
    setError(null)
    setSearched(false)
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Top tricolor stripe */}
      <div className="tricolor-bar w-full" />

      <Header />

      <main className="flex-1">
        {/* Hero + Search always visible */}
        <Hero searched={searched} />

        <div className="max-w-3xl mx-auto px-4 pb-6">
          <SearchBox
            onSearch={handleSearch}
            loading={loading}
            onReset={searched ? handleReset : null}
          />
        </div>

        {/* Results section */}
        {searched && (
          <ResultsPanel
            query={query}
            results={results}
            loading={loading}
            error={error}
          />
        )}
      </main>

      <Footer />
    </div>
  )
}
