"""Simple HTTP server for ClusterIQ using Python's built-in http.server."""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import logging
from datetime import datetime

from config import settings
from databricks_client import DatabricksClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
databricks_client = None
ai_agent = None
analysis_cache = {}
cache_timestamp = None

# Initialize clients
try:
    if settings.databricks_host and settings.databricks_token:
        databricks_client = DatabricksClient(
            host=settings.databricks_host,
            token=settings.databricks_token
        )
        logger.info("Databricks client initialized")
    
    # Try to initialize AI agent (optional)
    try:
        from ai_agent import ClusterIQAgent
        if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment_name:
            ai_agent = ClusterIQAgent(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_api_key=settings.azure_openai_api_key,
                azure_deployment_name=settings.azure_openai_deployment_name,
                model=settings.openai_model
            )
            logger.info("AI agent initialized")
        elif settings.openai_api_key:
            ai_agent = ClusterIQAgent(
                api_key=settings.openai_api_key,
                model=settings.openai_model
            )
            logger.info("AI agent initialized")
    except ImportError as e:
        logger.warning(f"AI agent not available (langchain not installed): {str(e)}")
        logger.info("Server will run without AI features. Clusters and jobs will still work.")
    except Exception as e:
        logger.warning(f"Could not initialize AI agent: {str(e)}")
        logger.info("Server will run without AI features.")
        
except Exception as e:
    logger.error(f"Error during startup: {str(e)}")


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for ClusterIQ API."""
    
    def _set_cors_headers(self):
        """Set CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def _send_json_response(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/' or path == '/health':
                self._send_json_response({
                    "status": "healthy",
                    "databricks_configured": databricks_client is not None,
                    "ai_configured": ai_agent is not None,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif path == '/api/jobs':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                jobs = databricks_client.get_all_jobs()
                self._send_json_response(jobs)
            
            elif path.startswith('/api/jobs/') and '/runs' in path:
                job_id = int(path.split('/')[3])
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                runs = databricks_client.get_job_runs(job_id=job_id)
                self._send_json_response(runs)
            
            elif path == '/api/clusters':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                logger.info("API: Fetching clusters...")
                clusters = databricks_client.get_all_clusters()
                logger.info(f"API: Returning {len(clusters)} clusters")
                self._send_json_response(clusters)
            
            elif path.startswith('/api/clusters/') and path.endswith('/metrics'):
                cluster_id = path.split('/')[3]
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                metrics = databricks_client.get_cluster_metrics(cluster_id)
                self._send_json_response(metrics)
            
            elif path == '/api/stats':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                jobs = databricks_client.get_all_jobs()
                clusters = databricks_client.get_all_clusters()
                running_clusters = [c for c in clusters if c.get("state") == "RUNNING"]
                self._send_json_response({
                    "total_jobs": len(jobs),
                    "total_clusters": len(clusters),
                    "running_clusters": len(running_clusters),
                    "idle_clusters": len([c for c in running_clusters if c.get("num_workers", 0) > 0]),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif path == '/api/recommendations':
                if not analysis_cache:
                    self._send_json_response({"error": "No analysis available"}, 404)
                    return
                self._send_json_response(analysis_cache)
            
            else:
                self._send_json_response({"error": "Not found"}, 404)
        
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            self._send_json_response({"error": str(e)}, 500)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/api/analyze':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                
                if not ai_agent:
                    self._send_json_response({
                        "error": "AI agent not available. Install langchain to enable AI features.",
                        "message": "Basic analysis available without AI"
                    }, 503)
                    return
                
                jobs = databricks_client.get_all_jobs()
                clusters = databricks_client.get_all_clusters()
                
                job_runs = {}
                for job in jobs[:10]:
                    job_id = job.get("job_id")
                    if job_id:
                        runs = databricks_client.get_job_runs(job_id=job_id, limit=10)
                        job_runs[job_id] = runs
                
                recommendations = ai_agent.analyze_jobs_and_clusters(
                    jobs=jobs,
                    clusters=clusters,
                    job_runs=job_runs
                )
                
                global analysis_cache, cache_timestamp
                analysis_cache = {
                    "recommendations": recommendations,
                    "jobs_count": len(jobs),
                    "clusters_count": len(clusters),
                    "timestamp": datetime.utcnow().isoformat()
                }
                cache_timestamp = datetime.utcnow()
                
                self._send_json_response({
                    "recommendations": recommendations,
                    "summary": {
                        "total_jobs": len(jobs),
                        "total_clusters": len(clusters),
                        "recommendations_count": len(recommendations),
                        "timestamp": cache_timestamp.isoformat()
                    }
                })
            
            else:
                self._send_json_response({"error": "Not found"}, 404)
        
        except Exception as e:
            logger.error(f"Error handling POST: {str(e)}", exc_info=True)
            self._send_json_response({"error": str(e)}, 500)
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server():
    """Run the HTTP server."""
    port = settings.backend_port
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, APIHandler)
    logger.info(f"ClusterIQ Server starting on http://0.0.0.0:{port}")
    logger.info(f"Using direct HTTP requests to Databricks API")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()

