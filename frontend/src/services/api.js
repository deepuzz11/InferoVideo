import axios from 'axios'

const BASE = '/api/v1'
const api = axios.create({ baseURL: BASE, timeout: 30000 })

export const processVideo   = (url) => api.post('/process', { url })
export const getJob         = (id)  => api.get(`/jobs/${id}`)
export const listJobs       = (limit=20) => api.get(`/jobs?limit=${limit}`)
export const searchJob      = (id, query, top_k=5, backend='tfidf') =>
  api.post(`/jobs/${id}/search`, { query, top_k, backend })
export const getChapters    = (id)  => api.get(`/jobs/${id}/chapters`)
export const getHighlights  = (id)  => api.get(`/jobs/${id}/highlights`)
export const getSummary     = (id)  => api.get(`/jobs/${id}/summary`)
export const healthCheck    = ()    => api.get('/health')

export default api
