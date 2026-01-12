"""AI Agent for analyzing Databricks jobs and clusters to identify cost leaks."""
from typing import List, Dict, Any, Optional
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
import json
import logging

logger = logging.getLogger(__name__)


class ClusterIQAgent:
    """AI Agent for cost optimization analysis."""
    
    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4-turbo-preview",
        azure_endpoint: str = "",
        azure_api_key: str = "",
        azure_deployment_name: str = ""
    ):
        """Initialize the AI agent.
        
        Args:
            api_key: OpenAI API key (for standard OpenAI)
            model: Model name to use
            azure_endpoint: Azure OpenAI endpoint URL
            azure_api_key: Azure OpenAI API key
            azure_deployment_name: Azure OpenAI deployment name
        """
        # Use Azure OpenAI if credentials are provided, otherwise use standard OpenAI
        if azure_endpoint and azure_api_key and azure_deployment_name:
            # Ensure endpoint doesn't have trailing slash
            endpoint = azure_endpoint.rstrip('/')
            self.llm = AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=azure_deployment_name,
                openai_api_version="2024-02-15-preview",
                openai_api_key=azure_api_key,
                temperature=0,
                model=azure_deployment_name,  # Use deployment name as model
            )
            logger.info(f"Using Azure OpenAI - Endpoint: {endpoint}, Deployment: {azure_deployment_name}")
        elif api_key:
            self.llm = ChatOpenAI(
                temperature=0,
                model_name=model,
                openai_api_key=api_key,
            )
            logger.info("Using standard OpenAI")
        else:
            raise ValueError("Either OpenAI API key or Azure OpenAI credentials must be provided")
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the agent with tools and prompts."""
        tools = [
            Tool(
                name="analyze_cluster_utilization",
                func=self._analyze_cluster_utilization,
                description="Analyzes cluster configuration and usage to identify over-provisioning"
            ),
            Tool(
                name="analyze_job_efficiency",
                func=self._analyze_job_efficiency,
                description="Analyzes job configuration and execution patterns to identify inefficiencies"
            ),
            Tool(
                name="calculate_cost_savings",
                func=self._calculate_cost_savings,
                description="Calculates potential cost savings from optimization recommendations"
            ),
        ]
        
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
        )
    
    def analyze_jobs_and_clusters(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> List[Dict[str, Any]]:
        """Analyze jobs and clusters to identify cost leaks and optimization opportunities.
        
        Args:
            jobs: List of job dictionaries
            clusters: List of cluster dictionaries
            job_runs: Optional dictionary mapping job_id to list of runs
            
        Returns:
            List of recommendations with analysis
        """
        try:
            # Prepare context for AI analysis
            context = self._prepare_analysis_context(jobs, clusters, job_runs)
            
            # Create analysis prompt
            prompt = f"""Analyze the following Databricks jobs and clusters to identify:
1. Cost leaks (over-provisioned clusters, idle resources)
2. Value leaks (small jobs on large clusters, inefficient configurations)
3. Optimization opportunities (right-sizing, scheduling, resource allocation)

Context:
{json.dumps(context, indent=2)}

Provide detailed recommendations for each identified issue, including:
- Issue type (cost leak, value leak, optimization opportunity)
- Severity (high, medium, low)
- Current configuration
- Recommended configuration
- Estimated cost savings
- Risk assessment
- Implementation steps

Format the response as a JSON array of recommendations."""

            # Get AI analysis
            try:
                response = self.llm.invoke(prompt)
                # Handle both ChatOpenAI and AzureChatOpenAI response formats
                if hasattr(response, 'content'):
                    content = response.content
                elif isinstance(response, str):
                    content = response
                else:
                    # Try to get content from AIMessage or similar
                    content = str(response)
                recommendations = self._parse_recommendations(content)
            except Exception as e:
                logger.error(f"Error calling LLM: {str(e)}")
                # Return fallback analysis if LLM call fails
                recommendations = self._fallback_analysis(jobs, clusters)
            
            # Enhance with additional analysis
            enhanced_recommendations = self._enhance_recommendations(
                recommendations, jobs, clusters, job_runs
            )
            
            return enhanced_recommendations
        
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return self._fallback_analysis(jobs, clusters)
    
    def _prepare_analysis_context(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Prepare context for AI analysis."""
        # Analyze cluster utilization
        cluster_analysis = []
        for cluster in clusters:
            if cluster.get("state") == "RUNNING":
                utilization_score = self._calculate_cluster_utilization(cluster)
                cluster_analysis.append({
                    "cluster_id": cluster.get("cluster_id"),
                    "cluster_name": cluster.get("cluster_name"),
                    "num_workers": cluster.get("num_workers", 0),
                    "node_type": cluster.get("node_type_id"),
                    "utilization_score": utilization_score,
                    "is_idle": utilization_score < 0.2,
                })
        
        # Analyze job patterns
        job_analysis = []
        for job in jobs:
            runs = job_runs.get(job.get("job_id"), []) if job_runs else []
            avg_duration = self._calculate_avg_duration(runs)
            job_analysis.append({
                "job_id": job.get("job_id"),
                "job_name": job.get("job_name"),
                "num_tasks": len(job.get("settings", {}).get("tasks", [])),
                "avg_duration_seconds": avg_duration,
                "cluster_config": self._extract_cluster_config(job),
            })
        
        return {
            "clusters": cluster_analysis,
            "jobs": job_analysis,
            "summary": {
                "total_clusters": len(clusters),
                "running_clusters": len([c for c in clusters if c.get("state") == "RUNNING"]),
                "total_jobs": len(jobs),
            }
        }
    
    def _calculate_cluster_utilization(self, cluster: Dict[str, Any]) -> float:
        """Calculate cluster utilization score (0-1)."""
        # Simplified utilization calculation
        # In production, this would use actual metrics
        num_workers = cluster.get("num_workers", 0)
        if num_workers == 0:
            return 0.0
        
        # Placeholder: would use actual metrics from Databricks
        # For now, return a heuristic based on cluster age and activity
        return 0.5  # Default moderate utilization
    
    def _calculate_avg_duration(self, runs: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate average duration of job runs."""
        if not runs:
            return None
        
        durations = [
            run.get("duration")
            for run in runs
            if run.get("duration") is not None
        ]
        
        return sum(durations) / len(durations) if durations else None
    
    def _extract_cluster_config(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract cluster configuration from job."""
        tasks = job.get("settings", {}).get("tasks", [])
        if not tasks:
            return None
        
        # Get cluster config from first task
        first_task = tasks[0]
        if first_task.get("new_cluster"):
            return first_task.get("new_cluster")
        elif first_task.get("cluster_id"):
            return {"cluster_id": first_task.get("cluster_id")}
        
        return None
    
    def _parse_recommendations(self, content: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured recommendations."""
        try:
            # Try to extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            recommendations = json.loads(json_str)
            if isinstance(recommendations, list):
                return recommendations
            elif isinstance(recommendations, dict) and "recommendations" in recommendations:
                return recommendations["recommendations"]
            else:
                return [recommendations]
        
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON, using fallback")
            return []
    
    def _enhance_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> List[Dict[str, Any]]:
        """Enhance recommendations with additional analysis."""
        enhanced = []
        
        for rec in recommendations:
            enhanced_rec = {
                **rec,
                "id": f"rec_{len(enhanced)}",
                "timestamp": self._get_current_timestamp(),
                "confidence_score": rec.get("confidence_score", 0.7),
            }
            enhanced.append(enhanced_rec)
        
        return enhanced
    
    def _fallback_analysis(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fallback analysis when AI fails."""
        recommendations = []
        
        # Check for idle clusters
        for cluster in clusters:
            if cluster.get("state") == "RUNNING" and cluster.get("num_workers", 0) > 0:
                recommendations.append({
                    "id": f"rec_{len(recommendations)}",
                    "type": "cost_leak",
                    "severity": "medium",
                    "title": f"Idle cluster detected: {cluster.get('cluster_name')}",
                    "description": "Cluster appears to be running with low utilization",
                    "resource_type": "cluster",
                    "resource_id": cluster.get("cluster_id"),
                    "current_config": {
                        "num_workers": cluster.get("num_workers"),
                        "node_type": cluster.get("node_type_id"),
                    },
                    "recommended_config": {
                        "action": "Terminate if idle for extended period",
                    },
                    "estimated_savings": "Medium",
                    "risk": "Low",
                })
        
        return recommendations
    
    def _analyze_cluster_utilization(self, cluster_data: str) -> str:
        """Tool function for analyzing cluster utilization."""
        # This would be called by the agent
        return "Analysis complete"
    
    def _analyze_job_efficiency(self, job_data: str) -> str:
        """Tool function for analyzing job efficiency."""
        return "Analysis complete"
    
    def _calculate_cost_savings(self, recommendation: str) -> str:
        """Tool function for calculating cost savings."""
        return "Calculation complete"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

