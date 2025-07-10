#!/bin/bash

# Script to setup Ollama models for English Learning Platform

echo "🚀 Setting up Ollama models for English Learning Platform..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "Waiting for Ollama service..."
  sleep 5
done

echo "✅ Ollama is ready!"

# List of models to download
MODELS=(
    "mistral:7b"
)

# Download models
for model in "${MODELS[@]}"; do
    echo "📥 Downloading model: $model"
    ollama pull "$model"
    if [ $? -eq 0 ]; then
        echo "✅ Successfully downloaded $model"
    else
        echo "❌ Failed to download $model"
    fi
done

echo "🎉 Ollama setup complete!"
echo "Available models:"
ollama list
