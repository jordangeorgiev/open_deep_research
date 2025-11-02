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
