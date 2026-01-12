"""Flask backend for ClusterIQ using direct HTTP requests."""
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import List, Dict, Any
import logging
from datetime import datetime

from config import settings
from databricks_client import DatabricksClient
from ai_agent import ClusterIQAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=settings.cors_origins)

# Initialize clients
databricks_client = None
ai_agent = None

# Cache for analysis results
analysis_cache = {}
cache_timestamp = None


# Initialize clients on startup
try:
    if settings.databricks_host and settings.databricks_token:
        databricks_client = DatabricksClient(
            host=settings.databricks_host,
            token=settings.databricks_token
        )
        logger.info("Databricks client initialized")
    
    if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment_name:
        ai_agent = ClusterIQAgent(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_api_key=settings.azure_openai_api_key,
            azure_deployment_name=settings.azure_openai_deployment_name,
            model=settings.openai_model
        )
        logger.info("AI agent initialized with Azure OpenAI")
    elif settings.openai_api_key:
        ai_agent = ClusterIQAgent(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        logger.info("AI agent initialized")
except Exception as e:
    logger.error(f"Error during startup: {str(e)}")


@app.route("/")
def root():
    """Root endpoint."""
    return jsonify({
        "service": "ClusterIQ API",
        "version": "1.0.0",
        "status": "running"
    })


@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "databricks_configured": databricks_client is not None,
        "ai_configured": ai_agent is not None,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    """Fetch all Databricks jobs."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        jobs = databricks_client.get_all_jobs()
        return jsonify(jobs)
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs/<int:job_id>/runs", methods=["GET"])
def get_job_runs(job_id):
    """Fetch runs for a specific job."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        limit = request.args.get("limit", 50, type=int)
        runs = databricks_client.get_job_runs(job_id=job_id, limit=limit)
        return jsonify(runs)
    except Exception as e:
        logger.error(f"Error fetching job runs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/clusters", methods=["GET"])
def get_clusters():
    """Fetch all Databricks clusters."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        logger.info("API: Fetching clusters...")
        clusters = databricks_client.get_all_clusters()
        logger.info(f"API: Returning {len(clusters)} clusters")
        return jsonify(clusters)
    except Exception as e:
        logger.error(f"Error fetching clusters: {str(e)}", exc_info=True)
        return jsonify([{"error": str(e), "message": "Failed to fetch clusters"}]), 500


@app.route("/api/clusters/<cluster_id>/metrics", methods=["GET"])
def get_cluster_metrics(cluster_id):
    """Fetch metrics for a specific cluster."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        metrics = databricks_client.get_cluster_metrics(cluster_id)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error fetching cluster metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze_jobs_and_clusters():
    """Analyze jobs and clusters to identify cost leaks."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    if not ai_agent:
        return jsonify({"error": "AI agent not configured"}), 503
    
    try:
        # Fetch data
        logger.info("Fetching jobs and clusters...")
        jobs = databricks_client.get_all_jobs()
        clusters = databricks_client.get_all_clusters()
        
        # Fetch runs for each job (limit to recent runs)
        job_runs = {}
        for job in jobs[:10]:  # Limit to first 10 jobs for performance
            job_id = job.get("job_id")
            if job_id:
                runs = databricks_client.get_job_runs(job_id=job_id, limit=10)
                job_runs[job_id] = runs
        
        # Perform AI analysis
        logger.info("Performing AI analysis...")
        recommendations = ai_agent.analyze_jobs_and_clusters(
            jobs=jobs,
            clusters=clusters,
            job_runs=job_runs
        )
        
        # Update cache
        global analysis_cache, cache_timestamp
        analysis_cache = {
            "recommendations": recommendations,
            "jobs_count": len(jobs),
            "clusters_count": len(clusters),
            "timestamp": datetime.utcnow().isoformat()
        }
        cache_timestamp = datetime.utcnow()
        
        return jsonify({
            "recommendations": recommendations,
            "summary": {
                "total_jobs": len(jobs),
                "total_clusters": len(clusters),
                "recommendations_count": len(recommendations),
                "timestamp": cache_timestamp.isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    """Get cached recommendations."""
    if not analysis_cache:
        return jsonify({"error": "No analysis available. Run /api/analyze first."}), 404
    
    return jsonify(analysis_cache)


@app.route("/api/recommendations/real-time", methods=["GET"])
def get_recommendations_realtime():
    """Get real-time recommendations (triggers fresh analysis)."""
    if not databricks_client or not ai_agent:
        return jsonify({"error": "Services not configured"}), 503
    
    try:
        # Fetch fresh data
        jobs = databricks_client.get_all_jobs()
        clusters = databricks_client.get_all_clusters()
        
        # Quick analysis (limited scope for real-time)
        job_runs = {}
        for job in jobs[:5]:  # Limit for real-time performance
            job_id = job.get("job_id")
            if job_id:
                runs = databricks_client.get_job_runs(job_id=job_id, limit=5)
                job_runs[job_id] = runs
        
        recommendations = ai_agent.analyze_jobs_and_clusters(
            jobs=jobs,
            clusters=clusters,
            job_runs=job_runs
        )
        
        return jsonify({
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat(),
            "real_time": True
        })
    
    except Exception as e:
        logger.error(f"Error in real-time analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get overall statistics."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        jobs = databricks_client.get_all_jobs()
        clusters = databricks_client.get_all_clusters()
        
        running_clusters = [c for c in clusters if c.get("state") == "RUNNING"]
        
        return jsonify({
            "total_jobs": len(jobs),
            "total_clusters": len(clusters),
            "running_clusters": len(running_clusters),
            "idle_clusters": len([c for c in running_clusters if c.get("num_workers", 0) > 0]),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug/clusters", methods=["GET"])
def debug_clusters():
    """Debug endpoint to test cluster fetching."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        logger.info("Debug: Testing cluster fetching...")
        clusters = databricks_client.get_all_clusters()
        
        return jsonify({
            "processed_clusters_count": len(clusters),
            "clusters": clusters,
            "client_host": databricks_client.host,
        })
    
    except Exception as e:
        logger.error(f"Debug error: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "client_host": databricks_client.host if databricks_client else None,
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=settings.backend_port,
        debug=True
    )
