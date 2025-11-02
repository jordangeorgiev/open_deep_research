# Open Deep Research Repository Overview

## Project Description
Open Deep Research is a configurable, fully open-source deep research agent that works across multiple model providers, search tools, and MCP (Model Context Protocol) servers. It enables automated research with parallel processing and comprehensive report generation.

## Repository Structure

### Root Directory
- `README.md` - Comprehensive project documentation with quickstart guide
- `pyproject.toml` - Python project configuration and dependencies
- `langgraph.json` - LangGraph configuration defining the main graph entry point
- `uv.lock` - UV package manager lock file
- `LICENSE` - MIT license
- `.env.example` - Environment variables template (not tracked)
- `docker-compose.yml` - Docker services for local setup (PostgreSQL, Redis, SearXNG)
- `test_local.py` - Local Ollama testing script
- `README_LOCAL.md` - Complete local setup guide for Ollama + SearXNG
- `LOCAL_SETUP_STATUS.md` - Current status of local implementation
- `FULL_OLLAMA_IMPLEMENTATION_COMPLETE.md` - Comprehensive Ollama implementation documentation
- `OLLAMA_REFACTORING_SUMMARY.md` - Technical summary of Ollama refactoring

### Core Implementation (`src/open_deep_research/`)
- `deep_researcher.py` - Main LangGraph implementation (entry point: `deep_researcher`)
- `configuration.py` - Configuration management and settings
- `state.py` - Graph state definitions and data structures  
- `prompts.py` - System prompts and prompt templates
- `utils.py` - Utility functions and helpers
- `files/` - Research output and example files

### Legacy Implementations (`src/legacy/`)
Contains two earlier research implementations:
- `graph.py` - Plan-and-execute workflow with human-in-the-loop
- `multi_agent.py` - Supervisor-researcher multi-agent architecture
- `legacy.md` - Documentation for legacy implementations
- `CLAUDE.md` - Legacy-specific Claude instructions
- `tests/` - Legacy-specific tests

### Security (`src/security/`)
- `auth.py` - Authentication handler for LangGraph deployment

### Testing (`tests/`)
- `run_evaluate.py` - Main evaluation script configured to run on deep research bench
- `evaluators.py` - Specialized evaluation functions  
- `prompts.py` - Evaluation prompts and criteria
- `pairwise_evaluation.py` - Comparative evaluation tools
- `supervisor_parallel_evaluation.py` - Multi-threaded evaluation

### Examples (`examples/`)
- `arxiv.md` - ArXiv research example
- `pubmed.md` - PubMed research example
- `inference-market.md` - Inference market analysis examples

### Local Ollama Examples (`examples/local_ollama_examples/`)
Complete local research examples using Ollama models and SearXNG:
- `example_quantum_computing.py` - Quantum error correction research
- `example_ai_safety.py` - AI alignment and safety techniques
- `example_climate_tech.py` - Direct air capture and carbon sequestration
- `example_medical_research.py` - mRNA vaccine technology beyond COVID-19
- `README.md` - Complete guide for running local examples
- `reports/` - Generated research reports from local examples

### Infrastructure (`scripts/`, `searxng/`)
- `scripts/setup_local.sh` - Automated local environment setup
- `scripts/test_searxng.sh` - SearXNG connection testing
- `searxng/settings.yml` - SearXNG search engine configuration

## Key Technologies
- **LangGraph** - Workflow orchestration and graph execution
- **LangChain** - LLM integration and tool calling
- **Multiple LLM Providers** - OpenAI, Anthropic, Google, Groq, DeepSeek, **Ollama (local)** support
- **Search APIs** - Tavily, OpenAI/Anthropic native search, DuckDuckGo, Exa, **SearXNG (local)**
- **MCP Servers** - Model Context Protocol for extended capabilities
- **Local Infrastructure** - Docker-based PostgreSQL, Redis, and SearXNG for fully offline operation

## Development Commands

### Cloud/API-based Development
- `uvx langgraph dev` - Start development server with LangGraph Studio
- `python tests/run_evaluate.py` - Run comprehensive evaluations
- `ruff check` - Code linting
- `mypy` - Type checking

### Local Ollama Development
- `docker-compose up -d` - Start local infrastructure (PostgreSQL, Redis, SearXNG)
- `docker-compose ps` - Check service status
- `docker-compose down` - Stop all services
- `python test_local.py` - Run local Ollama integration test
- `python examples/local_ollama_examples/example_*.py` - Run specific research examples
- `ollama list` - View installed Ollama models
- `ollama pull llama3.2:latest` - Install recommended model for English output

## Configuration
All settings configurable via:
- Environment variables (`.env` file)
- Web UI in LangGraph Studio
- Direct configuration modification

Key settings include model selection, search API choice, concurrency limits, and MCP server configurations.

## Recent Improvements (Latest Update)

### Local Ollama Support Enhancements
1. **Model Selection Fix**:
   - Changed default from `granite4:latest` to `llama3.2:latest`
   - **Reason**: Fixed Chinese language output issue - `llama3.2` has superior English instruction-following
   - All local examples now generate reports in English with proper formatting

2. **Tool Calling Robustness**:
   - Added `normalize_tool_parameters()` function in `utils.py`
   - **Fixes**: Parameter name mismatches between Ollama outputs and tool schemas
   - Handles `think_tool` parameter variations (`prompt`, `thought`, `question` → `reflection`)
   - Converts `searxng_search` singular `query` to plural `queries` automatically
   - **Result**: Eliminated all tool validation errors during execution

3. **Documentation Updates**:
   - Updated all local examples to use `llama3.2:latest`
   - Updated `examples/local_ollama_examples/README.md` with correct model recommendations
   - Added comprehensive setup guides and troubleshooting sections

### Technical Implementation Details
- **File**: `src/open_deep_research/utils.py:771-821`
- **Function**: `normalize_tool_parameters(tool_name, tool_input)`
- **Impact**: Cleaner execution logs, more reliable tool calling with Ollama models

### Verified Working Configuration
- **LLM**: `ollama:llama3.2:latest` (2GB, excellent English, fast)
- **Search**: SearXNG (localhost:8080)
- **Database**: PostgreSQL (localhost:5432)
- **Cache**: Redis
- **Report Quality**: High-quality English research reports with proper citations

### Recommended Ollama Models
- **Balanced (Recommended)**: `llama3.2:latest` - Best English quality, 2-4GB VRAM
- **High Quality**: `llama3.1:8b` or `mistral:latest` - Better reasoning, 8-10GB VRAM
- **Lightweight**: `llama3.2:1b` - Faster but lower quality, 2-3GB VRAM

### Known Issues (Minor)
- Occasional JSON parsing errors from Ollama structured output (harmless, retry logic handles it)
- Reports always complete successfully despite JSON errors in logs