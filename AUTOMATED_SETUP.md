# Automated GPU-Enabled English Learning Platform Setup

## Overview

This document describes the fully automated setup for the English Learning Platform with GPU-enabled Ollama model deployment. The system now automatically pulls the required models and ensures all services start in the correct order.

## Automated Features

### 🤖 Ollama Model Management
- **Automatic Model Pulling**: The `mistral:7b` model is automatically downloaded on first startup
- **Custom Ollama Image**: Built with `Dockerfile.ollama` for enhanced initialization
- **Robust Startup**: `ollama-init.sh` ensures Ollama service starts and model is available before continuing
- **GPU Support**: Automatically detects and uses NVIDIA GPU if available

### 🔄 Backend Service Coordination
- **Smart Startup**: Backend waits for Ollama service and model to be ready via `backend-init.sh`
- **Model Verification**: Tests model functionality before starting the API
- **Graceful Fallback**: Continues startup even if model tests fail (with warnings)

### 📚 Enhanced AI Features
- **Teacher-Style Responses**: AI Teacher provides encouraging, short paragraphs as a language teacher
- **Adaptive Quiz Generation**: Always generates 4 questions, avoids repetition, uses user history
- **Level-Aware Teaching**: `/teacher-chat/` endpoint adapts to user's proficiency level

## Docker Commands

### Development Environment

#### Start Development Stack
```powershell
# Start all services in development mode with hot reload
docker-compose -f docker-compose.dev.yml up -d

# View logs for all services
docker-compose -f docker-compose.dev.yml logs -f

# View logs for specific service
docker-compose -f docker-compose.dev.yml logs -f backend-dev
docker-compose -f docker-compose.dev.yml logs -f ollama
```

#### Stop Development Stack
```powershell
# Stop all development services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v

# Stop and remove images as well
docker-compose -f docker-compose.dev.yml down -v --rmi all
```

### Production Environment

#### Start Production Stack
```powershell
# Start all services in production mode
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f ollama
```

#### Stop Production Stack
```powershell
# Stop all production services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Stop and remove images as well
docker-compose down -v --rmi all
```

## Service URLs

- **Frontend**: http://localhost:3000 (dev) / http://localhost (prod)
- **Backend API**: http://localhost:8000
- **Ollama API**: http://localhost:11434
- **MongoDB**: localhost:27017

## Startup Sequence

1. **MongoDB**: Database starts first
2. **Ollama**: Custom image starts, pulls `mistral:7b` if needed, verifies model
3. **Backend**: Waits for Ollama + model, then starts API server
4. **Frontend**: Starts last, connects to backend

## Model Configuration

The system is configured to use:
- **Model**: `mistral:7b` (configured in environment variables)
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Max Tokens**: 4000 (sufficient for educational content)
- **Timeout**: 180s dev / 240s prod (allows for longer responses)

## Troubleshooting

### If Model Download Fails
```powershell
# Check Ollama logs
docker-compose logs ollama

# Manually pull model (if needed)
docker-compose exec ollama ollama pull mistral:7b

# Restart services
docker-compose restart backend
```

### If Backend Can't Connect to Ollama
```powershell
# Check if Ollama is running
docker-compose ps ollama

# Test Ollama API
curl http://localhost:11434/api/tags

# Check backend logs
docker-compose logs backend
```

### If GPU Support Issues
```powershell
# Verify NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Check GPU allocation in containers
docker-compose exec ollama nvidia-smi
docker-compose exec backend nvidia-smi
```

## Environment Variables

Key configuration variables in docker-compose files:

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `OLLAMA_MODEL` | `mistral:7b` | `mistral:7b` | AI model to use |
| `OLLAMA_TIMEOUT` | `180` | `240` | Request timeout (seconds) |
| `DEFAULT_QUIZ_QUESTIONS` | `4` | `4` | Questions per quiz |
| `LEVEL_UP_THRESHOLD` | `80` | `80` | Score needed to level up |
| `MIN_QUIZZES_FOR_LEVEL_CHANGE` | `3` | `3` | Quizzes before level change |

## File Structure

```
AISE_project/
├── docker-compose.yml           # Production configuration
├── docker-compose.dev.yml       # Development configuration
├── Dockerfile.ollama            # Custom Ollama image
├── ollama-init.sh               # Ollama initialization script
├── backend/
│   ├── Dockerfile               # Production backend image
│   ├── Dockerfile.dev           # Development backend image
│   └── backend-init.sh          # Backend startup coordination
└── frontend/
    ├── Dockerfile               # Production frontend image
    └── Dockerfile.dev           # Development frontend image
```

## Next Steps

1. **Test Full Startup**: Run the development stack and verify all services start correctly
2. **Monitor Performance**: Check GPU utilization and model response times
3. **Scale if Needed**: Adjust timeouts or add health checks as required
4. **Documentation**: Update any team documentation with new startup procedures

The platform now provides a seamless, automated experience for developers and users with robust GPU-accelerated AI capabilities.
