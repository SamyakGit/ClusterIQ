import { useQuery } from '@tanstack/react-query'
import { fetchClusters } from '../services/api'
import { Activity, Server, Clock, AlertCircle } from 'lucide-react'

function ClustersView() {
  const { data: clusters, isLoading, error } = useQuery({
    queryKey: ['clusters'],
    queryFn: fetchClusters,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading clusters...</div>
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        Error loading clusters: {error.message}
      </div>
    )
  }

  const getStateColor = (state) => {
    switch (state) {
      case 'RUNNING':
        return 'text-green-700 bg-green-100'
      case 'TERMINATED':
        return 'text-gray-700 bg-gray-100'
      case 'PENDING':
        return 'text-yellow-700 bg-yellow-100'
      case 'ERROR':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Databricks Clusters</h1>
          <p className="mt-2 text-sm text-gray-600">Monitor and manage your Databricks compute clusters</p>
        </div>
        <div className="text-sm font-medium text-gray-700 bg-gray-100 px-4 py-2 rounded-md">
          Total: {clusters?.length || 0} clusters
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clusters?.map((cluster) => (
          <div
            key={cluster.cluster_id}
            className="dxc-card hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center">
                <Server className="h-5 w-5 mr-2 text-primary-600" />
                <h3 className="font-semibold text-lg text-gray-900">{cluster.cluster_name}</h3>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getStateColor(
                  cluster.state
                )}`}
              >
                {cluster.state || 'UNKNOWN'}
              </span>
            </div>

            <div className="space-y-3">
              <div className="flex items-center text-sm">
                <Activity className="h-4 w-4 mr-2 text-gray-500" />
                <span className="text-gray-700">
                  Workers: <span className="font-semibold text-gray-900">{cluster.num_workers || 0}</span>
                </span>
              </div>

              {cluster.autoscale && (
                <div className="text-sm text-gray-600">
                  Autoscale: {cluster.autoscale.min_workers || 0} -{' '}
                  {cluster.autoscale.max_workers || 0} workers
                </div>
              )}

              <div className="text-sm text-gray-600 space-y-1">
                <div>Node Type: <span className="font-medium text-gray-900">{cluster.node_type_id || 'N/A'}</span></div>
                <div>Spark: <span className="font-medium text-gray-900">{cluster.spark_version || 'N/A'}</span></div>
              </div>

              {cluster.cluster_cores && (
                <div className="text-sm text-gray-600">
                  Cores: <span className="font-medium text-gray-900">{cluster.cluster_cores}</span>
                </div>
              )}

              {cluster.cluster_memory_mb && (
                <div className="text-sm text-gray-600">
                  Memory: <span className="font-medium text-gray-900">{(cluster.cluster_memory_mb / 1024).toFixed(1)} GB</span>
                </div>
              )}

              {cluster.autotermination_minutes && (
                <div className="flex items-center text-sm text-yellow-700">
                  <Clock className="h-4 w-4 mr-1" />
                  Auto-terminate: {cluster.autotermination_minutes} min
                </div>
              )}

              {cluster.last_activity_time && (
                <div className="text-xs text-gray-500 mt-2">
                  Last activity: {new Date(cluster.last_activity_time / 1000).toLocaleString()}
                </div>
              )}

              {cluster.state === 'RUNNING' && cluster.num_workers > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-center text-yellow-700 text-sm">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    <span>Monitor for idle time</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {(!clusters || clusters.length === 0) && (
        <div className="text-center py-12 text-gray-500">
          No clusters found
        </div>
      )}
    </div>
  )
}

export default ClustersView

