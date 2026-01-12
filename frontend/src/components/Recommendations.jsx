import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchRecommendationsRealtime, analyzeJobsAndClusters } from '../services/api'
import { AlertTriangle, TrendingDown, DollarSign, Clock, RefreshCw } from 'lucide-react'

function Recommendations() {
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['recommendations-realtime'],
    queryFn: fetchRecommendationsRealtime,
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false,
  })

  const handleManualAnalyze = async () => {
    try {
      await analyzeJobsAndClusters()
      refetch()
    } catch (error) {
      console.error('Analysis failed:', error)
    }
  }

  const recommendations = data?.recommendations || []

  const groupedByType = recommendations.reduce((acc, rec) => {
    const type = rec.type || 'other'
    if (!acc[type]) acc[type] = []
    acc[type].push(rec)
    return acc
  }, {})

  const groupedBySeverity = recommendations.reduce((acc, rec) => {
    const severity = rec.severity || 'low'
    if (!acc[severity]) acc[severity] = []
    acc[severity].push(rec)
    return acc
  }, {})

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Recommendations</h1>
          <p className="mt-2 text-sm text-gray-600">AI-powered optimization suggestions for your Databricks infrastructure</p>
        </div>
        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Auto-refresh</span>
          </label>
          {autoRefresh && (
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-white border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
              <option value={300}>5min</option>
            </select>
          )}
          <button
            onClick={handleManualAnalyze}
            className="dxc-button-primary flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Analyze Now
          </button>
        </div>
      </div>

      {data?.timestamp && (
        <div className="bg-blue-50 border-l-4 border-primary-600 rounded-r-lg p-4">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Last updated:</span> {new Date(data.timestamp).toLocaleString()}
            {data.real_time && ' (Real-time)'}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12">Loading recommendations...</div>
      ) : recommendations.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          No recommendations available. Click "Analyze Now" to generate recommendations.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="dxc-card bg-red-50 border-red-200">
              <div className="flex items-center mb-3">
                <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                <span className="font-semibold text-gray-900">High Priority</span>
              </div>
              <div className="text-3xl font-bold text-red-600">
                {groupedBySeverity.high?.length || 0}
              </div>
            </div>
            <div className="dxc-card bg-yellow-50 border-yellow-200">
              <div className="flex items-center mb-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                <span className="font-semibold text-gray-900">Medium Priority</span>
              </div>
              <div className="text-3xl font-bold text-yellow-600">
                {groupedBySeverity.medium?.length || 0}
              </div>
            </div>
            <div className="dxc-card bg-blue-50 border-blue-200">
              <div className="flex items-center mb-3">
                <AlertTriangle className="h-5 w-5 text-blue-600 mr-2" />
                <span className="font-semibold text-gray-900">Low Priority</span>
              </div>
              <div className="text-3xl font-bold text-blue-600">
                {groupedBySeverity.low?.length || 0}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {Object.entries(groupedByType).map(([type, recs]) => (
              <div key={type} className="dxc-card">
                <h2 className="text-xl font-semibold mb-6 text-gray-900 capitalize">
                  {type.replace('_', ' ')} ({recs.length})
                </h2>
                <div className="space-y-4">
                  {recs.map((rec) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function RecommendationCard({ recommendation }) {
  const severityColors = {
    high: 'border-red-500 bg-red-50',
    medium: 'border-yellow-500 bg-yellow-50',
    low: 'border-blue-500 bg-blue-50',
  }

  const severity = recommendation.severity || 'low'
  const colorClass = severityColors[severity] || severityColors.low

  return (
    <div className={`border-l-4 ${colorClass} rounded-lg p-6 bg-white shadow-sm hover:shadow-lg transition-shadow`}>
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold">
          {recommendation.title || recommendation.type || 'Recommendation'}
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            severity === 'high'
              ? 'bg-red-100 text-red-700'
              : severity === 'medium'
              ? 'bg-yellow-100 text-yellow-700'
              : 'bg-blue-100 text-blue-700'
          }`}
        >
          {severity.toUpperCase()}
        </span>
      </div>

      {recommendation.description && (
        <p className="text-gray-600 mb-4">{recommendation.description}</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {recommendation.current_config && (
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Current Configuration</h4>
            <div className="bg-gray-50 rounded p-3 text-sm border border-gray-200">
              <pre className="text-gray-700 text-xs overflow-x-auto">
                {JSON.stringify(recommendation.current_config, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {recommendation.recommended_config && (
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Recommended Configuration</h4>
            <div className="bg-gray-50 rounded p-3 text-sm border border-gray-200">
              <pre className="text-gray-700 text-xs overflow-x-auto">
                {JSON.stringify(recommendation.recommended_config, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-4">
        {recommendation.estimated_savings && (
          <div className="flex items-center text-green-700">
            <DollarSign className="h-4 w-4 mr-1" />
            <span className="text-sm font-semibold">
              Savings: {recommendation.estimated_savings}
            </span>
          </div>
        )}

        {recommendation.risk && (
          <div className="flex items-center text-yellow-700">
            <AlertTriangle className="h-4 w-4 mr-1" />
            <span className="text-sm">Risk: {recommendation.risk}</span>
          </div>
        )}

        {recommendation.resource_type && (
          <div className="flex items-center text-blue-700">
            <span className="text-sm">
              {recommendation.resource_type}: {recommendation.resource_id}
            </span>
          </div>
        )}
      </div>

      {recommendation.implementation_steps && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Implementation Steps</h4>
          <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
            {recommendation.implementation_steps.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

export default Recommendations

