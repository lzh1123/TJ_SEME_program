# Slideon — AI-Powered Intelligent PPT Generation System

> **Version 0.2.0** | MIT License | [Live Demo](http://119.3.125.141)

Slideon is an AI-driven presentation generation system that transforms a simple topic or uploaded document into a complete, professionally structured `.pptx` file. Powered by large language models (LLMs) and retrieval-augmented generation (RAG), it handles intent analysis, outline planning, content generation, layout rendering, and export — all in one pipeline.

**Core philosophy: "AI handles semantics, Renderer handles visuals."** The LLM outputs structured semantic DSL (Domain-Specific Language) only — no coordinates, no font sizes, no layout details. A dedicated rendering engine compiles the DSL into a RenderTree and produces pixel-perfect slides with consistent theming.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [RAG Setup (Optional)](#rag-setup-optional)
- [API Overview](#api-overview)
- [Deployment](#deployment)
- [Testing](#testing)
- [License](#license)

---

## Features

### 🧠 AI-Powered Generation Pipeline
- **3-stage pipeline**: Intent Analysis → Structure Planning → DSL Generation
- **15 slide types** supported: cover, agenda, text, timeline, KPI, comparison, SWOT, roadmap, process flow, chart, multi-column, architecture, quote, divider, team
- **Multi-LLM support**: DeepSeek, Qwen (Tongyi Qianwen), GLM (Zhipu) — switchable per user
- **Multi-layer fallback & repair**: 600+ lines of defensive code ensure usable output even when LLM calls fail

### 🔍 RAG (Retrieval-Augmented Generation)
- **Hybrid retrieval**: Dense vector search (Milvus ANN) + Sparse keyword search + Web search, fused via RRF (Reciprocal Rank Fusion)
- **Deep Fetch**: Full-text extraction from web pages via trafilatura
- **Document ingestion**: Upload PDF, DOCX, PPTX, TXT, MD files — auto-parsed, chunked, embedded, and stored in Milvus
- **Seed knowledge base**: 63 curated topics across 12 categories for bootstrap initialization
- **LangGraph orchestration**: Parallel multi-source retrieval with structured state management

### 🎨 Rendering & Themes
- **4 built-in themes**: Modern Blue (tech), Paper Light (education), Academic Gray (reports), Minimal Black (creative)
- **Design token system**: Colors, typography, spacing, radius, shadows — fully themable
- **Component-level editing**: Patch individual slide components (position, style, content) via API
- **PPTX export**: Native PowerPoint charts, text boxes, shapes, tables via python-pptx

### 📊 Quality Evaluation
- **Rule-based metrics**: Structure completeness, information density, content diversity, BLEU, ROUGE-L
- **LLM-as-Judge**: Semantic scoring on structure rationality, fact accuracy, logical coherence, content depth
- **RAG metrics**: Retrieval recall & precision tracking
- **Batch evaluation**: Cross-compare multiple configs × topics

### 👤 User System
- JWT authentication (access + refresh token rotation)
- Per-user LLM configuration (provider, model, API key)
- Personal dashboard, outline management, knowledge base

### 🖥️ Modern Frontend
- Vue 3 Composition API + Vite
- Floating ball UI for quick outline generation from any page
- Drag-and-drop document upload
- Outline editor with 15 slide type forms
- Radar chart & metric cards for evaluation visualization
- Responsive design with custom design token system

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI (Python 3.12) | Async HTTP API, auto OpenAPI docs |
| **AI Orchestration** | LangChain + LangGraph | Prompt templating & state graph engine |
| **LLM Providers** | DeepSeek / Qwen / GLM | Multi-model support via OpenAI-compatible API |
| **Vector Database** | Milvus 3.0 | Hybrid ANN + keyword search |
| **Embedding Model** | BAAI/bge-small-zh-v1.5 | 512-dim Chinese-English bilingual embeddings |
| **Web Search** | DuckDuckGo / Baidu Qianfan | Real-time web information retrieval |
| **Document Parsing** | PyMuPDF / python-docx / pypdf | PDF, DOCX, PPTX, TXT, MD extraction |
| **PPTX Export** | python-pptx | Native PowerPoint file generation |
| **Database** | PostgreSQL + SQLAlchemy (async) | User accounts, outlines, tokens |
| **Migrations** | Alembic | Database schema versioning |
| **Frontend** | Vue 3 + Vite + Pinia + Vue Router | SPA with Composition API |
| **Deployment** | GitHub Actions → Huawei Cloud | CI/CD with systemd + nginx |

---

## Architecture

```
User Input (Topic or Document)
        │
        ▼
┌──────────────────────────────────────┐
│            RAG Retrieval              │
│  Milvus ANN + Keyword + Web Search   │
│  → RRF Fusion → Enhanced Context     │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│           AI Pipeline                 │
│  Stage 1: Intent Analysis            │
│  Stage 2: Structure Planning (15     │
│           slide intent types)        │
│  Stage 3: DSL Generation (semantic   │
│           JSON, no layout fields)    │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│          Render Engine               │
│  Component Planner → Layout Engine   │
│  → Theme Engine → RenderTree (JSON)  │
└────────────────┬─────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Vue 3 SPA   │  │  PPTX Export  │
│  (edit/view) │  │  (.pptx file) │
└──────────────┘  └──────────────┘
```

The system follows a **DSL-driven architecture** where the LLM only outputs structured semantic data (slide intents, titles, bullet points, chart data, etc.) without any layout information. The rendering engine then handles all visual concerns — positioning, styling, theming — ensuring consistent, professional output regardless of which LLM generated the content.

### Design Principles

| Decision | Rationale |
|----------|-----------|
| AI outputs semantic DSL only | Decouples content from layout; renderer guarantees visual consistency |
| 15 intent types | Covers common PPT scenarios; each has dedicated composer + layout |
| RAG hybrid search + RRF fusion | Semantic + keyword + web — multi-source complementary retrieval |
| LangGraph orchestration | Parallel multi-source retrieval with structured state management |
| 3-layer fault tolerance | 600-line repair code + default 14-slide fallback ensures system always responds |
| BGE-small-zh-v1.5 | Lightweight 512-dim bilingual embeddings, matched to Milvus IP metric |
| In-memory task queue | MVP simplicity; migratable to Redis/Celery when needed |
| File-based presentation storage | JSON bundles for simplicity; migratable to object storage |

---

## Project Structure

```
TJ_SEME_program/
├── backend/
│   ├── ppt_backend/
│   │   ├── api/                        # FastAPI app factory + routes + auth
│   │   │   ├── main.py                 # App factory (CORS, concurrency limiter)
│   │   │   ├── routes.py               # Core API endpoints
│   │   │   ├── auth_routes.py          # Auth endpoints (register/login/refresh)
│   │   │   └── deps.py                 # Dependency injection helpers
│   │   ├── domain/                     # Pydantic domain models
│   │   │   ├── dsl.py                  # 15 semantic slide DSL types
│   │   │   ├── render_tree.py          # RenderTree component model
│   │   │   ├── presentation.py         # PresentationBundle model
│   │   │   └── theme.py                # Design token theme system (4 themes)
│   │   ├── services/
│   │   │   ├── ai/                     # AI generation pipeline
│   │   │   │   ├── pipeline.py         # 3-stage pipeline + fallback + repair
│   │   │   │   ├── client.py           # LLM invocation + JSON parsing
│   │   │   │   ├── prompts.py          # LangChain prompt templates
│   │   │   │   ├── schemas.py          # IntentAnalysis, PresentationPlan
│   │   │   │   └── model_config.py     # Multi-provider LLM configuration
│   │   │   ├── rendering/              # Render engine
│   │   │   │   ├── compiler.py         # DSL → RenderTree compiler
│   │   │   │   ├── planning.py         # 15 slide composers
│   │   │   │   ├── layout.py           # 9 layout classes (absolute positioning)
│   │   │   │   ├── theme_engine.py     # Theme token → component styles
│   │   │   │   └── registry.py         # Composer + layout registries
│   │   │   ├── rag/                    # Retrieval-Augmented Generation
│   │   │   │   ├── rag_service.py      # RAG facade
│   │   │   │   ├── retrieval.py        # HybridRetriever (core)
│   │   │   │   ├── milvus_client.py    # Milvus vector DB client
│   │   │   │   ├── embedding.py        # BGE embedding service
│   │   │   │   ├── knowledge_base.py   # Document ingestion + chunking
│   │   │   │   ├── web_search.py       # DuckDuckGo / Baidu search
│   │   │   │   ├── content_fetcher.py  # Full-text web page extraction
│   │   │   │   ├── rag_graph.py        # LangGraph state graph
│   │   │   │   ├── document_parser.py  # PDF/DOCX/PPTX/TXT/MD parser
│   │   │   │   ├── seed_knowledge.py   # 63 seed topics bootstrapper
│   │   │   │   └── task_queue.py       # Async document import queue
│   │   │   ├── evaluation/             # Quality evaluation
│   │   │   │   ├── evaluator.py        # Evaluation orchestrator
│   │   │   │   ├── metrics.py          # Rule-based metrics (BLEU, ROUGE-L, etc.)
│   │   │   │   ├── llm_judge.py        # LLM-as-Judge semantic scoring
│   │   │   │   ├── rag_eval.py         # RAG recall/precision tracking
│   │   │   │   └── schemas.py          # Evaluation data models
│   │   │   ├── presentation_service.py # Core business orchestration
│   │   │   └── auth_service.py         # JWT auth + user management
│   │   ├── exporters/
│   │   │   ├── pptx_exporter.py        # RenderTree → .pptx
│   │   │   └── pptx_components.py      # 16 PPTX component renderers
│   │   ├── repos/
│   │   │   └── presentation_repo.py    # File-based presentation storage
│   │   ├── infrastructure/
│   │   │   ├── database.py             # SQLAlchemy async engine + session
│   │   │   └── models/                 # User, RefreshToken, Presentation, Outline ORM
│   │   ├── container.py                # Dependency injection wiring
│   │   ├── settings.py                 # Env-based configuration
│   │   └── rag_bootstrap.py            # One-click KB initialization CLI
│   ├── alembic/                        # Database migrations (5 versions)
│   ├── prompt/                         # Prompt engineering reference docs
│   ├── test/                           # Unit + integration tests
│   └── requirements.txt
├── slideon-frontend/                   # Vue 3 + Vite SPA
│   └── src/
│       ├── views/                      # 10 page views
│       │   ├── HomeView.vue            # Landing page
│       │   ├── EditorView.vue          # PPT canvas (15+ component renderers)
│       │   ├── OutlineEditorView.vue   # DSL outline editor
│       │   ├── DashboardView.vue       # Outline management
│       │   ├── KnowledgeBaseView.vue   # KB document management
│       │   ├── BatchEvalView.vue       # Batch evaluation
│       │   ├── ProfileView.vue         # User profile + LLM config
│       │   ├── LoginView.vue           # Login
│       │   └── RegisterView.vue        # Registration
│       ├── components/common/          # Shared UI components
│       │   ├── AppHeader.vue           # Navigation bar
│       │   ├── OutlineModal.vue        # Generation modal
│       │   ├── EvaluationPanel.vue     # Quality evaluation panel
│       │   ├── KnowledgeBasePanel.vue  # KB management panel
│       │   ├── RadarChart.vue          # SVG radar chart
│       │   └── MetricCard.vue          # Score card component
│       ├── components/icons/           # Custom SVG icon system (48 icons)
│       ├── services/                   # API client + auth service
│       ├── stores/                     # Pinia stores (auth, outline, kb tasks)
│       ├── composables/                # useFloatingBall composable
│       ├── config/                     # API endpoints + config
│       ├── router/                     # Vue Router (10 routes)
│       ├── styles/                     # Design tokens + base + components CSS
│       └── utils/                      # ID generation utilities
├── scripts/                            # Experiment & report generation scripts
├── experiment/                         # AI outline generation experiments
│   ├── Experiment Design/              # Protocols, prompts, test cases
│   └── Report Assets/                  # CSVs, figures, raw outputs
├── test/                               # Test scripts & results (CSV/JSON/XML)
├── docs/                               # Project docs & architecture
├── document/                           # Deliverable documents (PDF)
├── data/                               # Runtime data (presentations, exports)
├── .github/workflows/deploy.yml        # CI/CD to Huawei Cloud
├── environment.yml                     # Conda environment spec
├── .env.example                        # Environment variable template
└── REMOTE_TESTING_GUIDE.md             # Remote API testing guide (Chinese)
```

---

## Getting Started

### Prerequisites

- **Python 3.12+** (recommended: use Conda with `environment.yml`)
- **Node.js 20+** (for frontend)
- **PostgreSQL** (for user accounts, outlines)
- **Milvus** (optional, for RAG features)

### Backend Setup

```bash
# Clone the repository
git clone <repo-url>
cd TJ_SEME_program

# Create conda environment
conda env create -f environment.yml
conda activate slideon

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example ../.env
# Edit .env with your API keys and database URL

# Run database migrations
alembic upgrade head

# Start the backend server
python -m uvicorn ppt_backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd slideon-frontend

# Install dependencies
npm install

# Start development server (port 3000)
npm run dev

# Build for production
npm run build
```

### RAG Setup (Optional)

RAG features require a running Milvus instance:

```bash
# Start Milvus (see backend/ppt_backend/milvus/README.md)
cd backend/ppt_backend/milvus
# Run standalone.bat (Windows) or use Docker

# Bootstrap the seed knowledge base
cd backend
python -m ppt_backend.rag_bootstrap
```

---

## API Overview

### Presentation Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/dsl` | Generate outline (DSL) from text topic |
| `POST` | `/dsl/from-document` | Generate outline from uploaded document |
| `POST` | `/render-tree` | Compile outline into RenderTree |
| `POST` | `/presentations` | Create full presentation (DSL + render + save) |
| `GET` | `/presentations/{id}` | Get full PresentationBundle |
| `PATCH` | `/presentations/{id}/components/{cid}` | Edit slide component |
| `PUT` | `/presentations/{id}/theme` | Switch theme with re-render |
| `POST` | `/presentations/{id}/regenerate` | Regenerate presentation |
| `POST` | `/presentations/{id}/export/pptx` | Download .pptx file |

### RAG & Knowledge Base

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rag/search` | Hybrid search (web + local vector) |
| `POST` | `/rag/enhance` | Get RAG-enhanced context for a topic |
| `POST` | `/rag/documents` | Upload document to knowledge base |
| `POST` | `/rag/documents/batch` | Batch upload (async with progress tracking) |
| `GET` | `/rag/documents` | List knowledge base documents |
| `DELETE` | `/rag/documents/{source}` | Remove document from KB |
| `POST` | `/rag/bootstrap` | Initialize seed knowledge base |

### Evaluation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/eval/single/{id}` | Evaluate a single presentation |
| `POST` | `/eval/batch` | Batch evaluation (multi-config × multi-topic) |

### Auth & System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login (returns JWT token pair) |
| `POST` | `/auth/refresh` | Refresh access token (token rotation) |
| `GET` | `/auth/me` | Get current user profile |
| `GET` | `/auth/llm-config` | Get per-user LLM configuration |
| `PUT` | `/auth/llm-config` | Update per-user LLM configuration |
| `GET` | `/health` | Health check |
| `GET` | `/themes` | List available themes |
| `GET` | `/llm/providers` | List available LLM providers |

> See [REMOTE_TESTING_GUIDE.md](REMOTE_TESTING_GUIDE.md) for detailed curl examples for every endpoint.

---

## Deployment

The project is deployed to **Huawei Cloud** via GitHub Actions (see [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)).

### Deployment Architecture

```
GitHub Actions Runner
        │
        ├── Build frontend (npm ci + npm run build)
        ├── SCP frontend dist → /tmp/slideon-dist
        │
        └── SSH → Huawei Cloud Server
              ├── git pull main
              ├── Write secrets to backend/.env
              ├── pip install -r requirements.txt
              ├── alembic upgrade head
              ├── systemctl restart slideon-backend
              ├── Health check (curl /health, up to 20 retries)
              └── Deploy frontend to nginx + reload
```

- **Backend**: systemd service (`slideon-backend`) running Uvicorn on port 8000
- **Frontend**: Static files served by nginx, reverse-proxied to backend API

### Manual Deployment

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn ppt_backend.api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd slideon-frontend
npm ci
npm run build
# Serve dist/ with nginx or any static file server
```

---

## Testing

### Running Tests

```bash
# All tests
cd backend
pytest

# Unit tests only
pytest test/unit/

# Integration tests only
pytest test/integration/

# With coverage
pytest --cov=ppt_backend --cov-report=html
```

### Test Structure

| Category | Location | Description |
|----------|----------|-------------|
| Unit tests | `backend/test/unit/` | Auth, DSL repair, RAG retrieval, evaluation metrics, persistence |
| Integration tests | `backend/test/integration/` | API smoke tests, rendering + export round-trip, service lifecycle |
| Contract tests | `test/scripts/run_api_contract_tests.py` | API contract verification |
| E2E tests | `test/scripts/run_frontend_e2e_tests.py` | Frontend end-to-end flows |
| Static analysis | `test/scripts/run_frontend_static_tests.py` | Frontend code quality |
| Experiment scripts | `scripts/` | AI outline generation experiments & reports |

### Remote API Testing

For testing against the deployed server, see [REMOTE_TESTING_GUIDE.md](REMOTE_TESTING_GUIDE.md) which includes curl commands for all endpoints against `http://119.3.125.141`.

---

## Environment Variables

See [`.env.example`](.env.example) for the full template. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | — |
| `QWEN_API_KEY` | Qwen (Tongyi Qianwen) API key | — |
| `GLM_API_KEY` | GLM (Zhipu) API key | — |
| `GLM_API_BASE` | GLM API base URL | `https://open.bigmodel.cn/api/paas/v4` |
| `GLM_MODEL` | GLM model name | `glm-4.7` |
| `LLM_API_BASE` | Default LLM API base | `https://api.deepseek.com` |
| `LLM_MODEL` | Default LLM model | `deepseek-v4-flash` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `JWT_SECRET_KEY` | JWT signing secret | — |
| `MILVUS_URI` | Milvus server address | `http://localhost:19530` |
| `EMBEDDING_MODEL` | Sentence transformer model | `BAAI/bge-small-zh-v1.5` |
| `RAG_ENABLED` | Enable RAG features | `true` |
| `WEB_SEARCH_PROVIDER` | Web search backend | `baidu` |
| `BAIDU_SEARCH_API_KEY` | Baidu Qianfan search API key | — |

---

## License

This project is licensed under the [MIT License](LICENCE).

Copyright (c) 2026 Steve Sun
