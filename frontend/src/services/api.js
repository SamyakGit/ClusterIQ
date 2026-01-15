import axios from 'axios'

// Use Vite proxy in development, or direct URL in production
// In dev mode, use empty string so requests go through Vite proxy
// In production, use full backend URL
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '' : 'http://localhost:8000')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error.message)
    if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      error.message = 'Cannot connect to backend server. Make sure the backend is running on http://localhost:8000'
    }
    return Promise.reject(error)
  }
)

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
  try {
    const response = await api.get('/api/recommendations/real-time')
    return response.data
  } catch (error) {
    // If real-time endpoint fails, try the regular recommendations endpoint
    if (error.response?.status === 404) {
      const response = await api.get('/api/recommendations')
      return {
        ...response.data,
        real_time: false
      }
    }
    throw error
  }
}

export const fetchStats = async () => {
  const response = await api.get('/api/stats')
  return response.data
}

export const fetchSQLWarehouses = async () => {
  const response = await api.get('/api/sql-warehouses')
  return response.data
}

export const fetchPools = async () => {
  const response = await api.get('/api/pools')
  return response.data
}

export const fetchVectorSearch = async () => {
  const response = await api.get('/api/vector-search')
  return response.data
}

export const fetchPolicies = async () => {
  const response = await api.get('/api/policies')
  return response.data
}

export const fetchApps = async () => {
  const response = await api.get('/api/apps')
  return response.data
}

export const fetchLakebase = async () => {
  const response = await api.get('/api/lakebase')
  return response.data
}

export const fetchAllCompute = async () => {
  const response = await api.get('/api/compute')
  return response.data
}

export const fetchMLJobs = async () => {
  const response = await api.get('/api/ml-jobs')
  return response.data
}

export const fetchMLflowExperiments = async () => {
  const response = await api.get('/api/mlflow-experiments')
  return response.data
}

export const fetchMLflowModels = async () => {
  const response = await api.get('/api/mlflow-models')
  return response.data
}

export const fetchModelServing = async () => {
  const response = await api.get('/api/model-serving')
  return response.data
}

export const fetchFeatureStore = async () => {
  const response = await api.get('/api/feature-store')
  return response.data
}

export const fetchSummaryMetrics = async () => {
  const response = await api.get('/api/summary')
  return response.data
}

export default api

