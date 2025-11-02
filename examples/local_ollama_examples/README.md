# Local Ollama Research Examples

This directory contains example research scripts that demonstrate the full capabilities of Open Deep Research using completely local infrastructure with zero external API dependencies.

## Overview

All examples use:
- **Local Ollama** (Llama 3.2 models) for all LLM operations
- **Local SearXNG** for web search (localhost:8080)
- **Local PostgreSQL** for state management (localhost:5432)
- **Local Redis** for caching

## Prerequisites

Before running these examples, ensure you have:

1. **Docker services running**:
   ```bash
   cd ../..  # Navigate to project root
   docker-compose up -d
   ```

2. **Ollama installed and running** with the llama3.2 model:
   ```bash
   ollama pull llama3.2:latest
   ```

3. **Python environment set up**:
   ```bash
   pip install -e .
   ```

## Available Examples

### 1. Quantum Computing Error Correction
**File**: `example_quantum_computing.py`

**Research Query**: "What are the most promising quantum error correction techniques currently being developed, and how do they compare in terms of practical implementation challenges and performance?"

**Topics Covered**:
- Surface codes, topological codes, and other QEC approaches
- Implementation challenges and hardware requirements
- Performance comparisons and benchmarks
- Practical applications and current state of the art

**Run**:
```bash
python examples/local_ollama_examples/example_quantum_computing.py
```

### 2. AI Safety and Alignment
**File**: `example_ai_safety.py`

**Research Query**: "What are the most effective techniques for AI alignment and safety in large language models? Compare approaches like RLHF, constitutional AI, and mechanistic interpretability."

**Topics Covered**:
- Reinforcement Learning from Human Feedback (RLHF)
- Constitutional AI and principle-based alignment
- Mechanistic interpretability approaches
- Effectiveness comparisons and limitations

**Run**:
```bash
python examples/local_ollama_examples/example_ai_safety.py
```

### 3. Climate Technology and Carbon Capture
**File**: `example_climate_tech.py`

**Research Query**: "What are the most promising direct air capture (DAC) and carbon sequestration technologies currently being developed? Compare their scalability, cost-effectiveness, and environmental impact."

**Topics Covered**:
- Direct air capture (DAC) technologies
- Carbon sequestration methods
- Scalability analysis
- Cost-effectiveness and environmental impact

**Run**:
```bash
python examples/local_ollama_examples/example_climate_tech.py
```

### 4. mRNA Vaccine Technology
**File**: `example_medical_research.py`

**Research Query**: "What are the latest developments in mRNA vaccine technology beyond COVID-19? Explore applications in cancer treatment, rare diseases, and personalized medicine."

**Topics Covered**:
- mRNA technology fundamentals
- Cancer vaccine applications
- Rare disease treatments
- Clinical trials and challenges

**Run**:
```bash
python examples/local_ollama_examples/example_medical_research.py
```

## Output

Each example generates a comprehensive research report saved to:
```
examples/local_ollama_examples/reports/<topic>_<timestamp>.md
```

Reports include:
- Research summary and key findings
- Detailed analysis from multiple sources
- Comparisons and evaluations
- Citations and references
- Timestamp and query metadata

## Execution Time

Typical execution time per example (with llama3.2:latest):
- **Simple queries**: 30-60 seconds
- **Complex queries**: 1-3 minutes
- **Time breakdown**:
  - Research brief generation: ~5 seconds
  - Per search iteration: ~5-10 seconds
  - Final report generation: ~10-15 seconds

## Customization

You can customize any example by:

1. **Changing the query**:
   ```python
   query = "Your custom research question here"
   ```

2. **Using different Ollama models**:
   ```python
   config = {
       "configurable": {
           "research_model": "ollama:llama3.1:8b",  # Different model
           # ... other settings
       }
   }
   ```

3. **Adjusting concurrency**:
   ```python
   "max_concurrent_research_units": 4,  # More parallel research
   ```

4. **Enabling clarification**:
   ```python
   "allow_clarification": True,  # Ask clarifying questions
   ```

## Running All Examples

To run all examples sequentially:

```bash
python examples/local_ollama_examples/example_quantum_computing.py
python examples/local_ollama_examples/example_ai_safety.py
python examples/local_ollama_examples/example_climate_tech.py
python examples/local_ollama_examples/example_medical_research.py
```

Or create a batch script:

```bash
# run_all_examples.sh
for example in examples/local_ollama_examples/example_*.py; do
    echo "Running $example..."
    python "$example"
    echo ""
done
```

## Troubleshooting

### Issue: "Model not found"
```bash
# Pull the required model
ollama pull llama3.2:latest
```

### Issue: "SearXNG not responding"
```bash
# Restart Docker services
docker-compose restart searxng
```

### Issue: "Connection refused to PostgreSQL"
```bash
# Check if services are running
docker-compose ps

# Restart if needed
docker-compose restart postgres
```

### Issue: "Slow performance"
- Use a smaller/faster model: `ollama:llama3.2:1b`
- Reduce concurrency: `max_concurrent_research_units: 1`
- Ensure GPU is being used by Ollama

## Performance Optimization

1. **Use appropriate model sizes**:
   - Fast/lightweight: `llama3.2:1b` (2-3 GB VRAM)
   - Balanced: `llama3.2:latest` (2-4 GB VRAM)
   - High quality: `llama3.1:8b` or `mistral:latest` (8-10 GB VRAM)

2. **Adjust concurrency based on hardware**:
   - 8GB VRAM: `max_concurrent_research_units: 1`
   - 16GB VRAM: `max_concurrent_research_units: 2`
   - 24GB+ VRAM: `max_concurrent_research_units: 3-4`

3. **Enable GPU acceleration**:
   - Ensure Ollama is using GPU (check with `ollama ps`)
   - Configure CUDA/ROCm if needed

## Architecture

Each example follows this workflow:

```
User Query
    ↓
Research Brief Generation (Ollama + JSON mode)
    ↓
Research Supervisor (Ollama + ReAct tool calling)
    ↓
[Loop: Parallel research units]
    │
    ├→ Researcher (Ollama + ReAct)
    ├→ Web Search (SearXNG)
    ├→ Summarization (Ollama)
    └→ Compression (Ollama + JSON mode)
    ↓
Final Report Generation (Ollama)
    ↓
Save Report to File
```

## Privacy and Security

All examples run **100% locally**:
- ✅ No data sent to external APIs
- ✅ No API keys required
- ✅ Complete privacy
- ✅ No rate limits
- ✅ Works offline (if SearXNG is configured for local sources)

## Next Steps

1. **Create your own examples**: Copy and modify any example script
2. **Experiment with models**: Try different Ollama models
3. **Tune prompts**: Modify queries for your specific needs
4. **Scale up**: Increase concurrency for faster research
5. **Add custom tools**: Extend the research capabilities

## Support

For issues, questions, or contributions:
- See the main project README
- Check the full implementation guide: `../../FULL_OLLAMA_IMPLEMENTATION_COMPLETE.md`
- Review the technical summary: `../../OLLAMA_REFACTORING_SUMMARY.md`

## License

MIT License - See main project LICENSE file
