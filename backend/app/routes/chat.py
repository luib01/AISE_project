# app/routes/chat.py

import requests
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.config import config

router = APIRouter()

class ChatRequest(BaseModel):
    conversation: List[str]
    # e.g. ["Hello", "Hi! How can I help you learn English?", "I want to practice grammar..."]

@router.post("/chat/")
async def chat_with_model(request: ChatRequest):
    """
    Calls the local Ollama API for English learning assistance.
    """
    # Combines conversation into a single 'prompt'
    # Adds an instruction: "You are a helpful English tutor..."
    prompt_text = "You are a helpful English tutor. Help students learn English grammar, vocabulary, and pronunciation. Provide clear explanations and examples.\n\nConversation:\n"
    for i, msg in enumerate(request.conversation):
        prompt_text += f"{msg}\n"
    prompt_text += "\nAnswer the user clearly and help them improve their English:\n"

    # Usa la configurazione centralizzata
    ollama_config = config.get_ollama_config()
    api_url = f"{ollama_config['base_url']}/api/generate"
    
    payload = {
        "model": ollama_config['model'],
        "prompt": prompt_text,
        "stream": False,
        "options": ollama_config['options']
    }

    try:
        response = requests.post(api_url, json=payload, timeout=ollama_config['timeout'])
        response.raise_for_status()
        data = response.json()

        bot_reply = data.get("response", "Sorry, I couldn't generate a response.")
        
        return {"reply": bot_reply}
    except requests.exceptions.RequestException as e:
        return {"error": f"Ollama connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
