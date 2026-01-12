import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchStats, analyzeJobsAndClusters, fetchRecommendations } from '../services/api'
import { Activity, Database, TrendingDown, AlertCircle, RefreshCw } from 'lucide-react'

function Dashboard() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [lastAnalysis, setLastAnalysis] = useState(null)

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: recommendations, refetch: refetchRecommendations } = useQuery({
    queryKey: ['recommendations'],
    queryFn: fetchRecommendations,
    enabled: false, // Don't fetch automatically
  })

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    try {
      await analyzeJobsAndClusters()
      setLastAnalysis(new Date().toLocaleString())
      refetchRecommendations()
      refetchStats()
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const highSeverityCount = recommendations?.recommendations?.filter(
    (r) => r.severity === 'high'
  ).length || 0

  const estimatedSavings = recommendations?.recommendations?.reduce((sum, r) => {
    const savings = parseFloat(r.estimated_savings?.replace(/[^0-9.]/g, '') || 0)
    return sum + savings
  }, 0) || 0

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-600">Monitor your Databricks infrastructure and optimization opportunities</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
          {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {lastAnalysis && (
        <div className="bg-blue-50 border-l-4 border-primary-600 rounded-r-lg p-4">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Last analysis:</span> {lastAnalysis}
          </p>
        </div>
      )}

      {statsLoading ? (
        <div className="text-center py-12 text-gray-500">Loading statistics...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Jobs"
            value={stats?.total_jobs || 0}
            icon={<Database className="h-6 w-6" />}
            color="blue"
          />
          <StatCard
            title="Total Clusters"
            value={stats?.total_clusters || 0}
            icon={<Activity className="h-6 w-6" />}
            color="green"
          />
          <StatCard
            title="Running Clusters"
            value={stats?.running_clusters || 0}
            icon={<Activity className="h-6 w-6" />}
            color="yellow"
          />
          <StatCard
            title="Idle Clusters"
            value={stats?.idle_clusters || 0}
            icon={<AlertCircle className="h-6 w-6" />}
            color="red"
          />
        </div>
      )}

      {recommendations && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="dxc-card">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-900">
              <TrendingDown className="h-5 w-5 mr-2 text-red-600" />
              High Priority Issues
            </h2>
            <div className="text-4xl font-bold text-red-600">{highSeverityCount}</div>
            <p className="text-gray-600 mt-2 text-sm">Issues requiring immediate attention</p>
          </div>

          <div className="dxc-card">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-900">
              <TrendingDown className="h-5 w-5 mr-2 text-green-600" />
              Estimated Savings
            </h2>
            <div className="text-4xl font-bold text-green-600">
              ${estimatedSavings.toFixed(2)}
            </div>
            <p className="text-gray-600 mt-2 text-sm">Potential monthly cost savings</p>
          </div>
        </div>
      )}

      {recommendations && recommendations.recommendations?.length > 0 && (
        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-6 text-gray-900">Recent Recommendations</h2>
          <div className="space-y-4">
            {recommendations.recommendations.slice(0, 5).map((rec) => (
              <div
                key={rec.id}
                className="bg-gray-50 rounded-lg p-4 border-l-4 border-primary-600 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{rec.title || rec.type}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {rec.description || 'No description available'}
                    </p>
                  </div>
                  <span
                    className={`ml-4 px-3 py-1 rounded-full text-xs font-semibold ${
                      rec.severity === 'high'
                        ? 'bg-red-100 text-red-700'
                        : rec.severity === 'medium'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {rec.severity || 'low'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    red: 'bg-red-50 border-red-200 text-red-700',
  }

  const iconColors = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
  }

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-6 dxc-card`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium mb-2 opacity-75">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
        </div>
        <div className={`${iconColors[color]} opacity-80`}>{icon}</div>
      </div>
    </div>
  )
}

export default Dashboard

