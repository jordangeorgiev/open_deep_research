# Open Deep Research - Fully Local Setup Guide

Transform Open Deep Research into a completely local, API-free research agent using Ollama, SearXNG, and Docker containers. No external API keys required.

> **⚠️ IMPORTANT UPDATE - Recommended Model Change**
>
> **New Recommendation**: Use `llama3.2:latest` instead of `granite4:latest` for **English language reports**
>
> **Why?** Testing revealed that `granite4` models sometimes default to Chinese output despite English prompts and explicit language instructions. `llama3.2:latest` has superior English instruction-following and generates consistently high-quality English reports.
>
> **Quick Start**:
> ```bash
> ollama pull llama3.2:latest  # ~2GB, excellent English quality
> ```
>
> See [Optimized Model Selection](#optimized-model-selection) for detailed recommendations.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Optimized Model Selection](#optimized-model-selection)
- [Detailed Setup](#detailed-setup)
- [Configuration Guide](#configuration-guide)
- [Service Management](#service-management)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)
- [Advanced Usage](#advanced-usage)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Open Deep Research (LangGraph Agent)            │
│  - Research planning & coordination                          │
│  - Report generation & synthesis                             │
└──────────┬──────────────────┬────────────────────────────────┘
           │                  │
           │                  │
    ┌──────▼──────┐    ┌─────▼──────────┐    ┌───────────────┐
    │   Ollama    │    │   SearXNG      │    │ MCP Servers   │
    │ (Local LLM) │    │ (Web Search)   │    │ (Optional)    │
    │             │    │                │    │               │
    │ • Granite4  │    │ • Google       │    │ • Filesystem  │
    │ • Llama3.1  │    │ • DuckDuckGo   │    │ • SQLite      │
    │ • Qwen2.5   │    │ • Brave        │    │ • GitHub      │
    │ • Mistral   │    │ • Wikipedia    │    │               │
    └─────────────┘    └────────────────┘    └───────────────┘
           │                  │                       │
    ┌──────▼──────────────────▼───────────────────────▼────────┐
    │         PostgreSQL Database (State & Traces)             │
    └──────────────────────────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │  LangFuse / LangSmith Community     │
    │  (Observability & Tracing)          │
    └─────────────────────────────────────┘
```

### Key Components

- **Ollama**: Local LLM inference server with GPU acceleration
- **SearXNG**: Privacy-focused metasearch engine aggregating multiple sources
- **PostgreSQL**: Local database for state persistence
- **LangFuse/LangSmith**: Open-source observability and tracing
- **MCP Servers**: Optional Model Context Protocol tools (filesystem, databases, APIs)
- **Docker Compose**: Orchestrates all services

### Benefits

✅ **Zero External Dependencies** - No API keys, no cloud services
✅ **Complete Privacy** - All data stays on your local machine
✅ **No Rate Limits** - Unlimited research queries
✅ **Cost-Free** - No per-token pricing
✅ **Offline Capable** - Works without internet (except live web search)
✅ **Reproducible** - Docker ensures consistent environment
✅ **Customizable** - Swap models, adjust resources freely

---

## Prerequisites

### Hardware Requirements

**Minimum** (Development/Testing):
- CPU: 4+ cores
- RAM: 16GB
- Storage: 50GB free space
- GPU: Not required (CPU inference works but slower)

**Recommended** (Production/Research):
- CPU: 8+ cores
- RAM: 32GB
- Storage: 100GB+ SSD
- GPU: NVIDIA GPU with 8GB+ VRAM (RTX 3060, RTX 4060, or better)

**Optimal** (High-Performance Research):
- CPU: 16+ cores
- RAM: 64GB+
- Storage: 200GB+ NVMe SSD
- GPU: NVIDIA GPU with 24GB+ VRAM (RTX 4090, A6000, or better)

### Software Requirements

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux) - Latest version
- **Docker Compose** v2.0+ (included with Docker Desktop)
- **Git** - For cloning the repository
- **Python** 3.10+ (for local development)
- **uv** package manager (recommended) - Install via `pip install uv`

### GPU Support (Optional but Recommended)

For NVIDIA GPUs:
- **Windows**: Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- **Linux**: Install `nvidia-docker2` package
- **Mac**: GPU acceleration not available (Apple Silicon uses CPU)

Verify GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/open_deep_research.git
cd open_deep_research
```

### 2. Create Docker Compose File

Create `docker-compose.yml` in the project root:

```yaml
version: '3.8'

services:
  # Ollama LLM Server
  ollama:
    image: ollama/ollama:latest
    container_name: odr-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_KEEP_ALIVE=5m
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - odr_network

  # SearXNG Search Engine
  searxng:
    image: searxng/searxng:latest
    container_name: odr-searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
      - SEARXNG_SECRET=change-this-secret-key
    restart: unless-stopped
    networks:
      - odr_network
    depends_on:
      - redis

  # Redis (for SearXNG caching)
  redis:
    image: redis:alpine
    container_name: odr-redis
    command: redis-server --save 30 1 --loglevel warning
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - odr_network

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: odr-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=open_deep_research
      - POSTGRES_USER=researcher
      - POSTGRES_PASSWORD=local_dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - odr_network

  # LangFuse (Observability)
  langfuse:
    image: langfuse/langfuse:latest
    container_name: odr-langfuse
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://researcher:local_dev_password@postgres:5432/open_deep_research
      - NEXTAUTH_SECRET=local-dev-secret-change-in-production
      - NEXTAUTH_URL=http://localhost:3000
      - TELEMETRY_ENABLED=false
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - odr_network

networks:
  odr_network:
    driver: bridge

volumes:
  ollama_data:
  redis_data:
  postgres_data:
```

### 3. Create SearXNG Configuration

Create directory and config file:

```bash
mkdir -p searxng
```

Create `searxng/settings.yml`:

```yaml
use_default_settings: true

server:
  secret_key: "change-this-secret-in-production"
  limiter: false
  image_proxy: true
  method: "GET"

search:
  safe_search: 0
  autocomplete: ""
  default_lang: "en"
  formats:
    - html
    - json

ui:
  static_use_hash: true
  infinite_scroll: true
  default_theme: simple

enabled_engines:
  - google
  - duckduckgo
  - brave
  - wikipedia
  - arxiv
  - github
  - stackoverflow
  - reddit

engines:
  - name: google
    engine: google
    shortcut: go
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
  - name: brave
    engine: brave
    shortcut: br
  - name: wikipedia
    engine: wikipedia
    shortcut: wp
  - name: arxiv
    engine: arxiv
    shortcut: arx
  - name: github
    engine: github
    shortcut: gh
  - name: stackoverflow
    engine: stackoverflow
    shortcut: so
  - name: reddit
    engine: reddit
    shortcut: re
```

### 4. Start Services

```bash
# Start all containers
docker-compose up -d

# Verify all services are running
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
odr-ollama          Up                  0.0.0.0:11434->11434/tcp
odr-searxng         Up                  0.0.0.0:8080->8080/tcp
odr-redis           Up                  6379/tcp
odr-postgres        Up                  0.0.0.0:5432->5432/tcp
odr-langfuse        Up                  0.0.0.0:3000->3000/tcp
```

### 5. Download Optimized Models

Create `scripts/setup_models.sh`:

```bash
#!/bin/bash
set -e

echo "🤖 Downloading optimized models for deep research..."
echo ""

# IBM Granite 4 Models (Latest & Most Optimized)
echo "📥 Downloading IBM Granite 4 8B (Recommended)..."
docker exec odr-ollama ollama pull granite4:8b

echo "📥 Downloading IBM Granite 4 3B (Fast, for summarization)..."
docker exec odr-ollama ollama pull granite4:3b

# Alternative High-Performance Models
echo "📥 Downloading Qwen2.5 14B (High quality)..."
docker exec odr-ollama ollama pull qwen2.5:14b

echo "📥 Downloading Llama 3.1 8B (Balanced)..."
docker exec odr-ollama ollama pull llama3.1:8b

# Optional: Larger models for better quality
echo ""
echo "⚠️  Optional: Download larger models for better quality (requires more VRAM)"
echo "    Uncomment the lines below to enable:"
echo ""
# docker exec odr-ollama ollama pull granite4:20b
# docker exec odr-ollama ollama pull qwen2.5:32b
# docker exec odr-ollama ollama pull llama3.1:70b

echo ""
echo "✅ Model setup complete!"
echo ""
echo "📊 Downloaded models:"
docker exec odr-ollama ollama list
```

Run it:
```bash
chmod +x scripts/setup_models.sh
./scripts/setup_models.sh
```

### 6. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# === Ollama Configuration ===
OLLAMA_BASE_URL=http://localhost:11434

# === Search Configuration ===
SEARXNG_URL=http://localhost:8080

# === Observability ===
LANGFUSE_PUBLIC_KEY=pk-lf-local
LANGFUSE_SECRET_KEY=sk-lf-local
LANGFUSE_HOST=http://localhost:3000

# === Database ===
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=open_deep_research
POSTGRES_USER=researcher
POSTGRES_PASSWORD=local_dev_password

# === Application Settings ===
GET_API_KEYS_FROM_CONFIG=false
```

### 7. Test the Setup

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test SearXNG
curl "http://localhost:8080/search?q=artificial+intelligence&format=json"

# Test PostgreSQL
docker exec odr-postgres psql -U researcher -d open_deep_research -c "SELECT version();"
```

### 8. Start the Research Agent

```bash
# Install dependencies
uv pip install -e .

# Start LangGraph development server
uvx langgraph dev
```

Access the agent:
- **LangGraph Studio**: http://localhost:3000 (or the port shown in terminal)
- **LangFuse Dashboard**: http://localhost:3000
- **SearXNG Interface**: http://localhost:8080

---

## Optimized Model Selection

### ⭐ NEW: Recommended Configuration (Llama 3.2 - Best for English)

**For English language research reports**, Llama 3.2 is now the recommended model due to superior instruction-following and consistent English output:

**Optimal `.env` configuration:**

```bash
# Optimized for English reports and tool calling
SUMMARIZATION_MODEL=ollama:llama3.2:latest
RESEARCH_MODEL=ollama:llama3.2:latest
COMPRESSION_MODEL=ollama:llama3.2:latest
FINAL_REPORT_MODEL=ollama:llama3.2:latest
SEARCH_API=searxng
SEARXNG_URL=http://localhost:8080
```

**Model Characteristics:**

| Model | Size | VRAM | Speed | English Quality | Best For |
|-------|------|------|-------|-----------------|----------|
| **llama3.2:latest** | 3B | 2-4GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | English reports, tool calling |
| **llama3.2:1b** | 1B | 2GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Fast research, summarization |
| **llama3.1:8b** | 8B | 8GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | High-quality reasoning |
| **mistral:latest** | 7B | 6GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Balanced performance |

**Why Llama 3.2?**
- ✅ **Consistent English output** - No language switching issues
- ✅ **Superior instruction-following** - Respects language instructions in system prompts
- ✅ **Excellent tool calling** - Works well with ReAct-style tool execution
- ✅ **Lightweight** - Only 2-4GB VRAM required
- ✅ **Fast inference** - Quick response times
- ✅ **Well-tested** - Verified across all local examples

**Quick Start:**
```bash
# Install recommended model
ollama pull llama3.2:latest

# Test it
python test_local.py
```

### Alternative Configuration (IBM Granite 4)

IBM Granite 4 models are optimized for enterprise use with excellent efficiency (**Note**: May default to Chinese output):

**Default `.env` configuration:**

```bash
# Optimized for quality and speed
SUMMARIZATION_MODEL=ollama:granite4:3b
RESEARCH_MODEL=ollama:granite4:8b
COMPRESSION_MODEL=ollama:granite4:8b
FINAL_REPORT_MODEL=ollama:granite4:8b
```

**Model Characteristics:**

| Model | Size | VRAM | Speed | Quality | Best For |
|-------|------|------|-------|---------|----------|
| **granite4:3b** | 3B | 3GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Summarization, quick tasks |
| **granite4:8b** | 8B | 6GB | ⚡⚡ | ⭐⭐⭐⭐ | Research, compression, reports |
| **granite4:20b** | 20B | 14GB | ⚡ | ⭐⭐⭐⭐⭐ | High-quality final reports |

**Why IBM Granite 4?**
- ✅ Latest generation with improved efficiency and instruction following
- ✅ Excellent long-context understanding (128K tokens)
- ✅ Enhanced reasoning capabilities over Granite 3
- ✅ Better multilingual support
- ✅ Open-source Apache 2.0 license
- ✅ Lower VRAM requirements than equivalent models

### Alternative Model Configurations

#### Budget/Development Setup (8GB VRAM)

```bash
SUMMARIZATION_MODEL=ollama:granite4:3b
RESEARCH_MODEL=ollama:granite4:8b
COMPRESSION_MODEL=ollama:granite4:8b
FINAL_REPORT_MODEL=ollama:qwen2.5:7b
```

**VRAM Usage:** ~6-7GB total

#### Balanced Setup (16GB VRAM)

```bash
SUMMARIZATION_MODEL=ollama:granite4:3b
RESEARCH_MODEL=ollama:qwen2.5:14b
COMPRESSION_MODEL=ollama:qwen2.5:14b
FINAL_REPORT_MODEL=ollama:granite4:8b
```

**VRAM Usage:** ~12-14GB total

#### High-Performance Setup (24GB+ VRAM)

```bash
SUMMARIZATION_MODEL=ollama:granite4:8b
RESEARCH_MODEL=ollama:qwen2.5:32b
COMPRESSION_MODEL=ollama:qwen2.5:32b
FINAL_REPORT_MODEL=ollama:granite4:20b
```

**VRAM Usage:** ~20-22GB total

#### Maximum Quality Setup (48GB+ VRAM / Multi-GPU)

```bash
SUMMARIZATION_MODEL=ollama:granite4:8b
RESEARCH_MODEL=ollama:llama3.1:70b
COMPRESSION_MODEL=ollama:llama3.1:70b
FINAL_REPORT_MODEL=ollama:qwen2.5:72b
```

**VRAM Usage:** ~45-48GB total

### Model Comparison Table

| Model Family | Strengths | Weaknesses | Use Case |
|--------------|-----------|------------|----------|
| **IBM Granite 4** | Instruction following, efficiency, reasoning, multilingual | Fewer variants than others | General research, reports, all tasks |
| **Qwen 2.5** | Speed, multilingual, coding, wide range of sizes | Can be verbose | Fast research, summarization |
| **Llama 3.1** | Quality, reasoning, coherence, well-tested | Slower, high VRAM | Deep analysis, final reports |
| **Mistral** | Balanced speed/quality | Less context length | Medium-complexity tasks |
| **DeepSeek R1** | Reasoning, math, problem-solving | Very slow | Complex analytical tasks |

### Model Download Commands

```bash
# IBM Granite 4 (Recommended)
docker exec odr-ollama ollama pull granite4:3b
docker exec odr-ollama ollama pull granite4:8b
docker exec odr-ollama ollama pull granite4:20b

# Qwen 2.5 (Fast & High Quality)
docker exec odr-ollama ollama pull qwen2.5:1.5b
docker exec odr-ollama ollama pull qwen2.5:7b
docker exec odr-ollama ollama pull qwen2.5:14b
docker exec odr-ollama ollama pull qwen2.5:32b

# Llama 3.1 (Highest Quality)
docker exec odr-ollama ollama pull llama3.1:8b
docker exec odr-ollama ollama pull llama3.1:70b

# Mistral (Balanced)
docker exec odr-ollama ollama pull mistral:7b-instruct
docker exec odr-ollama ollama pull mixtral:8x7b

# DeepSeek R1 (Reasoning)
docker exec odr-ollama ollama pull deepseek-r1:7b
docker exec odr-ollama ollama pull deepseek-r1:14b
```

### Check Downloaded Models

```bash
docker exec odr-ollama ollama list
```

### Model Performance Tips

1. **Start Small**: Begin with 8B models, upgrade if quality insufficient
2. **Mix Sizes**: Use small models for summarization, large for reports
3. **Monitor VRAM**: Use `nvidia-smi` to watch GPU memory usage
4. **Adjust Concurrency**: Lower `MAX_CONCURRENT_RESEARCH_UNITS` if running out of memory
5. **Use Quantization**: Add `:q4_0` suffix for lower VRAM (e.g., `llama3.1:70b-q4_0`)

---

## Detailed Setup

### Step-by-Step Setup Script

Create `scripts/local_setup.sh`:

```bash
#!/bin/bash
set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Open Deep Research - Local Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi
echo "✅ Docker is running"

# Check Docker Compose
if ! docker-compose version > /dev/null 2>&1; then
    echo "❌ Error: Docker Compose not found"
    exit 1
fi
echo "✅ Docker Compose is available"

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p searxng
mkdir -p scripts
mkdir -p research_data
echo "✅ Directories created"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Please create docker-compose.yml from the setup guide"
    exit 1
fi

# Start services
echo ""
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services
echo ""
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

# Check Ollama
echo ""
echo "🤖 Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama may not be ready yet"
fi

# Check SearXNG
echo ""
echo "🔍 Checking SearXNG..."
if curl -s http://localhost:8080/search?q=test > /dev/null; then
    echo "✅ SearXNG is running"
else
    echo "⚠️  SearXNG may not be ready yet"
fi

# Check PostgreSQL
echo ""
echo "🗃️  Checking PostgreSQL..."
if docker exec odr-postgres pg_isready -U researcher > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL may not be ready yet"
fi

# Check LangFuse
echo ""
echo "📊 Checking LangFuse..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ LangFuse is running"
else
    echo "⚠️  LangFuse may not be ready yet"
fi

# Setup environment file
echo ""
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env created (review and adjust as needed)"
else
    echo "ℹ️  .env already exists"
fi

# Download models
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 Model Download"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Download recommended models now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./scripts/setup_models.sh
else
    echo "⏭️  Skipping model download"
    echo "   Run './scripts/setup_models.sh' later to download models"
fi

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "  1. Review .env configuration:"
echo "     nano .env"
echo ""
echo "  2. Install Python dependencies:"
echo "     uv pip install -e ."
echo ""
echo "  3. Start the research agent:"
echo "     uvx langgraph dev"
echo ""
echo "📊 Service URLs:"
echo "  • Ollama API:     http://localhost:11434"
echo "  • SearXNG:        http://localhost:8080"
echo "  • LangFuse:       http://localhost:3000"
echo "  • PostgreSQL:     localhost:5432"
echo ""
echo "📚 Documentation:"
echo "  • Full guide:     README_LOCAL.md"
echo "  • Troubleshoot:   README_LOCAL.md#troubleshooting"
echo ""
echo "🔧 Useful Commands:"
echo "  • View logs:      docker-compose logs -f"
echo "  • Stop services:  docker-compose down"
echo "  • Restart:        docker-compose restart"
echo ""
```

Make it executable:
```bash
chmod +x scripts/local_setup.sh
./scripts/local_setup.sh
```

---

## Configuration Guide

### Environment Variables Reference

Complete `.env` file with all options:

```bash
#############################################
# OPEN DEEP RESEARCH - LOCAL CONFIGURATION
#############################################

# === Ollama LLM Server ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_KEEP_ALIVE=5m  # Keep models in memory for 5 minutes

# === Model Selection (IBM Granite 4 Optimized) ===
SUMMARIZATION_MODEL=ollama:granite4:3b
SUMMARIZATION_MODEL_MAX_TOKENS=8192

RESEARCH_MODEL=ollama:granite4:8b
RESEARCH_MODEL_MAX_TOKENS=10000

COMPRESSION_MODEL=ollama:granite4:8b
COMPRESSION_MODEL_MAX_TOKENS=8192

FINAL_REPORT_MODEL=ollama:granite4:8b
FINAL_REPORT_MODEL_MAX_TOKENS=10000

# === Search Configuration ===
SEARCH_API=searxng
SEARXNG_URL=http://localhost:8080
MAX_CONTENT_LENGTH=50000  # Max chars from web pages

# === Research Behavior ===
MAX_CONCURRENT_RESEARCH_UNITS=3  # Parallel research threads
MAX_RESEARCHER_ITERATIONS=6      # Max supervisor iterations
MAX_REACT_TOOL_CALLS=10          # Max tool calls per iteration
ALLOW_CLARIFICATION=true         # Ask user clarifying questions

# === Database (PostgreSQL) ===
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=open_deep_research
POSTGRES_USER=researcher
POSTGRES_PASSWORD=local_dev_password

# === Observability (LangFuse) ===
LANGFUSE_PUBLIC_KEY=pk-lf-local
LANGFUSE_SECRET_KEY=sk-lf-local
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_ENABLED=true

# === Application Settings ===
GET_API_KEYS_FROM_CONFIG=false
MAX_STRUCTURED_OUTPUT_RETRIES=3

# === Optional: MCP Servers ===
MCP_FILESYSTEM_ENABLED=false
MCP_FILESYSTEM_URL=http://localhost:8001

MCP_SQLITE_ENABLED=false
MCP_SQLITE_URL=http://localhost:8002

MCP_GITHUB_ENABLED=false
MCP_GITHUB_URL=http://localhost:8003

# === Logging ===
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Performance Tuning

Adjust based on your hardware:

**Low-End System (8GB RAM, no GPU):**
```bash
MAX_CONCURRENT_RESEARCH_UNITS=1
MAX_RESEARCHER_ITERATIONS=4
SUMMARIZATION_MODEL=ollama:granite4:3b
RESEARCH_MODEL=ollama:granite4:8b
```

**Mid-Range System (16GB RAM, 8GB VRAM):**
```bash
MAX_CONCURRENT_RESEARCH_UNITS=3
MAX_RESEARCHER_ITERATIONS=6
SUMMARIZATION_MODEL=ollama:granite4:3b
RESEARCH_MODEL=ollama:granite4:8b
```

**High-End System (32GB+ RAM, 24GB+ VRAM):**
```bash
MAX_CONCURRENT_RESEARCH_UNITS=5
MAX_RESEARCHER_ITERATIONS=8
SUMMARIZATION_MODEL=ollama:granite4:8b
RESEARCH_MODEL=ollama:qwen2.5:32b
FINAL_REPORT_MODEL=ollama:granite4:20b
```

---

## Service Management

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d ollama

# Stop all services
docker-compose down

# Stop and remove volumes (DELETES DATA)
docker-compose down -v

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart ollama
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ollama
docker-compose logs -f searxng

# Last 100 lines
docker-compose logs --tail=100 ollama
```

### Service Health Checks

```bash
# Check all containers
docker-compose ps

# Ollama health
curl http://localhost:11434/api/tags

# SearXNG health
curl "http://localhost:8080/search?q=test&format=json"

# PostgreSQL health
docker exec odr-postgres pg_isready -U researcher

# Redis health
docker exec odr-redis redis-cli ping
```

### Manage Ollama Models

```bash
# List downloaded models
docker exec odr-ollama ollama list

# Download a model
docker exec odr-ollama ollama pull granite4:8b

# Remove a model
docker exec odr-ollama ollama rm granite4:20b

# Show model details
docker exec odr-ollama ollama show granite4:8b

# Run a test prompt
docker exec -it odr-ollama ollama run granite4:8b "What is AI?"
```

### Database Management

```bash
# Access PostgreSQL shell
docker exec -it odr-postgres psql -U researcher -d open_deep_research

# Backup database
docker exec odr-postgres pg_dump -U researcher open_deep_research > backup.sql

# Restore database
cat backup.sql | docker exec -i odr-postgres psql -U researcher -d open_deep_research

# View table sizes
docker exec odr-postgres psql -U researcher -d open_deep_research -c "\dt+"
```

---

## Troubleshooting

### Common Issues

#### Issue: Ollama is slow or unresponsive

**Symptoms:**
- Model takes forever to respond
- High CPU usage, low GPU usage
- Timeout errors

**Solutions:**

1. **Check GPU is being used:**
```bash
# Watch GPU usage
watch -n 1 nvidia-smi

# Check Ollama logs
docker logs odr-ollama | grep GPU
```

2. **Ensure GPU is available to Docker:**
```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

3. **Use smaller models:**
```bash
# Switch to lighter model
docker exec odr-ollama ollama pull granite4:3b
```

4. **Increase Docker memory:**
   - Docker Desktop → Settings → Resources → Memory: Set to 16GB+

5. **Reduce concurrency:**
```bash
# In .env
MAX_CONCURRENT_RESEARCH_UNITS=1
```

---

#### Issue: SearXNG returns no results

**Symptoms:**
- Empty search results
- Timeout errors
- "Failed to fetch" errors

**Solutions:**

1. **Check SearXNG is running:**
```bash
curl "http://localhost:8080/search?q=test&format=json"
```

2. **View SearXNG logs:**
```bash
docker logs odr-searxng
```

3. **Verify search engines enabled:**
   - Edit `searxng/settings.yml`
   - Ensure engines are not `disabled: true`

4. **Test specific engine:**
```bash
curl "http://localhost:8080/search?q=test&engines=duckduckgo&format=json"
```

5. **Restart SearXNG:**
```bash
docker-compose restart searxng
```

---

#### Issue: Out of memory errors

**Symptoms:**
- "CUDA out of memory"
- Container crashes
- System freezes

**Solutions:**

1. **Check VRAM usage:**
```bash
nvidia-smi
```

2. **Use quantized models:**
```bash
# Instead of full precision
docker exec odr-ollama ollama pull llama3.1:70b-q4_0
```

3. **Reduce concurrency:**
```bash
MAX_CONCURRENT_RESEARCH_UNITS=1
MAX_REACT_TOOL_CALLS=5
```

4. **Use smaller models:**
```bash
RESEARCH_MODEL=ollama:granite4:8b  # Instead of 20b or larger
```

5. **Increase swap (Linux):**
```bash
sudo swapon --show
sudo fallocate -l 32G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

#### Issue: LangFuse not loading

**Symptoms:**
- Can't access http://localhost:3000
- Database connection errors

**Solutions:**

1. **Check PostgreSQL is ready:**
```bash
docker exec odr-postgres pg_isready
```

2. **View LangFuse logs:**
```bash
docker logs odr-langfuse
```

3. **Reset LangFuse database:**
```bash
docker-compose down langfuse
docker-compose up -d langfuse
```

4. **Access LangFuse shell:**
```bash
docker exec -it odr-langfuse sh
```

---

#### Issue: Models download very slowly

**Symptoms:**
- `ollama pull` takes hours
- Network timeouts

**Solutions:**

1. **Use smaller models first:**
```bash
docker exec odr-ollama ollama pull granite4:3b  # ~2GB
```

2. **Check Docker network:**
```bash
docker exec odr-ollama ping -c 3 registry.ollama.ai
```

3. **Download models outside Docker:**
```bash
# Install Ollama locally
ollama pull granite4:8b

# Copy to Docker volume
docker cp ~/.ollama/models odr-ollama:/root/.ollama/
```

4. **Use mirrors (China/restricted regions):**
```yaml
# In docker-compose.yml
ollama:
  environment:
    - OLLAMA_MIRRORS=https://ollama-mirror.example.com
```

---

### Diagnostic Commands

```bash
# Check all services
docker-compose ps

# View resource usage
docker stats

# Check disk space
df -h

# Check Docker logs
docker-compose logs --tail=50

# Test Ollama API
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"granite4:8b","prompt":"Hello","stream":false}'

# Test SearXNG
curl "http://localhost:8080/search?q=artificial+intelligence&format=json&pageno=1"

# Check network connectivity
docker exec odr-ollama ping -c 3 google.com
```

### Reset Everything

If all else fails:

```bash
# Stop and remove everything
docker-compose down -v

# Remove Docker images
docker rmi ollama/ollama:latest searxng/searxng:latest langfuse/langfuse:latest postgres:15-alpine redis:alpine

# Remove volumes
docker volume rm open_deep_research_ollama_data
docker volume rm open_deep_research_postgres_data
docker volume rm open_deep_research_redis_data

# Start fresh
./scripts/local_setup.sh
```

---

## Performance Optimization

### GPU Optimization

1. **Enable Tensor Cores (NVIDIA RTX):**
```yaml
# docker-compose.yml
ollama:
  environment:
    - CUDA_VISIBLE_DEVICES=0
    - NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

2. **Multi-GPU Support:**
```bash
# Use specific GPU
docker-compose exec -e CUDA_VISIBLE_DEVICES=1 ollama ollama run granite4:8b

# Use all GPUs
docker-compose up --scale ollama=2
```

3. **Monitor GPU utilization:**
```bash
watch -n 0.5 nvidia-smi
```

### CPU Optimization (No GPU)

1. **Increase threads:**
```yaml
ollama:
  environment:
    - OLLAMA_NUM_THREADS=8  # Set to number of CPU cores
```

2. **Use quantized models:**
```bash
docker exec odr-ollama ollama pull granite4:8b-q4_0
```

3. **Reduce concurrency:**
```bash
MAX_CONCURRENT_RESEARCH_UNITS=1
```

### Network Optimization

1. **Cache search results:**
   - Redis already caches SearXNG results
   - Adjust TTL in `searxng/settings.yml`

2. **Pre-download models:**
```bash
# Download all models at once
for model in granite4:3b granite4:8b qwen2.5:14b llama3.1:8b; do
  docker exec odr-ollama ollama pull $model &
done
wait
```

3. **Use local model mirror:**
```yaml
ollama:
  environment:
    - OLLAMA_MODELS=/models  # Use local directory
```

### Storage Optimization

1. **Clean up old models:**
```bash
docker exec odr-ollama ollama list
docker exec odr-ollama ollama rm old-model-name
```

2. **Use SSD for Ollama:**
```yaml
ollama:
  volumes:
    - /fast/ssd/path/ollama:/root/.ollama
```

3. **Compress logs:**
```yaml
ollama:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

---

## Advanced Usage

### Custom MCP Servers

Create local MCP server for filesystem access:

1. **Create `mcp-servers/filesystem/Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install fastmcp
COPY server.py .
CMD ["python", "server.py"]
```

2. **Create `mcp-servers/filesystem/server.py`:**
```python
from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("Filesystem Server")

@mcp.tool()
def read_file(path: str) -> str:
    """Read a local file."""
    return Path(f"/data/{path}").read_text()

@mcp.tool()
def list_files(directory: str = ".") -> list[str]:
    """List files in directory."""
    return [str(p) for p in Path(f"/data/{directory}").iterdir()]

if __name__ == "__main__":
    mcp.run(host="0.0.0.0", port=8000)
```

3. **Add to `docker-compose.yml`:**
```yaml
  mcp-filesystem:
    build: ./mcp-servers/filesystem
    container_name: odr-mcp-filesystem
    ports:
      - "8001:8000"
    volumes:
      - ./research_data:/data:ro
    networks:
      - odr_network
```

4. **Enable in `.env`:**
```bash
MCP_FILESYSTEM_ENABLED=true
MCP_FILESYSTEM_URL=http://localhost:8001
```

### Custom Search Engines

Add more search engines to SearXNG:

```yaml
# searxng/settings.yml
engines:
  - name: pubmed
    engine: pubmed
    shortcut: pm
    timeout: 10

  - name: semantic-scholar
    engine: semantic_scholar
    shortcut: ss

  - name: google-scholar
    engine: google_scholar
    shortcut: gsc
```

### Batch Research Processing

Create `scripts/batch_research.py`:

```python
"""Run multiple research queries in batch."""
import asyncio
from langgraph_sdk import get_client

async def run_research(client, query: str):
    """Run a single research query."""
    thread = await client.threads.create()
    await client.runs.create(
        thread_id=thread["thread_id"],
        assistant_id="deep_researcher",
        input={"messages": [{"role": "user", "content": query}]}
    )
    return thread["thread_id"]

async def main():
    queries = [
        "Latest advances in quantum computing",
        "Impact of AI on healthcare",
        "Renewable energy trends 2024"
    ]

    client = get_client(url="http://localhost:3000")

    tasks = [run_research(client, q) for q in queries]
    results = await asyncio.gather(*tasks)

    print(f"Started {len(results)} research threads")
    for thread_id, query in zip(results, queries):
        print(f"  {thread_id}: {query}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python scripts/batch_research.py
```

### Monitoring & Alerts

Set up Prometheus + Grafana for monitoring:

```yaml
# docker-compose.yml
  prometheus:
    image: prom/prometheus:latest
    container_name: odr-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - odr_network

  grafana:
    image: grafana/grafana:latest
    container_name: odr-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - odr_network
```

---

## FAQ

**Q: Can this work completely offline?**
A: Yes, except for live web search. Pre-download models and use local data sources.

**Q: How much disk space do I need?**
A: Minimum 50GB. Each model:
- 3B model: ~2GB
- 8B model: ~4.7GB
- 20B model: ~12GB
- 32B model: ~19GB
- 70B model: ~40GB

**Q: Can I use Apple Silicon (M1/M2/M3)?**
A: Yes! Ollama supports Apple Silicon. Remove GPU sections from docker-compose.yml.

**Q: How do I backup my research?**
```bash
# Backup database
docker exec odr-postgres pg_dump -U researcher open_deep_research > backup.sql

# Backup files
cp -r research_data research_data_backup

# Backup models (optional, can re-download)
docker cp odr-ollama:/root/.ollama ./ollama_backup
```

**Q: Can I use commercial cloud models alongside local?**
A: Yes! Keep cloud provider configs and switch models per task.

**Q: How do I update containers?**
```bash
docker-compose pull
docker-compose up -d
```

---

## Resources

- **Ollama Documentation**: https://ollama.ai/docs
- **SearXNG Documentation**: https://docs.searxng.org
- **LangFuse Documentation**: https://langfuse.com/docs
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **IBM Granite Models**: https://www.ibm.com/granite

---

## License

This setup guide is part of the Open Deep Research project, licensed under MIT.

---

**Need help?** Open an issue on GitHub or check the troubleshooting section above.
