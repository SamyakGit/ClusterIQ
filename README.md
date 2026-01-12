# ClusterIQ

> An AI-driven optimization engine for Databricks that continuously scans jobs and clusters to improve compute utilization and reduce cost.

---

## 📋 Overview

ClusterIQ transforms raw execution and usage metrics into clear, actionable recommendations. It applies intelligence across all jobs and clusters, not just individual runs, helping teams optimize their Databricks infrastructure efficiently.

---

## 🎯 Problem Statement

Databricks provides rich metrics and monitoring, but optimization decisions are still largely manual and reactive. Teams often run diverse workloads on shared or oversized clusters, leading to:

- **Idle compute** waste
- **Inflated DBU consumption**
- **Inconsistent performance**

ClusterIQ addresses this gap by providing intelligent, automated analysis and recommendations.

---

## ✨ Key Capabilities

- **End-to-end scanning** of Databricks jobs and clusters
- **Historical analysis** of CPU, memory, IO, and runtime behavior
- **Detection** of underutilized and over-provisioned clusters
- **Job classification** based on workload patterns
- **AI-driven recommendations** for cluster right-sizing and scheduling
- **Cost-saving estimation** with risk indicators

---

## 🏗️ Architecture Overview

```
┌──────────────────────────┐
│      Databricks APIs     │
│──────────────────────────│
│ • Jobs API               │
│ • Clusters API           │
│ • Runs API               │
│ • DBU & Metrics Logs     │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│   Data Collection Layer  │
│──────────────────────────│
│ • Job metadata           │
│ • Cluster configuration  │
│ • Runtime metrics        │
│ • Historical execution   │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Workload Analysis Layer │
│──────────────────────────│
│ • CPU vs memory profiling│
│ • Idle and peak detection│
│ • Job pattern clustering │
│ • Cost trend analysis    │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│ AI Optimization Engine   │
│──────────────────────────│
│ • Right-sizing logic     │
│ • Cluster type selection │
│ • Schedule optimization  │
│ • Savings estimation     │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│ Recommendation Output    │
│──────────────────────────│
│ • Job-level insights     │
│ • Cluster-level actions  │
│ • Cost-saving estimates  │
│ • Risk and impact scores │
└──────────────────────────┘
```

---

## 🔄 How It Works

### 1. **Collect**
Pulls job, cluster, and execution data using Databricks APIs and system metrics.

### 2. **Analyze**
Builds historical profiles of workloads to understand true resource consumption patterns.

### 3. **Learn**
Applies AI models and heuristics to classify workloads and detect inefficiencies.

### 4. **Recommend**
Produces ranked, explainable recommendations with estimated savings and impact.

---

## 💡 Sample Recommendations

- **Reduce worker count** for jobs consistently using less than 40% CPU
- **Move lightweight jobs** to job clusters or single-node execution
- **Disable autoscaling** where scale-up is never triggered
- **Consolidate overlapping schedules** to reduce concurrent cluster load
- **Terminate long-running idle clusters**

---

## 📈 Expected Benefits

- **20–40% reduction** in DBU consumption
- **Higher cluster utilization**
- **Improved job stability** and predictability
- **Faster optimization cycles** without manual analysis
- **Strong alignment** with FinOps and cost governance goals

---

## 👥 Target Users

- Data engineering teams
- Databricks platform administrators
- Cloud and FinOps teams
- Engineering leadership

---

## 🚫 Non-Goals

ClusterIQ focuses on decision intelligence, not blind automation. It does **not**:

- Replace Databricks native monitoring tools
- Provide real-time job execution control
- Make automatic changes without human approval

---

## 🔒 Security and Access

- **Read-only access** to Databricks APIs via REST API
- **No modification** of job or cluster configuration by default
- **Supports** service principals and scoped tokens
- **Direct HTTP requests** - Uses standard REST API calls (curl-style) for maximum compatibility

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Databricks workspace access token
- Azure OpenAI API key and endpoint (or standard OpenAI API key)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ClusterIQ
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your credentials
   ```

3. **Set up the frontend:**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Run the application:**
   ```bash
   # Terminal 1: Start backend (simple HTTP server)
   cd backend
   python simple_server.py

   # Terminal 2: Start frontend
   cd frontend
   npm run dev
   ```

5. **Open your browser:**
   - Navigate to `http://localhost:3000`
   - Backend API available at `http://localhost:8000`

For detailed setup instructions, see [SETUP.md](SETUP.md).

**Note:** The backend uses Python's built-in HTTP server and direct REST API calls to Databricks (no FastAPI or external web framework required).

---

## 📁 Project Structure

```
ClusterIQ/
├── backend/                 # Python backend service
│   ├── simple_server.py    # Simple HTTP server (main server)
│   ├── main.py             # Flask alternative (optional)
│   ├── databricks_client.py # Databricks REST API client (curl-style)
│   ├── ai_agent.py         # GenAI agent for analysis (optional)
│   ├── config.py           # Configuration management
│   ├── requirements.txt    # Python dependencies
│   ├── env.example         # Environment variables template
│   └── test_databricks_api.py # API testing script
│
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Recommendations.jsx
│   │   │   ├── JobsView.jsx
│   │   │   └── ClustersView.jsx
│   │   ├── services/       # API service layer
│   │   │   └── api.js
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # Entry point
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
│
├── README.md               # This file
├── SETUP.md                # Detailed setup guide
└── .gitignore             # Git ignore rules
```

---

## 🛠️ Technology Stack

### Backend
- **Python HTTP Server** - Built-in `http.server` module (no external framework)
- **Requests** - Direct HTTP requests to Databricks REST API (curl-style)
- **LangChain** - AI agent framework (optional)
- **Azure OpenAI** - GPT models for analysis via Azure OpenAI
- **Python-dotenv** - Environment configuration

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework (DXC-inspired design)
- **React Query** - Data fetching and caching
- **Axios** - HTTP client
- **React Router** - Client-side routing

---

## 🚀 Future Enhancements

- Automated remediation with approval workflows
- Integration with cost management tools
- Slack or Teams notifications for high-impact recommendations
- Forecast-based cluster sizing
- Multi-workspace aggregation
- Real-time cluster metrics and utilization tracking
- Historical cost analysis and trends

## 🔧 Architecture Details

### Backend Architecture
- **Simple HTTP Server**: Uses Python's built-in `http.server` module
- **Direct REST API Calls**: Makes HTTP requests directly to Databricks REST API endpoints
- **No External Dependencies**: Minimal dependencies - only `requests` for HTTP calls
- **Optional AI Features**: AI agent is optional - server runs without langchain if not installed

### API Endpoints
- `GET /health` - Health check
- `GET /api/jobs` - List all Databricks jobs
- `GET /api/jobs/{id}/runs` - Get job runs
- `GET /api/clusters` - List all clusters (using direct REST API)
- `GET /api/clusters/{id}/metrics` - Get cluster metrics
- `GET /api/stats` - Get statistics
- `POST /api/analyze` - Run AI analysis (requires AI agent)
- `GET /api/recommendations` - Get cached recommendations

---

## 📝 Summary

> **ClusterIQ brings intelligence where Databricks stops short.**  
> It turns metrics into decisions, and decisions into measurable cost savings.

### Key Features
- ✅ **Simple & Lightweight**: No heavy frameworks - uses Python's built-in HTTP server
- ✅ **Direct API Integration**: Uses REST API calls (curl-style) for maximum compatibility  
- ✅ **Real-time Monitoring**: Auto-refresh capabilities for live cluster monitoring
- ✅ **AI-Powered Analysis**: Optional Azure OpenAI integration for intelligent recommendations
- ✅ **Modern UI**: DXC-inspired professional design with React and Tailwind CSS
- ✅ **Minimal Dependencies**: Works with Python standard library + requests (AI features optional)

---
