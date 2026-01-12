import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const fetchJobs = async () => {
  const response = await api.get('/api/jobs')
  return response.data
}

export const fetchJobRuns = async (jobId) => {
  const response = await api.get(`/api/jobs/${jobId}/runs`)
  return response.data
}

export const fetchClusters = async () => {
  const response = await api.get('/api/clusters')
  return response.data
}

export const fetchClusterMetrics = async (clusterId) => {
  const response = await api.get(`/api/clusters/${clusterId}/metrics`)
  return response.data
}

export const analyzeJobsAndClusters = async () => {
  const response = await api.post('/api/analyze')
  return response.data
}

export const fetchRecommendations = async () => {
  const response = await api.get('/api/recommendations')
  return response.data
}

export const fetchRecommendationsRealtime = async () => {
  const response = await api.get('/api/recommendations/real-time')
  return response.data
}

export const fetchStats = async () => {
  const response = await api.get('/api/stats')
  return response.data
}

export default api

