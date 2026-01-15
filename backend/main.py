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
    
    try:
        # Fetch data
        logger.info("Fetching jobs and clusters...")
        jobs = databricks_client.get_all_jobs()
        clusters = databricks_client.get_all_clusters()
        logger.info(f"Fetched: {len(jobs)} jobs, {len(clusters)} clusters")
        
        recommendations = []
        analysis_type = "rule-based"
        
        # Always start with rule-based analysis
        logger.info("Performing rule-based analysis on clusters and jobs...")
        try:
            # Import the basic analysis function
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from simple_server import perform_basic_analysis
            
            basic_recommendations = perform_basic_analysis(jobs, clusters)
            recommendations.extend(basic_recommendations)
            logger.info(f"Rule-based analysis generated {len(basic_recommendations)} recommendations")
        except Exception as basic_error:
            logger.error(f"Error in rule-based analysis: {str(basic_error)}")
            # Create basic recommendations manually if import fails
            for cluster in clusters:
                if cluster.get("state") == "RUNNING":
                    recommendations.append({
                        "id": f"rec_{len(recommendations)}",
                        "type": "cost_leak",
                        "severity": "medium",
                        "title": f"Running cluster: {cluster.get('cluster_name', 'Unknown')}",
                        "description": f"Cluster is running. Monitor for idle time and consider auto-termination if not actively used.",
                        "resource_type": "cluster",
                        "resource_id": cluster.get("cluster_id"),
                        "estimated_savings": "Medium - depends on idle time",
                        "risk": "Low",
                    })
            for job in jobs:
                if len(job.get("settings", {}).get("tasks", [])) == 0:
                    recommendations.append({
                        "id": f"rec_{len(recommendations)}",
                        "type": "optimization",
                        "severity": "low",
                        "title": f"Job with no tasks: {job.get('job_name', 'Unknown')}",
                        "description": "Job has no configured tasks. Consider reviewing job configuration.",
                        "resource_type": "job",
                        "resource_id": job.get("job_id"),
                        "estimated_savings": "N/A",
                        "risk": "Low",
                    })
        
        # Try AI analysis if available (enhances the recommendations)
        if ai_agent:
            try:
                logger.info("Attempting AI-enhanced analysis...")
                # Fetch runs for each job (limit to recent runs)
                job_runs = {}
                for job in jobs[:10]:  # Limit to first 10 jobs for performance
                    job_id = job.get("job_id")
                    if job_id:
                        try:
                            runs = databricks_client.get_job_runs(job_id=job_id, limit=10)
                            job_runs[job_id] = runs
                        except Exception as run_error:
                            logger.warning(f"Could not fetch runs for job {job_id}: {str(run_error)}")
                
                # Perform AI analysis
                ai_recommendations = ai_agent.analyze_jobs_and_clusters(
                    jobs=jobs,
                    clusters=clusters,
                    job_runs=job_runs
                )
                
                # If AI analysis succeeds and returns recommendations, use it
                if ai_recommendations and len(ai_recommendations) > 0:
                    recommendations = ai_recommendations
                    analysis_type = "ai"
                    logger.info(f"AI analysis completed: {len(recommendations)} recommendations")
                else:
                    logger.info("AI analysis returned no recommendations, using rule-based results")
            except Exception as ai_error:
                logger.warning(f"AI analysis failed, using rule-based results: {str(ai_error)}")
                # Continue with rule-based recommendations
        else:
            logger.info("AI agent not available, using rule-based analysis")
        
        # Ensure we have at least some recommendations
        if not recommendations:
            recommendations = [{
                "id": "rec_no_data",
                "type": "info",
                "severity": "low",
                "title": "Analysis Complete",
                "description": f"Analyzed {len(jobs)} jobs and {len(clusters)} clusters. No immediate optimization opportunities detected.",
                "estimated_savings": "Continue monitoring",
                "risk": "None",
            }]
        
        # Update cache
        global analysis_cache, cache_timestamp
        analysis_cache = {
            "recommendations": recommendations,
            "jobs_count": len(jobs),
            "clusters_count": len(clusters),
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_type": analysis_type
        }
        cache_timestamp = datetime.utcnow()
        
        return jsonify({
            "recommendations": recommendations,
            "summary": {
                "total_jobs": len(jobs),
                "total_clusters": len(clusters),
                "recommendations_count": len(recommendations),
                "analysis_type": analysis_type,
                "timestamp": cache_timestamp.isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    """Get cached recommendations."""
    if not analysis_cache or not analysis_cache.get("recommendations"):
        return jsonify({
            "recommendations": [],
            "has_analysis": False,
            "message": "No analysis available. Run /api/analyze first."
        }), 200
    
    return jsonify({
        **analysis_cache,
        "has_analysis": True
    })


@app.route("/api/recommendations/real-time", methods=["GET"])
def get_recommendations_realtime():
    """Get real-time recommendations (returns cached analysis if available)."""
    # First check if we have cached analysis
    if analysis_cache and analysis_cache.get("recommendations"):
        return jsonify({
            **analysis_cache,
            "real_time": True,
            "has_analysis": True,
            "timestamp": cache_timestamp.isoformat() if cache_timestamp else datetime.utcnow().isoformat()
        })
    
    # If no cache, check if services are configured
    if not databricks_client:
        return jsonify({
            "recommendations": [],
            "timestamp": datetime.utcnow().isoformat(),
            "real_time": True,
            "has_analysis": False,
            "message": "No analysis available. Databricks client not configured. Please configure Databricks credentials and run an analysis first."
        }), 200
    
    if not ai_agent:
        return jsonify({
            "recommendations": [],
            "timestamp": datetime.utcnow().isoformat(),
            "real_time": True,
            "has_analysis": False,
            "message": "No analysis available. AI agent not configured. Please configure OpenAI/Azure OpenAI credentials and run an analysis first."
        }), 200
    
    # If no cache but services are configured, return message to run analysis
    return jsonify({
        "recommendations": [],
        "timestamp": datetime.utcnow().isoformat(),
        "real_time": True,
        "has_analysis": False,
        "message": "No analysis available. Please run an analysis first."
    }), 200


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


@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Get summary metrics including cost savings and optimization statistics."""
    try:
        # Get recommendations from cache
        recommendations = analysis_cache.get("recommendations", []) if analysis_cache else []
        
        # Calculate metrics
        total_recommendations = len(recommendations)
        
        # Calculate cost savings
        total_savings = 0
        savings_by_type = {"cost_leak": 0, "value_leak": 0, "optimization_opportunity": 0}
        
        for rec in recommendations:
            savings_str = rec.get("estimated_savings", "")
            if savings_str:
                # Try to extract numeric value (handles "$500/month", "30%", etc.)
                import re
                # Extract numbers (including decimals)
                numbers = re.findall(r'\d+\.?\d*', savings_str)
                if numbers:
                    savings_value = float(numbers[0])
                    # If it's a percentage, estimate based on average (rough calculation)
                    if '%' in savings_str.lower():
                        savings_value = savings_value * 100  # Rough estimate: treat % as base amount
                    total_savings += savings_value
                    
                    # Track by type
                    rec_type = rec.get("type", "optimization_opportunity")
                    if rec_type in savings_by_type:
                        savings_by_type[rec_type] += savings_value
        
        # Count by type
        by_type = {
            "cost_leak": len([r for r in recommendations if r.get("type") == "cost_leak"]),
            "value_leak": len([r for r in recommendations if r.get("type") == "value_leak"]),
            "optimization_opportunity": len([r for r in recommendations if r.get("type") == "optimization_opportunity"])
        }
        
        # Count by severity
        by_severity = {
            "high": len([r for r in recommendations if r.get("severity") == "high"]),
            "medium": len([r for r in recommendations if r.get("severity") == "medium"]),
            "low": len([r for r in recommendations if r.get("severity") == "low"])
        }
        
        # Count unique jobs identified for optimization
        job_ids = set()
        for rec in recommendations:
            if rec.get("resource_type") == "job":
                resource_id = rec.get("resource_id")
                if resource_id:
                    job_ids.add(str(resource_id))
        
        # Count unique resources by type
        resources_by_type = {}
        for rec in recommendations:
            res_type = rec.get("resource_type", "unknown")
            if res_type not in resources_by_type:
                resources_by_type[res_type] = set()
            resource_id = rec.get("resource_id")
            if resource_id:
                resources_by_type[res_type].add(str(resource_id))
        
        resources_count = {k: len(v) for k, v in resources_by_type.items()}
        
        # Get analysis metadata
        analysis_timestamp = cache_timestamp.isoformat() if cache_timestamp else None
        jobs_analyzed = analysis_cache.get("jobs_count", 0) if analysis_cache else 0
        clusters_analyzed = analysis_cache.get("clusters_count", 0) if analysis_cache else 0
        
        return jsonify({
            "total_cost_savings": round(total_savings, 2),
            "total_cost_savings_formatted": f"${total_savings:,.2f}",
            "total_recommendations": total_recommendations,
            "jobs_identified": len(job_ids),
            "resources_optimized": sum(resources_count.values()),
            "by_type": by_type,
            "by_severity": by_severity,
            "savings_by_type": {k: round(v, 2) for k, v in savings_by_type.items()},
            "resources_by_type": resources_count,
            "analysis_metadata": {
                "timestamp": analysis_timestamp,
                "jobs_analyzed": jobs_analyzed,
                "clusters_analyzed": clusters_analyzed,
                "has_analysis": len(recommendations) > 0
            },
            "success_metrics": {
                "recommendations_generated": total_recommendations,
                "high_priority_actions": by_severity["high"],
                "potential_monthly_savings": round(total_savings, 2),
                "optimization_coverage": f"{len(job_ids)} jobs, {sum(resources_count.values())} resources"
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return jsonify({
            "error": str(e),
            "total_cost_savings": 0,
            "total_recommendations": 0,
            "jobs_identified": 0,
            "has_analysis": False
        }), 500


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
