#!/bin/bash

# Enhanced Ollama initialization script for English Learning Platform
# This script ensures the model is available before starting the service

set -e  # Exit on any error

echo "🚀 Starting Ollama initialization..."

# Start Ollama service in background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    if [ ! -z "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    
    echo "Attempt $((attempt + 1))/$max_attempts: Waiting for Ollama..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Failed to start Ollama after $max_attempts attempts"
    exit 1
fi

# Check if model already exists
MODEL_NAME="mistral:7b"
echo "🔍 Checking if $MODEL_NAME is already available..."

if ollama list | grep -q "$MODEL_NAME"; then
    echo "✅ Model $MODEL_NAME is already available"
else
    echo "📥 Downloading model: $MODEL_NAME"
    echo "This may take several minutes depending on your internet connection..."
    
    # Pull the model with progress indication
    if ollama pull "$MODEL_NAME"; then
        echo "✅ Successfully downloaded $MODEL_NAME"
    else
        echo "❌ Failed to download $MODEL_NAME"
        exit 1
    fi
fi

# Verify the model is working
echo "🧪 Testing model functionality..."
if echo '{"model":"'$MODEL_NAME'","prompt":"Hello","stream":false}' | curl -s -X POST http://localhost:11434/api/generate -d @- > /dev/null; then
    echo "✅ Model test successful!"
else
    echo "⚠️  Model test failed, but continuing..."
fi

echo "🎉 Ollama setup complete!"
echo "📋 Available models:"
ollama list

# Keep the service running
echo "🔄 Keeping Ollama service running..."
wait $OLLAMA_PID
