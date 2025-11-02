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
