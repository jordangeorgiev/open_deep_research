# Open Deep Research - Local Web UI Development Plan

## Executive Summary

This document outlines a comprehensive plan to develop a local web UI for Open Deep Research, providing an intuitive interface for conducting AI-powered research with full control over configuration, models, and research workflows.

**Key Objectives**:
- 🎨 Modern, intuitive web interface for research workflows
- ⚙️ Complete configuration management (models, search, parameters)
- 📚 Built-in research templates and examples
- 📊 Real-time research progress tracking
- 💾 Research history and report management
- 🔧 Zero external dependencies (fully local)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [UI/UX Design](#uiux-design)
4. [Features & Requirements](#features--requirements)
5. [API Design](#api-design)
6. [Data Models](#data-models)
7. [Implementation Phases](#implementation-phases)
8. [File Structure](#file-structure)
9. [Component Breakdown](#component-breakdown)
10. [Configuration Management](#configuration-management)
11. [Development Timeline](#development-timeline)
12. [Deployment Strategy](#deployment-strategy)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              React Web Application (UI)                     │ │
│  │  • Research Dashboard  • Configuration Panel                │ │
│  │  • Report Viewer       • Model Management                   │ │
│  │  • History Browser     • Template Library                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Server)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  REST API Endpoints:                                        │ │
│  │  • /api/research      • /api/config                         │ │
│  │  • /api/models        • /api/templates                      │ │
│  │  • /api/reports       • /api/health                         │ │
│  │                                                              │ │
│  │  WebSocket Endpoints:                                       │ │
│  │  • /ws/research       (real-time progress)                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         LangGraph Deep Researcher Integration               │ │
│  │  • Async research execution                                 │ │
│  │  • Progress streaming                                       │ │
│  │  • State management                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Local Infrastructure                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │   Ollama     │  │   SearXNG    │  │   PostgreSQL        │   │
│  │   (LLMs)     │  │   (Search)   │  │   (State/History)   │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │    Redis     │  │  File System │                            │
│  │   (Cache)    │  │   (Reports)  │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### Component Layers

1. **Presentation Layer** (React Frontend)
   - User interface components
   - Real-time updates via WebSocket
   - State management (React Context/Zustand)
   - Form validation and error handling

2. **API Layer** (FastAPI Backend)
   - RESTful API endpoints
   - WebSocket server for streaming
   - Request validation (Pydantic)
   - Authentication & authorization (optional)

3. **Business Logic Layer** (Python Services)
   - Research orchestration
   - Configuration management
   - Template processing
   - Report generation

4. **Integration Layer**
   - LangGraph deep_researcher integration
   - Ollama model management
   - Database operations
   - File system operations

5. **Infrastructure Layer**
   - Docker containers
   - PostgreSQL database
   - Redis cache
   - SearXNG search engine

---

## Technology Stack

### Frontend

**Core Framework**: React 18+ with TypeScript
- **Why**: Component-based, excellent ecosystem, TypeScript for type safety
- **Build Tool**: Vite (fast development, optimized builds)
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand (lightweight, simple API)
- **Forms**: React Hook Form + Zod validation
- **Data Fetching**: TanStack Query (React Query)
- **WebSocket**: native WebSocket API with reconnection logic
- **Markdown**: react-markdown with syntax highlighting
- **Charts**: Recharts (for research analytics)
- **Icons**: Lucide React

**Key Libraries**:
```json
{
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "vite": "^5.0.0",
  "tailwindcss": "^3.4.0",
  "zustand": "^4.5.0",
  "react-hook-form": "^7.50.0",
  "zod": "^3.22.0",
  "@tanstack/react-query": "^5.0.0",
  "react-markdown": "^9.0.0",
  "recharts": "^2.10.0",
  "lucide-react": "^0.300.0"
}
```

### Backend

**Core Framework**: FastAPI (Python 3.11+)
- **Why**: Fast, modern, async support, automatic OpenAPI docs
- **WebSocket**: FastAPI native WebSocket support
- **Validation**: Pydantic v2
- **Database ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Cache**: Redis client (aioredis)
- **Task Queue**: asyncio-based background tasks
- **File Storage**: Local filesystem with organized structure

**Key Libraries**:
```python
fastapi[all]==0.109.0
pydantic==2.6.0
sqlalchemy==2.0.25
alembic==1.13.0
redis[hiredis]==5.0.1
langchain-core
langgraph
```

### Database Schema

**PostgreSQL Tables**:
- `research_sessions` - Research execution records
- `research_reports` - Generated reports
- `configurations` - Saved configuration presets
- `templates` - Research templates
- `model_registry` - Available Ollama models
- `search_history` - Search query logs
- `user_preferences` - UI/UX preferences (optional)

### Development Tools

- **Linting**: ESLint (frontend), Ruff (backend)
- **Formatting**: Prettier (frontend), Black (backend)
- **Type Checking**: TypeScript compiler, mypy
- **Testing**: Vitest (frontend), pytest (backend)
- **API Documentation**: Swagger UI (auto-generated by FastAPI)
- **Container**: Docker & Docker Compose

---

## UI/UX Design

### Main Views

#### 1. **Dashboard (Home Page)**

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] Open Deep Research          [Settings] [History]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔍 New Research                                            │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Enter your research question...                       │ │
│  │                                                        │ │
│  │                                                        │ │
│  └───────────────────────────────────────────────────────┘ │
│  [⚙️ Quick Config ▼] [📚 Use Template ▼] [🚀 Start Research]│
│                                                             │
│  📊 Quick Stats                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 47       │ │ 12       │ │ 3 Active │ │ llama3.2 │      │
│  │ Reports  │ │ Templates│ │ Models   │ │ Current  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                             │
│  📋 Recent Research                                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ⏱️ 2 hours ago | Quantum Computing Error Correction   │ │
│  │ ⏱️ 1 day ago   | AI Safety Alignment Techniques       │ │
│  │ ⏱️ 3 days ago  | mRNA Vaccine Technology              │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  📖 Featured Templates                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │ Scientific │ │ Technology │ │ Market     │            │
│  │ Research   │ │ Analysis   │ │ Research   │            │
│  └────────────┘ └────────────┘ └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

#### 2. **Research Execution View**

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                              [⏸️] [⏹️]  │
├─────────────────────────────────────────────────────────────┤
│  Research: "Quantum Computing Error Correction"             │
│  Status: In Progress | Elapsed: 2m 34s                      │
│                                                             │
│  Progress Timeline                                          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ✅ Research brief generated                            │ │
│  │ ✅ Supervisor planning (2 parallel units)              │ │
│  │ 🔄 Unit 1: Surface code techniques (67%)              │ │
│  │    ├─ Search: surface code quantum error...           │ │
│  │    ├─ Found 8 sources                                 │ │
│  │    └─ Summarizing results...                          │ │
│  │ 🔄 Unit 2: Topological codes (43%)                    │ │
│  │    ├─ Search: topological quantum codes...            │ │
│  │    └─ Processing 6 sources...                         │ │
│  │ ⏳ Final report generation (pending)                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Live Output                                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ [14:32:18] Researcher 1: Analyzing surface codes...   │ │
│  │ [14:32:24] Found paper: "Fault-tolerant quantum..."   │ │
│  │ [14:32:30] Researcher 2: Comparing topological...     │ │
│  │ [14:32:35] Summarization: Processing 947 tokens...    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Configuration Used                                         │
│  Model: llama3.2:latest | Search: SearXNG | Units: 2       │
└─────────────────────────────────────────────────────────────┘
```

#### 3. **Configuration Panel**

```
┌─────────────────────────────────────────────────────────────┐
│  Configuration                        [Save Preset ▼] [Reset]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🤖 Model Configuration                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Research Model        [llama3.2:latest        ▼]      │ │
│  │ Summarization Model   [llama3.2:latest        ▼]      │ │
│  │ Compression Model     [llama3.2:latest        ▼]      │ │
│  │ Final Report Model    [llama3.1:8b            ▼]      │ │
│  │                                                        │ │
│  │ [📥 Manage Models] [🔄 Refresh Available Models]      │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  🔍 Search Configuration                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Search API           [SearXNG (Local)         ▼]      │ │
│  │ SearXNG URL          [http://localhost:8080         ] │ │
│  │ Max Results/Query    [10                    ] results │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ⚙️ Research Parameters                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Max Concurrent Units        [━━━━━━○────] 2           │ │
│  │ Max Research Iterations     [━━━━━○─────] 5           │ │
│  │ Max Tool Calls              [━━━━○──────] 5           │ │
│  │ Allow Clarification         [✓] Yes  [ ] No           │ │
│  │ Max Content Length          [100000         ] chars   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  💾 Database & Storage                                      │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ PostgreSQL URL       [postgresql://localhost:5432... ]│ │
│  │ Redis URL            [redis://localhost:6379        ] │ │
│  │ Report Output Dir    [./research_output             ] │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  [Test Configuration] [Apply] [Save as Default]            │
└─────────────────────────────────────────────────────────────┘
```

#### 4. **Model Management**

```
┌─────────────────────────────────────────────────────────────┐
│  Ollama Model Management               [🔄 Refresh] [➕ Pull]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Installed Models                                           │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ┌─────────────────────────────────────────────────┐   │ │
│  │ │ 🟢 llama3.2:latest           2.0 GB  ⭐ Default │   │ │
│  │ │ Size: 3B params | Modified: 2 hours ago         │   │ │
│  │ │ [Set Default] [Test] [Remove]                   │   │ │
│  │ └─────────────────────────────────────────────────┘   │ │
│  │                                                        │ │
│  │ ┌─────────────────────────────────────────────────┐   │ │
│  │ │ 🟢 llama3.1:8b               4.7 GB              │   │ │
│  │ │ Size: 8B params | Modified: 1 day ago           │   │ │
│  │ │ [Set Default] [Test] [Remove]                   │   │ │
│  │ └─────────────────────────────────────────────────┘   │ │
│  │                                                        │ │
│  │ ┌─────────────────────────────────────────────────┐   │ │
│  │ │ 🟢 mistral:latest            4.4 GB              │   │ │
│  │ │ Size: 7B params | Modified: 3 days ago          │   │ │
│  │ │ [Set Default] [Test] [Remove]                   │   │ │
│  │ └─────────────────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Recommended Models                                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ □ qwen2.5:7b         (Reasoning)      [Pull Model]    │ │
│  │ □ llama3.2:1b        (Lightweight)    [Pull Model]    │ │
│  │ □ deepseek-r1:8b     (Research)       [Pull Model]    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Model Usage Statistics                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ llama3.2:latest  █████████████████░░░  76% (38 uses) │ │
│  │ llama3.1:8b      ████████░░░░░░░░░░░░  32% (16 uses) │ │
│  │ mistral:latest   ███░░░░░░░░░░░░░░░░░  12% ( 6 uses) │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 5. **Templates Library**

```
┌─────────────────────────────────────────────────────────────┐
│  Research Templates                 [➕ Create] [📥 Import]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [All] [Scientific] [Technology] [Business] [Custom]       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔬 Scientific Research                               │   │
│  │ Comprehensive scientific literature review template │   │
│  │ • Optimized for academic papers and citations       │   │
│  │ • 3-5 parallel research units                        │   │
│  │ • Focus on peer-reviewed sources                     │   │
│  │ [Use Template] [Edit] [Duplicate]                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 💻 Technology Analysis                               │   │
│  │ Deep dive into emerging technologies and trends     │   │
│  │ • GitHub, documentation, and blog sources           │   │
│  │ • 2-4 parallel units for different aspects          │   │
│  │ • Code examples and implementation details          │   │
│  │ [Use Template] [Edit] [Duplicate]                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📊 Market Research                                   │   │
│  │ Competitive analysis and market trend research      │   │
│  │ • Business news and financial sources               │   │
│  │ • Company data and market reports                   │   │
│  │ • Comparison tables and metrics                      │   │
│  │ [Use Template] [Edit] [Duplicate]                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🏥 Medical/Clinical Research                         │   │
│  │ Evidence-based medical research template            │   │
│  │ • PubMed and clinical trial sources                 │   │
│  │ • Focus on systematic reviews and meta-analyses     │   │
│  │ • Clinical guidelines and best practices            │   │
│  │ [Use Template] [Edit] [Duplicate]                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 6. **Report Viewer**

```
┌─────────────────────────────────────────────────────────────┐
│  Quantum Computing Error Correction Report                  │
│  Generated: Nov 2, 2025 | Duration: 3m 45s | [⬇️] [🔗] [✏️] │
├─────────────────────────────────────────────────────────────┤
│  Sidebar                      │  Report Content             │
│  ──────────                   │  ──────────────             │
│  📄 Table of Contents         │  # Quantum Error Correction │
│    └─ Overview                │                             │
│    └─ Surface Codes          │  ## Overview                │
│    └─ Topological Codes      │                             │
│    └─ Comparison              │  Quantum error correction   │
│    └─ Conclusion              │  techniques are essential... │
│    └─ Sources (12)            │                             │
│                               │  ### Surface Code           │
│  ⚙️ Configuration Used        │                             │
│    • llama3.2:latest         │  The surface code is a...   │
│    • 2 concurrent units       │                             │
│    • SearXNG search          │  [1] Fowler et al. (2012)   │
│                               │  "Surface codes: Towards..." │
│  📊 Metrics                   │                             │
│    • Sources: 12              │  ### Topological Codes      │
│    • Searches: 8              │                             │
│    • Tokens: ~15.4K          │  Topological codes use...   │
│    • Quality: ⭐⭐⭐⭐⭐         │                             │
│                               │  ## Comparison              │
│  🏷️ Tags                      │                             │
│    quantum computing          │  | Feature | Surface |... │
│    error correction           │                             │
│    physics                    │  ## Sources                 │
│                               │                             │
│  [📋 Copy] [💾 Save] [🔄]    │  1. Fowler et al. "Surface..│
└─────────────────────────────────────────────────────────────┘
```

#### 7. **History Browser**

```
┌─────────────────────────────────────────────────────────────┐
│  Research History                [🔍 Search] [📅 Filter]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Filters: [All Time ▼] [All Models ▼] [All Tags ▼]        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Nov 2, 2025  14:32    ⏱️ 3m 45s    ⭐⭐⭐⭐⭐            │ │
│  │ Quantum Computing Error Correction Techniques         │ │
│  │ Model: llama3.2:latest | Sources: 12 | Size: 4.5KB   │ │
│  │ Tags: quantum, physics, error-correction              │ │
│  │ [View Report] [Re-run] [Delete]                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Nov 1, 2025  09:15    ⏱️ 2m 12s    ⭐⭐⭐⭐              │ │
│  │ AI Safety and Alignment Techniques                    │ │
│  │ Model: llama3.2:latest | Sources: 8 | Size: 3.2KB    │ │
│  │ Tags: ai-safety, alignment, ml                        │ │
│  │ [View Report] [Re-run] [Delete]                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Oct 31, 2025  16:47   ⏱️ 4m 33s    ⭐⭐⭐⭐⭐            │ │
│  │ mRNA Vaccine Technology Beyond COVID-19               │ │
│  │ Model: llama3.1:8b | Sources: 15 | Size: 6.1KB       │ │
│  │ Tags: medical, vaccines, biotechnology                │ │
│  │ [View Report] [Re-run] [Delete]                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Showing 1-10 of 47 results    [1] [2] [3] ... [5] [Next]  │
└─────────────────────────────────────────────────────────────┘
```

---

## Features & Requirements

### Core Features (MVP)

1. **Research Execution**
   - ✅ Text input for research queries
   - ✅ Real-time progress tracking via WebSocket
   - ✅ Pause/resume/cancel controls
   - ✅ Live output logs
   - ✅ Error handling and recovery

2. **Configuration Management**
   - ✅ Model selection (all 4 model types)
   - ✅ Search API configuration
   - ✅ Research parameters (concurrency, iterations, etc.)
   - ✅ Database/storage settings
   - ✅ Save/load configuration presets
   - ✅ Quick config templates

3. **Report Management**
   - ✅ View generated reports (markdown rendering)
   - ✅ Download reports (MD, PDF, HTML)
   - ✅ Share reports (copy link, export)
   - ✅ Tag and categorize reports
   - ✅ Search report history

4. **Model Management**
   - ✅ List installed Ollama models
   - ✅ Pull new models from UI
   - ✅ Remove unused models
   - ✅ Test model performance
   - ✅ Set default models
   - ✅ Model usage statistics

5. **Template Library**
   - ✅ Pre-built research templates
   - ✅ Create custom templates
   - ✅ Import/export templates
   - ✅ Template variables and customization
   - ✅ Category organization

### Advanced Features (Phase 2)

6. **Analytics & Insights**
   - 📊 Research quality metrics
   - 📊 Cost/time analysis per research
   - 📊 Model performance comparisons
   - 📊 Source reliability tracking
   - 📊 Usage trends and patterns

7. **Collaboration Features**
   - 👥 Share research sessions
   - 👥 Comment on reports
   - 👥 Export for citation tools
   - 👥 Research collections/projects

8. **Advanced Search**
   - 🔍 Full-text search across reports
   - 🔍 Advanced filters (date, model, tags, quality)
   - 🔍 Saved searches
   - 🔍 Search within specific reports

9. **Automation**
   - 🤖 Scheduled research runs
   - 🤖 Webhook integrations
   - 🤖 Batch processing
   - 🤖 Email notifications

10. **Developer Tools**
    - 🛠️ API playground
    - 🛠️ GraphQL explorer
    - 🛠️ Request/response inspector
    - 🛠️ System health monitoring

---

## API Design

### REST API Endpoints

#### Research Endpoints

```python
# Start new research
POST /api/research
Request:
{
  "query": "What are the latest advances in quantum computing?",
  "config": {
    "research_model": "ollama:llama3.2:latest",
    "max_concurrent_units": 2,
    ...
  },
  "template_id": "scientific" (optional)
}
Response:
{
  "session_id": "uuid-here",
  "status": "started",
  "websocket_url": "ws://localhost:8000/ws/research/uuid-here"
}

# Get research status
GET /api/research/{session_id}
Response:
{
  "session_id": "uuid",
  "status": "in_progress",
  "progress": 0.67,
  "current_step": "researcher_unit_2",
  "elapsed_seconds": 145,
  "estimated_remaining": 75
}

# Pause/Resume research
POST /api/research/{session_id}/pause
POST /api/research/{session_id}/resume

# Cancel research
POST /api/research/{session_id}/cancel

# Get research result
GET /api/research/{session_id}/result
Response:
{
  "session_id": "uuid",
  "status": "completed",
  "report": "# Full markdown report...",
  "metadata": {
    "duration_seconds": 220,
    "sources_count": 12,
    "token_usage": 15432
  }
}

# List research history
GET /api/research?limit=10&offset=0&filter=completed
Response:
{
  "total": 47,
  "items": [...]
}
```

#### Configuration Endpoints

```python
# Get current configuration
GET /api/config
Response:
{
  "research_model": "ollama:llama3.2:latest",
  "summarization_model": "ollama:llama3.2:latest",
  ...
}

# Update configuration
PUT /api/config
Request:
{
  "research_model": "ollama:llama3.1:8b",
  ...
}

# Save configuration preset
POST /api/config/presets
Request:
{
  "name": "High Quality Research",
  "description": "Uses llama3.1:8b for better results",
  "config": {...}
}

# List configuration presets
GET /api/config/presets

# Load preset
POST /api/config/presets/{preset_id}/load

# Validate configuration
POST /api/config/validate
Request: { config object }
Response:
{
  "valid": true,
  "warnings": ["High VRAM usage expected"],
  "errors": []
}
```

#### Model Management Endpoints

```python
# List installed models
GET /api/models
Response:
{
  "models": [
    {
      "name": "llama3.2:latest",
      "size_gb": 2.0,
      "params": "3B",
      "modified": "2025-11-02T10:30:00Z",
      "is_default": true
    }
  ]
}

# Pull new model
POST /api/models/pull
Request:
{
  "model_name": "mistral:latest"
}
Response:
{
  "task_id": "uuid",
  "status": "downloading",
  "progress": 0.15
}

# Remove model
DELETE /api/models/{model_name}

# Test model
POST /api/models/{model_name}/test
Request:
{
  "prompt": "Hello, world!"
}
Response:
{
  "response": "Hello! How can I help you?",
  "latency_ms": 245
}

# Set default model
POST /api/models/{model_name}/set-default
Request:
{
  "model_type": "research"  # or summarization, compression, final_report
}
```

#### Template Endpoints

```python
# List templates
GET /api/templates?category=scientific

# Get template
GET /api/templates/{template_id}
Response:
{
  "id": "uuid",
  "name": "Scientific Research",
  "category": "scientific",
  "description": "...",
  "config": {...},
  "variables": [
    {
      "name": "focus_area",
      "type": "string",
      "description": "Main research focus"
    }
  ]
}

# Create template
POST /api/templates
Request:
{
  "name": "Custom Template",
  "config": {...}
}

# Update template
PUT /api/templates/{template_id}

# Delete template
DELETE /api/templates/{template_id}

# Apply template to query
POST /api/templates/{template_id}/apply
Request:
{
  "query": "Research quantum computing",
  "variables": {
    "focus_area": "error correction"
  }
}
```

#### Report Management Endpoints

```python
# List reports
GET /api/reports?tag=quantum&sort=date_desc

# Get report
GET /api/reports/{report_id}

# Update report metadata
PATCH /api/reports/{report_id}
Request:
{
  "tags": ["quantum", "physics"],
  "rating": 5,
  "notes": "Excellent comprehensive analysis"
}

# Delete report
DELETE /api/reports/{report_id}

# Export report
GET /api/reports/{report_id}/export?format=pdf

# Search reports
POST /api/reports/search
Request:
{
  "query": "quantum error",
  "filters": {
    "date_from": "2025-10-01",
    "min_rating": 4
  }
}
```

#### System Endpoints

```python
# Health check
GET /api/health
Response:
{
  "status": "healthy",
  "services": {
    "ollama": "online",
    "searxng": "online",
    "postgres": "online",
    "redis": "online"
  }
}

# Get system info
GET /api/system/info
Response:
{
  "version": "1.0.0",
  "ollama_models_count": 3,
  "reports_count": 47,
  "storage_used_mb": 234.5
}

# Get statistics
GET /api/system/stats
Response:
{
  "total_research_sessions": 50,
  "avg_duration_seconds": 180,
  "total_reports_generated": 47,
  "top_models": [
    {"model": "llama3.2:latest", "usage": 38}
  ]
}
```

### WebSocket Endpoints

```python
# Real-time research progress
WS /ws/research/{session_id}

Messages sent to client:
{
  "type": "progress",
  "data": {
    "progress": 0.45,
    "current_step": "researcher_unit_1",
    "message": "Analyzing surface codes..."
  }
}

{
  "type": "log",
  "data": {
    "timestamp": "2025-11-02T14:32:18Z",
    "level": "info",
    "message": "Found 8 sources for query: surface code..."
  }
}

{
  "type": "complete",
  "data": {
    "session_id": "uuid",
    "report": "# Full report...",
    "metadata": {...}
  }
}

{
  "type": "error",
  "data": {
    "code": "MODEL_ERROR",
    "message": "Ollama connection failed"
  }
}
```

---

## Data Models

### Database Schema (SQLAlchemy)

```python
# models.py

class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(UUID, primary_key=True)
    query = Column(Text, nullable=False)
    status = Column(Enum("pending", "in_progress", "completed", "failed", "cancelled"))
    config = Column(JSONB)  # Full configuration snapshot
    template_id = Column(UUID, ForeignKey("templates.id"), nullable=True)

    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    report_id = Column(UUID, ForeignKey("reports.id"), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    sources_count = Column(Integer, default=0)
    token_usage = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="session")
    template = relationship("Template")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID, primary_key=True)
    session_id = Column(UUID, ForeignKey("research_sessions.id"))

    content = Column(Text, nullable=False)  # Markdown report
    title = Column(String(500))

    # User metadata
    tags = Column(ARRAY(String))
    rating = Column(Integer, nullable=True)  # 1-5 stars
    notes = Column(Text, nullable=True)

    # Auto-generated metadata
    word_count = Column(Integer)
    sources = Column(JSONB)  # List of source URLs and titles

    # Storage
    file_path = Column(String(1000))  # Path to saved .md file

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("ResearchSession", back_populates="report")


class ConfigurationPreset(Base):
    __tablename__ = "configuration_presets"

    id = Column(UUID, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    config = Column(JSONB, nullable=False)

    is_default = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # Built-in presets

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class Template(Base):
    __tablename__ = "templates"

    id = Column(UUID, primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    description = Column(Text)

    config = Column(JSONB)  # Configuration overrides
    variables = Column(JSONB)  # Template variables definition

    is_system = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    name = Column(String(200), primary_key=True)
    size_bytes = Column(BigInteger)
    params = Column(String(50))  # e.g., "3B", "8B"

    is_default_research = Column(Boolean, default=False)
    is_default_summarization = Column(Boolean, default=False)
    is_default_compression = Column(Boolean, default=False)
    is_default_final_report = Column(Boolean, default=False)

    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)

**Goal**: Set up basic architecture and infrastructure

**Tasks**:
1. ✅ Set up project structure
   - Create frontend (Vite + React + TypeScript)
   - Create backend (FastAPI + Python)
   - Set up Docker Compose for full stack

2. ✅ Database setup
   - PostgreSQL schema migration
   - SQLAlchemy models
   - Alembic configuration

3. ✅ Basic API implementation
   - Health check endpoints
   - Configuration endpoints
   - Model listing endpoint

4. ✅ Frontend scaffolding
   - React Router setup
   - Basic layout components
   - Tailwind CSS configuration
   - shadcn/ui component library

**Deliverables**:
- ✅ Running FastAPI server
- ✅ Running React dev server
- ✅ Docker Compose configuration
- ✅ Database migrations working
- ✅ Basic API documentation (Swagger)

---

### Phase 2: Research Execution (Week 3-4)

**Goal**: Implement core research functionality

**Tasks**:
1. ✅ LangGraph integration
   - Wrap deep_researcher for API use
   - Async execution handler
   - Progress tracking

2. ✅ WebSocket implementation
   - Real-time progress updates
   - Log streaming
   - Connection management

3. ✅ Research execution UI
   - Query input form
   - Progress visualization
   - Live output display
   - Error handling

4. ✅ Basic report viewer
   - Markdown rendering
   - Basic formatting
   - Download functionality

**Deliverables**:
- ✅ Working research execution
- ✅ Real-time progress updates
- ✅ Basic report viewing
- ✅ Error recovery

---

### Phase 3: Configuration & Models (Week 5-6)

**Goal**: Full configuration and model management

**Tasks**:
1. ✅ Configuration UI
   - All parameter controls
   - Form validation
   - Preset management

2. ✅ Model management
   - Ollama API integration
   - Pull/remove models
   - Model testing
   - Default model selection

3. ✅ Configuration persistence
   - Save/load presets
   - Default configuration
   - Import/export config

4. ✅ Advanced research controls
   - Pause/resume
   - Cancel
   - Re-run with modifications

**Deliverables**:
- ✅ Complete configuration panel
- ✅ Model management UI
- ✅ Configuration presets
- ✅ Full research controls

---

### Phase 4: Templates & History (Week 7-8)

**Goal**: Template system and research history

**Tasks**:
1. ✅ Template system
   - Template CRUD operations
   - Template variables
   - Category organization
   - Built-in templates

2. ✅ Research history
   - List/search previous research
   - Filter and sort
   - Pagination
   - Quick re-run

3. ✅ Report management
   - Tagging system
   - Rating system
   - Notes/annotations
   - Advanced search

4. ✅ Enhanced report viewer
   - Table of contents
   - Metadata display
   - Export options (PDF, HTML)

**Deliverables**:
- ✅ Working template system
- ✅ Complete history browser
- ✅ Enhanced report viewer
- ✅ Export functionality

---

### Phase 5: Polish & Optimization (Week 9-10)

**Goal**: UI/UX polish and performance

**Tasks**:
1. ✅ UI/UX refinement
   - Responsive design
   - Dark mode
   - Accessibility (WCAG 2.1)
   - Loading states

2. ✅ Performance optimization
   - API response caching
   - Frontend code splitting
   - Database query optimization
   - WebSocket reconnection logic

3. ✅ Analytics implementation
   - Usage statistics
   - Model performance metrics
   - Cost/time analysis

4. ✅ Testing & QA
   - Unit tests (frontend & backend)
   - Integration tests
   - E2E tests (Playwright)
   - Load testing

**Deliverables**:
- ✅ Polished, responsive UI
- ✅ Optimized performance
- ✅ Analytics dashboard
- ✅ Comprehensive test suite

---

### Phase 6: Advanced Features (Week 11-12)

**Goal**: Advanced features and documentation

**Tasks**:
1. ✅ Advanced analytics
   - Research quality metrics
   - Model comparison charts
   - Usage trends

2. ✅ Automation features
   - Scheduled research
   - Batch processing
   - Webhook integrations

3. ✅ Developer tools
   - API playground
   - System monitoring
   - Debug tools

4. ✅ Documentation
   - User guide
   - API documentation
   - Developer documentation
   - Video tutorials

**Deliverables**:
- ✅ Advanced feature set
- ✅ Complete documentation
- ✅ Production-ready system

---

## File Structure

```
open-deep-research-ui/
├── frontend/                      # React frontend
│   ├── public/
│   │   ├── favicon.ico
│   │   └── index.html
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── common/          # Shared components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Select.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   └── Toast.tsx
│   │   │   ├── layout/          # Layout components
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── MainLayout.tsx
│   │   │   ├── research/        # Research-related
│   │   │   │   ├── QueryInput.tsx
│   │   │   │   ├── ProgressTracker.tsx
│   │   │   │   ├── LiveOutput.tsx
│   │   │   │   └── QuickConfig.tsx
│   │   │   ├── config/          # Configuration
│   │   │   │   ├── ModelSelector.tsx
│   │   │   │   ├── SearchConfig.tsx
│   │   │   │   ├── ParameterSlider.tsx
│   │   │   │   └── PresetManager.tsx
│   │   │   ├── models/          # Model management
│   │   │   │   ├── ModelCard.tsx
│   │   │   │   ├── ModelPuller.tsx
│   │   │   │   ├── ModelTester.tsx
│   │   │   │   └── ModelStats.tsx
│   │   │   ├── templates/       # Templates
│   │   │   │   ├── TemplateCard.tsx
│   │   │   │   ├── TemplateEditor.tsx
│   │   │   │   └── TemplateVariables.tsx
│   │   │   ├── reports/         # Report viewing
│   │   │   │   ├── ReportViewer.tsx
│   │   │   │   ├── ReportSidebar.tsx
│   │   │   │   ├── TableOfContents.tsx
│   │   │   │   └── ExportMenu.tsx
│   │   │   └── history/         # History
│   │   │       ├── HistoryList.tsx
│   │   │       ├── HistoryFilter.tsx
│   │   │       └── HistoryCard.tsx
│   │   ├── pages/               # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ResearchPage.tsx
│   │   │   ├── ConfigPage.tsx
│   │   │   ├── ModelsPage.tsx
│   │   │   ├── TemplatesPage.tsx
│   │   │   ├── ReportPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── hooks/               # Custom hooks
│   │   │   ├── useResearch.ts
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useConfig.ts
│   │   │   ├── useModels.ts
│   │   │   └── useTemplates.ts
│   │   ├── api/                 # API clients
│   │   │   ├── client.ts
│   │   │   ├── research.ts
│   │   │   ├── config.ts
│   │   │   ├── models.ts
│   │   │   ├── templates.ts
│   │   │   └── reports.ts
│   │   ├── store/               # State management
│   │   │   ├── researchStore.ts
│   │   │   ├── configStore.ts
│   │   │   ├── uiStore.ts
│   │   │   └── authStore.ts (optional)
│   │   ├── types/               # TypeScript types
│   │   │   ├── research.ts
│   │   │   ├── config.ts
│   │   │   ├── models.ts
│   │   │   ├── templates.ts
│   │   │   └── api.ts
│   │   ├── utils/               # Utilities
│   │   │   ├── formatters.ts
│   │   │   ├── validators.ts
│   │   │   ├── constants.ts
│   │   │   └── helpers.ts
│   │   ├── styles/              # Global styles
│   │   │   ├── globals.css
│   │   │   └── tailwind.css
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── backend/                       # FastAPI backend
│   ├── app/
│   │   ├── api/                  # API routes
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── research.py
│   │   │   │   ├── config.py
│   │   │   │   ├── models.py
│   │   │   │   ├── templates.py
│   │   │   │   ├── reports.py
│   │   │   │   └── system.py
│   │   │   └── websockets.py
│   │   ├── core/                 # Core functionality
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── redis.py
│   │   │   ├── security.py (optional)
│   │   │   └── logger.py
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── research.py
│   │   │   ├── report.py
│   │   │   ├── config.py
│   │   │   ├── template.py
│   │   │   └── model_registry.py
│   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── research.py
│   │   │   ├── config.py
│   │   │   ├── models.py
│   │   │   ├── templates.py
│   │   │   └── reports.py
│   │   ├── services/             # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── research_service.py
│   │   │   ├── config_service.py
│   │   │   ├── model_service.py
│   │   │   ├── template_service.py
│   │   │   ├── report_service.py
│   │   │   └── ollama_service.py
│   │   ├── integrations/         # External integrations
│   │   │   ├── __init__.py
│   │   │   ├── langgraph.py
│   │   │   ├── ollama.py
│   │   │   └── searxng.py
│   │   ├── utils/                # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── progress.py
│   │   │   ├── validators.py
│   │   │   └── helpers.py
│   │   └── main.py
│   ├── alembic/                  # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── tests/                    # Backend tests
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_integrations/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docker/                        # Docker configurations
│   ├── frontend.Dockerfile
│   ├── backend.Dockerfile
│   └── nginx.conf
│
├── docker-compose.yml             # Full stack orchestration
├── docker-compose.dev.yml         # Development overrides
├── .env.example                   # Environment variables template
├── .gitignore
├── README.md
└── WEB_UI_DEVELOPMENT_PLAN.md    # This document
```

---

## Component Breakdown

### Frontend Components

#### 1. **Common Components** (`components/common/`)

**Button.tsx**
```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  onClick?: () => void;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading,
  disabled,
  icon,
  onClick,
  children
}) => {
  // Implementation with Tailwind classes
};
```

**Input.tsx**
```tsx
interface InputProps {
  type?: 'text' | 'number' | 'email' | 'password';
  label?: string;
  placeholder?: string;
  error?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  required?: boolean;
}

export const Input: React.FC<InputProps> = ({ ... }) => {
  // Implementation
};
```

#### 2. **Research Components** (`components/research/`)

**QueryInput.tsx**
```tsx
interface QueryInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  templateId?: string;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  value,
  onChange,
  onSubmit,
  loading,
  templateId
}) => {
  return (
    <div className="space-y-4">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-32 p-4 border rounded-lg"
        placeholder="Enter your research question..."
      />
      <div className="flex gap-4">
        <QuickConfigDropdown />
        <TemplateSelector />
        <Button
          onClick={onSubmit}
          loading={loading}
          disabled={!value.trim()}
        >
          Start Research
        </Button>
      </div>
    </div>
  );
};
```

**ProgressTracker.tsx**
```tsx
interface ProgressStep {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  substeps?: ProgressStep[];
}

interface ProgressTrackerProps {
  steps: ProgressStep[];
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ steps }) => {
  return (
    <div className="space-y-2">
      {steps.map(step => (
        <ProgressStepItem key={step.id} step={step} />
      ))}
    </div>
  );
};
```

#### 3. **Configuration Components** (`components/config/`)

**ModelSelector.tsx**
```tsx
interface ModelSelectorProps {
  label: string;
  value: string;
  onChange: (model: string) => void;
  modelType: 'research' | 'summarization' | 'compression' | 'final_report';
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  label,
  value,
  onChange,
  modelType
}) => {
  const { data: models } = useModels();

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 border rounded"
      >
        {models?.map(model => (
          <option key={model.name} value={model.name}>
            {model.name} ({model.params})
          </option>
        ))}
      </select>
    </div>
  );
};
```

### Backend Services

#### 1. **Research Service** (`services/research_service.py`)

```python
class ResearchService:
    def __init__(self, db: Session, redis: Redis):
        self.db = db
        self.redis = redis

    async def start_research(
        self,
        query: str,
        config: ResearchConfig,
        template_id: Optional[str] = None
    ) -> ResearchSession:
        """Start new research session"""
        # Create database record
        session = ResearchSession(
            id=uuid4(),
            query=query,
            status="pending",
            config=config.dict(),
            template_id=template_id
        )
        self.db.add(session)
        self.db.commit()

        # Queue for background execution
        await self._queue_research(session.id)

        return session

    async def execute_research(self, session_id: str):
        """Execute research in background"""
        session = self.db.query(ResearchSession).get(session_id)

        try:
            session.status = "in_progress"
            session.started_at = datetime.utcnow()
            self.db.commit()

            # Execute LangGraph research
            result = await self._run_langgraph_research(
                session.query,
                session.config
            )

            # Save report
            report = Report(
                id=uuid4(),
                session_id=session_id,
                content=result["report"],
                title=self._extract_title(result["report"]),
                sources=result["sources"]
            )
            self.db.add(report)

            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session.report_id = report.id

        except Exception as e:
            session.status = "failed"
            session.error_message = str(e)

        finally:
            self.db.commit()

    async def _run_langgraph_research(
        self,
        query: str,
        config: dict
    ) -> dict:
        """Execute research using LangGraph"""
        from open_deep_research.deep_researcher import deep_researcher

        # Convert config to LangGraph format
        langgraph_config = self._convert_config(config)

        # Execute research with progress tracking
        final_state = None
        async for event in deep_researcher.astream(
            {"messages": [HumanMessage(content=query)]},
            config=langgraph_config
        ):
            # Publish progress to WebSocket
            await self._publish_progress(event)

            # Update final state
            for node_name, node_output in event.items():
                final_state = node_output

        return {
            "report": final_state.get("final_report"),
            "sources": self._extract_sources(final_state)
        }
```

#### 2. **Model Service** (`services/model_service.py`)

```python
class ModelService:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client

    async def list_models(self) -> List[ModelInfo]:
        """List installed Ollama models"""
        models = await self.ollama.list()
        return [
            ModelInfo(
                name=m["name"],
                size_bytes=m["size"],
                params=self._extract_params(m["name"]),
                modified=m["modified_at"]
            )
            for m in models
        ]

    async def pull_model(self, model_name: str) -> AsyncIterator[PullProgress]:
        """Pull model from Ollama registry"""
        async for progress in self.ollama.pull(model_name):
            yield PullProgress(
                status=progress["status"],
                progress=progress.get("completed", 0) / progress.get("total", 1)
            )

    async def test_model(self, model_name: str, prompt: str) -> TestResult:
        """Test model with a prompt"""
        start_time = time.time()
        response = await self.ollama.generate(
            model=model_name,
            prompt=prompt
        )
        latency = (time.time() - start_time) * 1000

        return TestResult(
            response=response["response"],
            latency_ms=latency
        )
```

---

## Configuration Management

### Configuration Structure

```typescript
interface ResearchConfiguration {
  // Model Configuration
  models: {
    research: string;              // "ollama:llama3.2:latest"
    summarization: string;         // "ollama:llama3.2:latest"
    compression: string;           // "ollama:llama3.2:latest"
    finalReport: string;           // "ollama:llama3.1:8b"
  };

  // Search Configuration
  search: {
    api: 'searxng' | 'tavily' | 'duckduckgo' | 'exa';
    searxngUrl?: string;           // "http://localhost:8080"
    tavilyApiKey?: string;
    maxResultsPerQuery: number;    // 10
  };

  // Research Parameters
  research: {
    maxConcurrentUnits: number;    // 2
    maxResearchIterations: number; // 5
    maxToolCalls: number;          // 5
    allowClarification: boolean;   // false
    maxContentLength: number;      // 100000
  };

  // Model Parameters
  modelParams: {
    researchMaxTokens: number;     // 2048
    summarizationMaxTokens: number;// 1024
    compressionMaxTokens: number;  // 2048
    finalReportMaxTokens: number;  // 4096
    temperature: number;           // 0.7
  };

  // Database & Storage
  storage: {
    postgresUrl: string;           // "postgresql://..."
    redisUrl: string;              // "redis://localhost:6379"
    reportOutputDir: string;       // "./research_output"
  };
}
```

### Built-in Configuration Presets

```typescript
const PRESETS: Record<string, ResearchConfiguration> = {
  'fast-local': {
    name: 'Fast Local Research',
    description: 'Optimized for speed with lightweight models',
    models: {
      research: 'ollama:llama3.2:1b',
      summarization: 'ollama:llama3.2:1b',
      compression: 'ollama:llama3.2:1b',
      finalReport: 'ollama:llama3.2:latest'
    },
    research: {
      maxConcurrentUnits: 1,
      maxResearchIterations: 3,
      // ... other settings
    }
  },

  'balanced': {
    name: 'Balanced Quality & Speed',
    description: 'Recommended for most research tasks',
    models: {
      research: 'ollama:llama3.2:latest',
      summarization: 'ollama:llama3.2:latest',
      compression: 'ollama:llama3.2:latest',
      finalReport: 'ollama:llama3.2:latest'
    },
    research: {
      maxConcurrentUnits: 2,
      maxResearchIterations: 5,
      // ...
    }
  },

  'high-quality': {
    name: 'High Quality Research',
    description: 'Best quality with larger models',
    models: {
      research: 'ollama:llama3.1:8b',
      summarization: 'ollama:llama3.2:latest',
      compression: 'ollama:llama3.1:8b',
      finalReport: 'ollama:llama3.1:8b'
    },
    research: {
      maxConcurrentUnits: 3,
      maxResearchIterations: 8,
      // ...
    }
  },

  'scientific': {
    name: 'Scientific Research',
    description: 'Optimized for academic/scientific queries',
    models: {
      research: 'ollama:llama3.1:8b',
      summarization: 'ollama:llama3.2:latest',
      compression: 'ollama:llama3.1:8b',
      finalReport: 'ollama:llama3.1:8b'
    },
    research: {
      maxConcurrentUnits: 4,
      maxResearchIterations: 10,
      maxToolCalls: 8,
      // ...
    }
  }
};
```

---

## Development Timeline

### Week-by-Week Breakdown

**Weeks 1-2: Core Infrastructure**
- [ ] Project setup and tooling
- [ ] Database schema and migrations
- [ ] Basic API framework
- [ ] Frontend scaffolding
- [ ] Docker Compose configuration

**Weeks 3-4: Research Execution**
- [ ] LangGraph integration
- [ ] WebSocket implementation
- [ ] Research execution UI
- [ ] Progress tracking
- [ ] Report viewer (basic)

**Weeks 5-6: Configuration & Models**
- [ ] Configuration management
- [ ] Model management UI
- [ ] Ollama integration
- [ ] Preset system
- [ ] Advanced controls

**Weeks 7-8: Templates & History**
- [ ] Template system
- [ ] History browser
- [ ] Report management
- [ ] Advanced report viewer
- [ ] Export functionality

**Weeks 9-10: Polish & Optimization**
- [ ] UI/UX refinement
- [ ] Performance optimization
- [ ] Analytics implementation
- [ ] Testing suite
- [ ] Bug fixes

**Weeks 11-12: Advanced Features**
- [ ] Advanced analytics
- [ ] Automation features
- [ ] Developer tools
- [ ] Documentation
- [ ] Production deployment

**Total Timeline**: 12 weeks (3 months)

---

## Deployment Strategy

### Development Environment

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/frontend.Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev

  backend:
    build:
      context: ./backend
      dockerfile: ../docker/backend.Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ../src:/app/open_deep_research
    environment:
      - DATABASE_URL=postgresql://researcher:password@postgres:5432/odr_ui
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - searxng
      - ollama
    command: uvicorn app.main:app --reload --host 0.0.0.0

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: odr_ui
      POSTGRES_USER: researcher
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine

  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ../searxng:/etc/searxng

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  ollama_data:
```

### Production Environment

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: ../docker/backend.Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    command: uvicorn app.main:app --host 0.0.0.0 --workers 4
    restart: unless-stopped

  # ... postgres, redis, searxng, ollama (same as dev)
```

### Environment Variables

```bash
# .env.example

# Database
DATABASE_URL=postgresql://researcher:password@localhost:5432/odr_ui
REDIS_URL=redis://localhost:6379

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Ollama
OLLAMA_HOST=http://localhost:11434

# SearXNG
SEARXNG_URL=http://localhost:8080

# Storage
REPORT_OUTPUT_DIR=./research_output
MAX_UPLOAD_SIZE_MB=10

# Security (optional)
SECRET_KEY=your-secret-key-here
ENABLE_AUTH=false

# Logging
LOG_LEVEL=INFO
```

---

## Next Steps

### Immediate Actions (Before Development)

1. **Review and Approve Plan**
   - [ ] Review architecture decisions
   - [ ] Confirm technology stack
   - [ ] Approve UI/UX designs
   - [ ] Finalize timeline

2. **Environment Setup**
   - [ ] Set up development machines
   - [ ] Install required tools (Node.js, Python, Docker)
   - [ ] Clone repository
   - [ ] Set up local Ollama

3. **Team Organization**
   - [ ] Assign roles (frontend dev, backend dev, full-stack)
   - [ ] Set up communication channels
   - [ ] Schedule daily standups
   - [ ] Create project board (GitHub Projects / Jira)

4. **Documentation Preparation**
   - [ ] Create developer onboarding guide
   - [ ] Set up code style guides
   - [ ] Prepare API documentation template
   - [ ] Create PR template

### Success Criteria

**Phase 1 Success Metrics**:
- ✅ All services running in Docker
- ✅ API health check returns 200
- ✅ Frontend loads without errors
- ✅ Database migrations successful

**MVP Success Metrics**:
- ✅ Can execute research from UI
- ✅ Real-time progress updates work
- ✅ Reports display correctly
- ✅ Configuration can be saved/loaded

**Production Success Metrics**:
- ✅ 99% uptime
- ✅ < 2s page load time
- ✅ < 500ms API response time
- ✅ Zero critical bugs
- ✅ Complete test coverage (>80%)

---

## Conclusion

This plan provides a comprehensive roadmap for building a production-ready local web UI for Open Deep Research. The architecture is designed to be:

- **Scalable**: Can handle multiple concurrent research sessions
- **Maintainable**: Clean separation of concerns, well-documented
- **User-Friendly**: Intuitive UI with comprehensive features
- **Local-First**: Zero external dependencies, fully offline capable
- **Extensible**: Easy to add new features and integrations

**Estimated Development Time**: 12 weeks with 1-2 developers
**Recommended Team**: 1 full-stack developer or 1 frontend + 1 backend developer

The phased approach allows for incremental delivery and testing, ensuring a stable product at each milestone.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-02
**Author**: Claude Code Development Team
