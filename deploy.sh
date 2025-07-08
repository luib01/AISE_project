#!/bin/bash

# English Learning Platform - Deployment Script

set -e  # Exit on any error

echo "🚀 Starting English Learning Platform Deployment"
echo "================================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run docker compose command
docker_compose() {
    if command_exists docker-compose; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Parse command line arguments
ENVIRONMENT="production"
PULL_IMAGES=false
SETUP_MODELS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--development)
            ENVIRONMENT="development"
            shift
            ;;
        --pull)
            PULL_IMAGES=true
            shift
            ;;
        --setup-models)
            SETUP_MODELS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev, --development    Deploy in development mode with hot reload"
            echo "  --pull                  Pull latest images before deployment"
            echo "  --setup-models         Download and setup Ollama models"
            echo "  --help                  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🎯 Deployment mode: $ENVIRONMENT"

# Determine compose file
if [ "$ENVIRONMENT" = "development" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

# Pull images if requested
if [ "$PULL_IMAGES" = true ]; then
    echo "📥 Pulling latest images..."
    docker_compose -f $COMPOSE_FILE pull
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker_compose -f $COMPOSE_FILE down

# Build and start services
echo "🏗️  Building and starting services..."
docker_compose -f $COMPOSE_FILE up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
echo "   - MongoDB..."
until docker_compose -f $COMPOSE_FILE exec -T mongodb mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; do
    echo "     Waiting for MongoDB..."
    sleep 5
done
echo "   ✅ MongoDB is ready"

echo "   - Ollama..."
until docker_compose -f $COMPOSE_FILE exec -T ollama curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
    echo "     Waiting for Ollama..."
    sleep 5
done
echo "   ✅ Ollama is ready"

echo "   - Backend..."
until docker_compose -f $COMPOSE_FILE exec -T backend curl -s http://localhost:8000/ >/dev/null 2>&1; do
    echo "     Waiting for Backend..."
    sleep 5
done
echo "   ✅ Backend is ready"

# Setup Ollama models if requested
if [ "$SETUP_MODELS" = true ]; then
    echo "🤖 Setting up Ollama models..."
    docker_compose -f $COMPOSE_FILE exec ollama ollama pull gemma2:2b
    docker_compose -f $COMPOSE_FILE exec ollama ollama pull llama3.2:3b
    echo "   ✅ Models setup complete"
fi

# Show status
echo ""
echo "🎉 Deployment completed successfully!"
echo "================================================"
echo ""
echo "📊 Service Status:"
docker_compose -f $COMPOSE_FILE ps

echo ""
echo "🌐 Access URLs:"
if [ "$ENVIRONMENT" = "development" ]; then
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8000"
    echo "   API Docs:  http://localhost:8000/docs"
else
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8000"
    echo "   API Docs:  http://localhost:8000/docs"
fi
echo "   MongoDB:   mongodb://admin:password123@localhost:27017"
echo "   Ollama:    http://localhost:11434"

echo ""
echo "📝 Useful Commands:"
echo "   View logs:     docker_compose -f $COMPOSE_FILE logs -f"
echo "   Stop services: docker_compose -f $COMPOSE_FILE down"
echo "   Restart:       docker_compose -f $COMPOSE_FILE restart"
echo "   Shell access:  docker_compose -f $COMPOSE_FILE exec [service] /bin/bash"

echo ""
echo "✨ Happy learning! 🎓"
