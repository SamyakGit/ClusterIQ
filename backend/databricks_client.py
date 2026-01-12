"""Databricks API client using direct HTTP requests (curl-style)."""
from typing import List, Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class DatabricksClient:
    """Client for interacting with Databricks APIs using direct HTTP requests."""
    
    def __init__(self, host: str, token: str):
        """Initialize Databricks client.
        
        Args:
            host: Databricks workspace URL
            token: Databricks personal access token
        """
        self.host = host.rstrip('/')  # Remove trailing slash
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        logger.info(f"Databricks client initialized for host: {self.host}")
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Fetch all jobs from Databricks workspace using REST API.
        
        Returns:
            List of job dictionaries with metadata
        """
        try:
            url = f"{self.host}/api/2.1/jobs/list"
            logger.info(f"Fetching jobs from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get("jobs", [])
            
            # Transform to match expected format
            job_list = []
            for job in jobs:
                job_dict = {
                    "job_id": job.get("job_id"),
                    "job_name": job.get("settings", {}).get("name", "Unknown"),
                    "created_time": job.get("created_time"),
                    "creator_user_name": job.get("creator_user_name"),
                    "settings": {
                        "timeout_seconds": job.get("settings", {}).get("timeout_seconds"),
                        "max_concurrent_runs": job.get("settings", {}).get("max_concurrent_runs"),
                        "tasks": [
                            {
                                "task_key": task.get("task_key"),
                                "description": task.get("description"),
                                "timeout_seconds": task.get("timeout_seconds"),
                                "cluster_id": task.get("existing_cluster_id"),
                                "new_cluster": task.get("new_cluster"),
                            }
                            for task in job.get("settings", {}).get("tasks", [])
                        ],
                    },
                    "schedule": job.get("settings", {}).get("schedule"),
                }
                job_list.append(job_dict)
            
            logger.info(f"Fetched {len(job_list)} jobs from Databricks")
            return job_list
        
        except Exception as e:
            logger.error(f"Error fetching jobs: {str(e)}", exc_info=True)
            return []
    
    def get_job_runs(self, job_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent runs for a specific job using REST API.
        
        Args:
            job_id: Job ID
            limit: Maximum number of runs to fetch
            
        Returns:
            List of run dictionaries
        """
        try:
            url = f"{self.host}/api/2.1/jobs/runs/list"
            params = {
                "job_id": job_id,
                "limit": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            runs_data = data.get("runs", [])
            
            runs = []
            for run in runs_data:
                start_time = run.get("start_time")
                end_time = run.get("end_time")
                duration = None
                if start_time and end_time:
                    duration = (end_time - start_time) / 1000  # Convert ms to seconds
                
                run_dict = {
                    "run_id": run.get("run_id"),
                    "job_id": run.get("job_id"),
                    "run_name": run.get("run_name"),
                    "state": {
                        "life_cycle_state": run.get("state", {}).get("life_cycle_state"),
                        "result_state": run.get("state", {}).get("result_state"),
                        "state_message": run.get("state", {}).get("state_message"),
                    },
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "cluster_instance": {
                        "cluster_id": run.get("cluster_instance", {}).get("cluster_id"),
                    } if run.get("cluster_instance") else None,
                    "tasks": [
                        {
                            "task_key": task.get("task_key"),
                            "run_id": task.get("run_id"),
                            "state": task.get("state", {}).get("life_cycle_state"),
                            "start_time": task.get("start_time"),
                            "end_time": task.get("end_time"),
                            "duration": (task.get("end_time") - task.get("start_time")) / 1000 if task.get("end_time") and task.get("start_time") else None,
                        }
                        for task in run.get("tasks", [])
                    ],
                }
                runs.append(run_dict)
            
            return runs
        
        except Exception as e:
            logger.error(f"Error fetching runs for job {job_id}: {str(e)}")
            return []
    
    def get_all_clusters(self) -> List[Dict[str, Any]]:
        """Fetch all clusters from Databricks workspace using REST API.
        
        Returns:
            List of cluster dictionaries
        """
        try:
            url = f"{self.host}/api/2.1/clusters/list"
            logger.info(f"Fetching clusters from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            clusters_data = data.get("clusters", [])
            logger.info(f"Found {len(clusters_data)} clusters in API response")
            
            clusters = []
            for cluster in clusters_data:
                try:
                    # Handle state - can be string or dict
                    state = cluster.get("state")
                    if isinstance(state, dict):
                        state = state.get("cluster_state", "UNKNOWN")
                    elif state is None:
                        state = "UNKNOWN"
                    
                    cluster_dict = {
                        "cluster_id": cluster.get("cluster_id"),
                        "cluster_name": cluster.get("cluster_name") or f"Cluster-{cluster.get('cluster_id')}",
                        "state": state,
                        "spark_version": cluster.get("spark_version"),
                        "node_type_id": cluster.get("node_type_id"),
                        "driver_node_type_id": cluster.get("driver_node_type_id"),
                        "num_workers": cluster.get("num_workers", 0),
                        "autotermination_minutes": cluster.get("autotermination_minutes"),
                        "enable_elastic_disk": cluster.get("enable_elastic_disk"),
                        "cluster_source": cluster.get("cluster_source"),
                        "start_time": cluster.get("start_time"),
                        "terminated_time": cluster.get("terminated_time"),
                        "last_activity_time": cluster.get("last_activity_time"),
                        "cluster_memory_mb": cluster.get("cluster_memory_mb"),
                        "cluster_cores": cluster.get("cluster_cores"),
                        "default_tags": cluster.get("default_tags", {}),
                        "spark_conf": cluster.get("spark_conf", {}),
                        "autoscale": {
                            "min_workers": cluster.get("autoscale", {}).get("min_workers"),
                            "max_workers": cluster.get("autoscale", {}).get("max_workers"),
                        } if cluster.get("autoscale") else None,
                    }
                    clusters.append(cluster_dict)
                    logger.info(f"Added cluster: {cluster_dict['cluster_name']} (State: {cluster_dict['state']})")
                
                except Exception as cluster_error:
                    logger.warning(f"Error processing cluster {cluster.get('cluster_id')}: {str(cluster_error)}")
                    # Add basic info even if processing fails
                    clusters.append({
                        "cluster_id": cluster.get("cluster_id"),
                        "cluster_name": cluster.get("cluster_name", f"Cluster-{cluster.get('cluster_id')}"),
                        "state": cluster.get("state", "UNKNOWN"),
                        "error": f"Could not process: {str(cluster_error)}"
                    })
            
            logger.info(f"Successfully fetched {len(clusters)} clusters from Databricks")
            return clusters
        
        except Exception as e:
            logger.error(f"Error fetching clusters: {str(e)}", exc_info=True)
            return []
    
    def get_cluster_metrics(self, cluster_id: str) -> Dict[str, Any]:
        """Fetch metrics for a specific cluster using REST API.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Dictionary with cluster metrics
        """
        try:
            url = f"{self.host}/api/2.1/clusters/get"
            params = {"cluster_id": cluster_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            cluster = response.json()
            state = cluster.get("state")
            if isinstance(state, dict):
                state = state.get("cluster_state")
            
            return {
                "cluster_id": cluster_id,
                "state": state,
                "num_workers": cluster.get("num_workers", 0),
                "cluster_cores": cluster.get("cluster_cores"),
                "cluster_memory_mb": cluster.get("cluster_memory_mb"),
            }
        
        except Exception as e:
            logger.error(f"Error fetching metrics for cluster {cluster_id}: {str(e)}")
            return {}
