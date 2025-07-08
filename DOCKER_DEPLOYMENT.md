# 🐳 Docker Deployment Guide - English Learning Platform

Questa guida ti aiuterà a deployare l'English Learning Platform utilizzando Docker.

## 📋 Prerequisiti

- **Docker** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git** per clonare il repository
- **8GB RAM** minimo raccomandato per Ollama
- **10GB spazio disco** per modelli AI

## 🚀 Quick Start

### 1. Clone e naviga nel progetto
```bash
git clone <repository-url>
cd adaptive-learning-platform
```

### 2. Avvio rapido (Sviluppo)
```bash
# Usando il Makefile (raccomandato)
make quick-start

# Oppure usando lo script direttamente
chmod +x deploy.sh
./deploy.sh --dev --setup-models
```

### 3. Accedi all'applicazione
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB**: mongodb://admin:password123@localhost:27017

## 🛠️ Comandi Disponibili

### Usando il Makefile (Raccomandato)
```bash
# Sviluppo
make dev              # Avvia ambiente di sviluppo
make dev-logs         # Visualizza logs di sviluppo
make dev-down         # Ferma ambiente di sviluppo

# Produzione
make prod             # Avvia ambiente di produzione
make prod-logs        # Visualizza logs di produzione
make prod-down        # Ferma ambiente di produzione

# Utilità
make build            # Build delle immagini
make health           # Controlla stato servizi
make clean            # Pulizia completa
make help             # Mostra tutti i comandi
```

### Usando Docker Compose direttamente
```bash
# Sviluppo
docker-compose -f docker-compose.dev.yml up -d --build
docker-compose -f docker-compose.dev.yml logs -f
docker-compose -f docker-compose.dev.yml down

# Produzione
docker-compose up -d --build
docker-compose logs -f
docker-compose down
```

## 🎯 Modalità di Deployment

### 🔧 Modalità Sviluppo
- **Hot reload** per backend e frontend
- **Volumi mappati** per sviluppo live
- **Debug abilitato**
- **Porta**: 3000 (frontend), 8000 (backend)

```bash
make dev
```

### 🏭 Modalità Produzione
- **Build ottimizzato**
- **Nginx reverse proxy**
- **Health checks**
- **Restart automatico**

```bash
make prod
```

## 🏗️ Architettura dei Container

```
┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │
│   (React App)   │────│   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘
          │                       │
          └───────────┬───────────┘
                      │
          ┌─────────────────┐    ┌─────────────────┐
          │    MongoDB      │    │     Ollama      │
          │   Port: 27017   │    │   Port: 11434   │
          └─────────────────┘    └─────────────────┘
```

## 📊 Monitoraggio e Debug

### Controllare lo stato dei servizi
```bash
make health
# oppure
docker-compose ps
```

### Visualizzare i logs
```bash
# Tutti i servizi
make logs

# Servizio specifico
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama
docker-compose logs -f mongodb
```

### Accesso shell ai container
```bash
# Backend
make shell-backend
docker-compose exec backend /bin/bash

# Frontend
docker-compose exec frontend /bin/sh

# MongoDB
make shell-mongodb
docker-compose exec mongodb mongosh "mongodb://admin:password123@localhost:27017/EnglishLearning?authSource=admin"

# Ollama
make shell-ollama
docker-compose exec ollama /bin/bash
```

## 🤖 Gestione Modelli Ollama

### Setup automatico dei modelli
```bash
make setup
```

### Setup manuale
```bash
# Accedi al container Ollama
docker-compose exec ollama /bin/bash

# Scarica modelli
ollama pull gemma2:2b
ollama pull llama3.2:3b
ollama pull llama3.2:1b

# Lista modelli installati
ollama list
```

### Modelli raccomandati
- **gemma2:2b** - Leggero, veloce (2GB)
- **llama3.2:3b** - Bilanciato (3GB)
- **llama3.2:1b** - Ultra leggero (1GB)

## 💾 Backup e Restore Database

### Backup
```bash
make db-backup
```

### Restore
```bash
make db-restore
```

## 🔧 Configurazione Avanzata

### Variabili d'ambiente personalizzate
Crea un file `.env.local`:
```bash
# Database
MONGO_URI=mongodb://admin:custompassword@mongodb:27017/EnglishLearning?authSource=admin

# Ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TEMPERATURE=0.5
OLLAMA_MAX_TOKENS=1500

# Learning settings
LEVEL_UP_THRESHOLD=85
LEVEL_DOWN_THRESHOLD=65
```

### Porta personalizzate
Modifica `docker-compose.yml`:
```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Cambia porta frontend
  backend:
    ports:
      - "9000:8000"  # Cambia porta backend
```

## 🚨 Troubleshooting

### Problema: Ollama non risponde
```bash
# Controlla logs
docker-compose logs ollama

# Riavvia Ollama
docker-compose restart ollama

# Verifica modelli
docker-compose exec ollama ollama list
```

### Problema: Backend non si connette al database
```bash
# Controlla MongoDB
docker-compose logs mongodb

# Verifica connessione
docker-compose exec backend python -c "
from app.db import get_db
print('DB connection:', get_db().name)
"
```

### Problema: Frontend non carica
```bash
# Controlla build frontend
docker-compose logs frontend

# Rebuild senza cache
docker-compose build --no-cache frontend
```

### Pulizia completa in caso di problemi
```bash
make clean-all
```

## 📈 Performance e Ottimizzazione

### Requisiti minimi
- **CPU**: 2 core
- **RAM**: 8GB (4GB per Ollama + 2GB per MongoDB + 2GB per app)
- **Disco**: 10GB liberi

### Ottimizzazioni per produzione
1. **Usa un reverse proxy** (Nginx incluso)
2. **Abilita SSL/TLS** per HTTPS
3. **Configura backup automatici**
4. **Monitora risorse** con Docker stats

```bash
# Monitoraggio risorse
docker stats
```

## 🔐 Sicurezza

### Produzione checklist
- [ ] Cambia password di default MongoDB
- [ ] Abilita SSL/TLS
- [ ] Configura firewall
- [ ] Usa secrets per password
- [ ] Aggiorna regolarmente le immagini base

### Password di default
- **MongoDB**: `admin` / `password123`

⚠️ **IMPORTANTE**: Cambia sempre le password di default in produzione!

## 📞 Supporto

Per problemi o domande:
1. Controlla i logs: `make logs`
2. Verifica lo stato: `make health`
3. Prova pulizia: `make clean`
4. Riavvia: `make restart`

---

🎉 **Buon apprendimento con la English Learning Platform!** 🚀
