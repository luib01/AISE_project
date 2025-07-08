# backend/app/config.py
"""
Configurazione centralizzata per l'applicazione.
Tutte le variabili d'ambiente sono definite qui.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Carica le variabili d'ambiente dal file .env nella directory backend
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Configurazione dell'applicazione"""
    
    # Database
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/EnglishLearning")
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")
    
    # Ollama API Settings
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "2000"))
    
    # Quiz Settings
    DEFAULT_QUIZ_QUESTIONS = int(os.getenv("DEFAULT_QUIZ_QUESTIONS", "4"))
    
    # Learning Levels
    ENGLISH_LEVELS = ["beginner", "intermediate", "advanced"]
    
    # Level Progression Thresholds
    LEVEL_UP_THRESHOLD = int(os.getenv("LEVEL_UP_THRESHOLD", "80"))  # Score needed to level up
    LEVEL_DOWN_THRESHOLD = int(os.getenv("LEVEL_DOWN_THRESHOLD", "60"))  # Score below which to level down
    MIN_QUIZZES_FOR_LEVEL_CHANGE = int(os.getenv("MIN_QUIZZES_FOR_LEVEL_CHANGE", "3"))
    
    @staticmethod
    def get_ollama_config():
        """Ritorna la configurazione Ollama completa"""
        return {
            "base_url": Config.OLLAMA_BASE_URL,
            "model": Config.OLLAMA_MODEL,
            "timeout": Config.OLLAMA_TIMEOUT,
            "options": {
                "temperature": Config.OLLAMA_TEMPERATURE,
                "max_tokens": Config.OLLAMA_MAX_TOKENS
            }
        }
    
    @staticmethod
    def get_available_models():
        """Lista dei modelli disponibili"""
        return [
            "llama3.1:8b",
            "llama3.2:3b",
            "gemma2:2b",
            "llama3.2:1b",
            "mistral:7b",
            "codellama:7b",
            "qwen2:7b",
            "phi3:mini"
        ]
    
    @staticmethod
    def validate_model(model_name: str) -> bool:
        """Verifica se il modello è valido"""
        return model_name in Config.get_available_models()

# Istanza globale della configurazione
config = Config()
