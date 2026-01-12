# ClusterIQ Backend

FastAPI backend service for ClusterIQ that integrates with Databricks APIs and uses GenAI for cost optimization analysis.

## Features

- **Databricks Integration:** Fetches jobs, clusters, and execution metrics
- **AI-Powered Analysis:** Uses OpenAI/LangChain to identify cost leaks and optimization opportunities
- **Real-time Updates:** Provides real-time recommendations via API endpoints
- **RESTful API:** Clean REST API for frontend consumption

## Architecture

```
main.py              # FastAPI application and routes
databricks_client.py # Databricks API client
ai_agent.py          # GenAI agent for analysis
config.py            # Configuration management
```

## API Endpoints

See SETUP.md for complete API documentation.

## Configuration

Create a `.env` file with:
- Databricks credentials (host, token)
- OpenAI API key
- Server configuration

## Running

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --port 8000
```

