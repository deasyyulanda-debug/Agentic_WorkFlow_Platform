# 🤖 Agentic Workflow Platform

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)
![Tests](https://img.shields.io/badge/tests-36%2F36-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**A powerful full-stack platform for creating and executing multi-step AI workflows**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture)

</div>

---

## 📖 Overview

The **Agentic Workflow Platform** enables you to design, manage, and execute sophisticated multi-step AI workflows using multiple AI providers. Built with FastAPI and Next.js, it provides a robust backend API and an intuitive web interface for workflow automation.

### ✨ Highlights

- 🔗 **Multi-Step Workflows**: Chain multiple AI interactions in sequence, parallel, or conditional modes
- 🤖 **4 AI Providers**: OpenAI, Anthropic (Claude), Google Gemini, and DeepSeek
- 🎭 **AI Personas**: Configure different personas (Student, Researcher, ML Engineer, Data Scientist, AI Architect) for each step
- 🚀 **Production Ready**: 100% test coverage, comprehensive error handling, and async architecture
- 💅 **Modern UI**: Beautiful Next.js interface with dark mode support and real-time updates
- 📊 **Real-time Monitoring**: Track workflow execution status with live updates

## 🎯 Features

### Workflow Management
- ✅ Create multi-step AI workflows with visual builder
- ✅ Three execution modes: **Sequential**, **Parallel**, **Conditional**
- ✅ Configure AI personas and providers per step
- ✅ Validate workflows before execution
- ✅ Save and reuse workflow templates

### Provider Configuration
- ✅ Support for 4 major AI providers
- ✅ Secure API key management
- ✅ Test provider connections
- ✅ Activate/deactivate providers
- ✅ Multiple configurations per provider

### Execution & Monitoring
- ✅ Synchronous and asynchronous execution
- ✅ Real-time status tracking
- ✅ Step-by-step execution monitoring
- ✅ Execution history and analytics
- ✅ Artifact storage and retrieval

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ ([Download](https://www.python.org/downloads/))
- Node.js 18+ ([Download](https://nodejs.org/))
- Docker (optional) ([Download](https://www.docker.com/))

### Option 1: Local Development

**1. Clone the repository**
```bash
git clone <repository-url>
cd Agentic_WorkFlow_Platform
```

**2. Start the Backend**
```bash
cd apps/api
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
python run.py
```

Backend runs at: http://localhost:8000  
API Docs: http://localhost:8000/docs

**3. Start the Frontend** (in a new terminal)

> **Note**: If Node.js is not installed, download it from [nodejs.org](https://nodejs.org/)

```bash
cd apps/web
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

**4. Configure Providers**
- Open http://localhost:3000/settings
- Click "Add Provider"
- Enter your API key for OpenAI, Anthropic, Gemini, or DeepSeek
- Test the connection
- Activate the provider

**5. Create Your First Workflow**
- Navigate to http://localhost:3000/workflows
- Click "New Workflow"
- Add workflow steps with prompts
- Select providers and personas
- Save and execute!

### Option 2: Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## 📊 Architecture

### Monorepo Structure

```
Agentic_WorkFlow_Platform/
├── apps/
│   ├── api/              # FastAPI Backend (Python)
│   │   ├── src/
│   │   │   ├── api/     # REST API endpoints (31 endpoints)
│   │   │   ├── engine/  # Workflow execution engine
│   │   │   ├── providers/ # AI provider integrations
│   │   │   └── db/      # Database models & repositories
│   │   └── tests/       # Pytest suite (36 tests, 100% coverage)
│   │
│   └── web/             # Next.js Frontend (TypeScript)
│       ├── app/         # Pages (dashboard, workflows, runs, settings)
│       ├── components/  # React components
│       ├── lib/         # API client & utilities
│       └── types/       # TypeScript definitions
│
├── data/                # Persistent storage
│   ├── db/             # SQLite database
│   └── artifacts/      # Workflow execution results
│
├── docs/               # Documentation
└── docker-compose.yml  # Container orchestration
```

### Technology Stack

**Backend**
- FastAPI (async web framework)
- SQLAlchemy 2.0 (ORM)
- Pydantic 2.0 (validation)
- Pytest (testing)
- SQLite/PostgreSQL

**Frontend**
- Next.js 14 (App Router)
- TypeScript
- TanStack Query (data fetching)
- Tailwind CSS (styling)
- Axios (HTTP client)
- Zustand (state management)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete project overview and statistics |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Comprehensive deployment guide |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Full API reference (31 endpoints) |
| [BACKEND_STATUS.md](BACKEND_STATUS.md) | Backend verification report |
| [apps/web/README.md](apps/web/README.md) | Frontend-specific documentation |
| [docs/architecture/](docs/architecture/) | Architecture documentation (5 docs) |

## 🎭 Workflow Examples

### Example 1: Research Assistant
```typescript
{
  name: "Research Assistant",
  mode: "sequential",
  steps: [
    {
      prompt: "Research the latest AI trends in 2024",
      provider: "openai",
      persona: "researcher"
    },
    {
      prompt: "Summarize key findings in 5 bullet points",
      provider: "anthropic",
      persona: "ai_architect"
    }
  ]
}
```

### Example 2: Parallel Analysis
```typescript
{
  name: "Multi-Perspective Analysis",
  mode: "parallel",
  steps: [
    {
      prompt: "Analyze from ML engineer perspective",
      provider: "openai",
      persona: "ml_engineer"
    },
    {
      prompt: "Analyze from researcher perspective",
      provider: "gemini",
      persona: "researcher"
    }
  ]
}
```

## 🧪 Testing

### Run Backend Tests
```bash
cd apps/api
pytest                                    # Run all tests
pytest --cov=src --cov-report=html       # With coverage
```

**Results**: ✅ 36/36 tests passing (100% coverage)

## 📦 API Endpoints

The platform provides 31 REST API endpoints across 4 modules:

| Module | Endpoints | Description |
|--------|-----------|-------------|
| **Settings** | 9 | Provider configuration and management |
| **Workflows** | 8 | Workflow creation and lifecycle |
| **Runs** | 8 | Workflow execution and monitoring |
| **Artifacts** | 6 | Result storage and retrieval |

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete reference.

## 🔒 Security

- ✅ API key encryption at rest
- ✅ CORS configuration
- ✅ Input validation with Pydantic
- ✅ Environment-based secrets
- ✅ Error message sanitization

## 🛣️ Roadmap

### Version 1.1 (Next)
- [ ] WebSocket support for real-time updates
- [ ] Dark mode toggle in UI
- [ ] Workflow templates library
- [ ] Enhanced artifact viewer

### Version 1.2
- [ ] Visual workflow designer (drag-and-drop)
- [ ] User authentication and authorization
- [ ] Team collaboration features
- [ ] Scheduled workflow execution

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**
- Check Python version: `python --version` (3.11+)
- Ensure virtual environment is activated
- Verify dependencies: `pip install -r requirements.txt`

**Frontend won't start**
- Install Node.js from [nodejs.org](https://nodejs.org/)
- Clear node_modules: `rm -rf node_modules && npm install`

**API connection failed**
- Verify backend is running: http://localhost:8000/api/v1/health
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS settings in backend

See [DEPLOYMENT.md](DEPLOYMENT.md) for more troubleshooting tips.

## 📊 Project Stats

- **Lines of Code**: ~5,500+
- **Test Coverage**: 100% (36/36 tests)
- **API Endpoints**: 31
- **Supported Providers**: 4
- **Execution Modes**: 3
- **AI Personas**: 5

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Special thanks to:
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing backend framework
- [Next.js](https://nextjs.org/) for the powerful React framework
- [TanStack Query](https://tanstack.com/query) for data fetching
- [Tailwind CSS](https://tailwindcss.com/) for styling
- All AI providers (OpenAI, Anthropic, Google, DeepSeek)

---

<div align="center">

**Built with ❤️ using FastAPI & Next.js**

</div>
