/**
 * api.js
 * ------
 * Centralised API service for the SchemeMatch Bharat frontend.
 * All backend calls go through this module.
 */

import axios from 'axios'

// ── Base URL ────────────────────────────────────────────────
// In development, Vite proxies /api → http://localhost:8000
// In production, set VITE_API_URL env variable
const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,          // 30s timeout (embedding can be slow first time)
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request interceptor (add auth token here if needed later) ──
client.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// ── Response interceptor (normalise errors) ─────────────────
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Unknown error'
    return Promise.reject({ ...error, message })
  }
)

// ── API methods ─────────────────────────────────────────────

/**
 * POST /search
 * Send a user query and receive ranked matching schemes.
 *
 * @param {string} query    - Natural language description of user's situation
 * @param {number} [topK=5] - Number of results to return
 * @returns {Promise<SearchResponse>}
 */
export const searchSchemes = (query, topK = 5) =>
  client.post('/search', { query, top_k: topK })

/**
 * GET /schemes
 * Retrieve all schemes in the database (for browsing / admin).
 *
 * @returns {Promise<Array>}
 */
export const listAllSchemes = () =>
  client.get('/schemes')

/**
 * GET /health
 * Check backend + DB status.
 *
 * @returns {Promise<HealthResponse>}
 */
export const checkHealth = () =>
  client.get('/health')
