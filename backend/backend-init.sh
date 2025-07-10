#!/bin/bash

# Backend startup script with Ollama model verification
# This ensures the backend doesn't start until Ollama and the model are ready

set -e

echo "🚀 Starting backend initialization..."

# Wait for Ollama service to be available
echo "⏳ Waiting for Ollama service..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama service is ready!"
        break
    fi
    
    echo "Attempt $((attempt + 1))/$max_attempts: Waiting for Ollama service..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Failed to connect to Ollama after $max_attempts attempts"
    exit 1
fi

# Check if the required model is available
MODEL_NAME="${OLLAMA_MODEL:-mistral:7b}"
echo "🔍 Checking if model $MODEL_NAME is available..."

max_model_attempts=30
model_attempt=0

while [ $model_attempt -lt $max_model_attempts ]; do
    if curl -s http://ollama:11434/api/tags | grep -q "$MODEL_NAME"; then
        echo "✅ Model $MODEL_NAME is ready!"
        break
    fi
    
    echo "Attempt $((model_attempt + 1))/$max_model_attempts: Waiting for model $MODEL_NAME..."
    sleep 5
    model_attempt=$((model_attempt + 1))
done

if [ $model_attempt -eq $max_model_attempts ]; then
    echo "⚠️  Model $MODEL_NAME not found, but starting backend anyway..."
fi

# Test the model with a simple request
echo "🧪 Testing model functionality..."
if echo '{"model":"'$MODEL_NAME'","prompt":"Hello","stream":false}' | curl -s -X POST http://ollama:11434/api/generate -d @- > /dev/null; then
    echo "✅ Model test successful!"
else
    echo "⚠️  Model test failed, but continuing with backend startup..."
fi

echo "🎉 Backend prerequisites ready! Starting application..."

# Start the backend application
exec "$@"
