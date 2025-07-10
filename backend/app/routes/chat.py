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
    # Enhanced teacher prompt for better educational responses
    teacher_instructions = """You are a friendly and supportive English teacher. Your role is to help students learn English effectively.

IMPORTANT RESPONSE GUIDELINES:
- Keep paragraphs SHORT (2-3 sentences maximum)
- Use simple, clear language appropriate for English learners
- Be encouraging and patient
- Provide practical examples when explaining concepts
- Break complex topics into digestible pieces
- Use bullet points or numbered lists when helpful
- Always be supportive and positive

TEACHING APPROACH:
- Explain grammar rules simply with examples
- Correct mistakes gently and constructively
- Provide context for vocabulary words
- Suggest practice exercises when appropriate
- Ask follow-up questions to engage the student
- Adapt your language level to the student's ability

Remember: Short paragraphs, clear explanations, and encouraging tone!"""

    # Build conversation context
    conversation_text = "\n\nConversation History:\n"
    for i, msg in enumerate(request.conversation):
        if i % 2 == 0:
            conversation_text += f"Student: {msg}\n"
        else:
            conversation_text += f"Teacher: {msg}\n"
    
    # Create the final prompt
    prompt_text = f"""{teacher_instructions}

{conversation_text}

Now respond as the English teacher. Keep your response in short, clear paragraphs (2-3 sentences each). Be helpful, encouraging, and educational:

Teacher:"""

    # Use centralized Ollama configuration
    ollama_config = config.get_ollama_config()
    api_url = f"{ollama_config['base_url']}/api/generate"
    
    payload = {
        "model": ollama_config['model'],
        "prompt": prompt_text,
        "stream": False,
        "options": {
            "temperature": 0.7,  # Slightly creative but consistent
            "num_predict": 300,   # Limit response length for shorter paragraphs
            "top_p": 0.9,
            "stop": ["\nStudent:", "\nTeacher:", "Student:", "Teacher:"],  # Stop at conversation breaks
            "repeat_penalty": 1.1
        }
    }

    try:
        response = requests.post(api_url, json=payload, timeout=ollama_config['timeout'])
        response.raise_for_status()
        data = response.json()

        bot_reply = data.get("response", "Sorry, I couldn't generate a response.")
        
        # Post-process the response to ensure good formatting
        formatted_reply = format_teacher_response(bot_reply)
        
        return {"reply": formatted_reply}
    except requests.exceptions.RequestException as e:
        return {"error": f"Ollama connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def format_teacher_response(response: str) -> str:
    """
    Format the AI response to ensure it follows teacher-like guidelines with short paragraphs.
    """
    if not response:
        return "I'm here to help you learn English! What would you like to practice today?"
    
    # Clean up the response
    response = response.strip()
    
    # Remove any unwanted prefixes
    prefixes_to_remove = ["Teacher:", "teacher:", "AI:", "Assistant:", "Response:"]
    for prefix in prefixes_to_remove:
        if response.startswith(prefix):
            response = response[len(prefix):].strip()
    
    # Split into sentences
    sentences = response.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Group sentences into short paragraphs (2-3 sentences each)
    paragraphs = []
    current_paragraph = []
    
    for sentence in sentences:
        current_paragraph.append(sentence)
        
        # Create new paragraph after 2-3 sentences
        if len(current_paragraph) >= 2:
            # Check if the next logical break point
            if (len(current_paragraph) == 3 or 
                any(keyword in sentence.lower() for keyword in ['example', 'for instance', 'let me', 'try this'])):
                paragraphs.append('. '.join(current_paragraph) + '.')
                current_paragraph = []
    
    # Add remaining sentences as a paragraph
    if current_paragraph:
        paragraphs.append('. '.join(current_paragraph) + '.')
    
    # Join paragraphs with double newlines for clear separation
    formatted_response = '\n\n'.join(paragraphs)
    
    # Ensure the response is encouraging and ends appropriately
    if not any(ending in formatted_response.lower() for ending in ['?', 'practice', 'try', 'help']):
        formatted_response += "\n\nWhat else would you like to practice?"
    
    return formatted_response

class TeacherChatRequest(BaseModel):
    message: str
    user_level: str = "beginner"  # beginner, intermediate, advanced
    learning_focus: str = "general"  # grammar, vocabulary, pronunciation, conversation, general

@router.post("/teacher-chat/")
async def teacher_chat(request: TeacherChatRequest):
    """
    Enhanced teacher chat that adapts to student level and learning focus.
    """
    # Level-specific language guidelines
    level_guidelines = {
        "beginner": "Use very simple vocabulary and short sentences. Explain basic concepts step by step.",
        "intermediate": "Use moderately complex vocabulary. Provide more detailed explanations with examples.",
        "advanced": "Use sophisticated vocabulary. Provide nuanced explanations and cultural context."
    }
    
    # Focus-specific teaching approaches
    focus_approaches = {
        "grammar": "Focus on grammar rules, provide examples, and explain the 'why' behind the rules.",
        "vocabulary": "Provide definitions, synonyms, usage examples, and memory techniques.",
        "pronunciation": "Give phonetic guidance, stress patterns, and practice suggestions.",
        "conversation": "Encourage natural dialogue, provide conversation starters, and give feedback.",
        "general": "Provide well-rounded support covering all aspects of English learning."
    }
    
    teacher_prompt = f"""You are an experienced English teacher. You are helping a {request.user_level} level student who wants to focus on {request.learning_focus}.

TEACHING GUIDELINES:
- {level_guidelines.get(request.user_level, level_guidelines["beginner"])}
- {focus_approaches.get(request.learning_focus, focus_approaches["general"])}

RESPONSE STYLE:
- Keep paragraphs very short (1-2 sentences)
- Use encouraging and supportive language
- Provide practical examples
- Ask engaging follow-up questions
- Give specific, actionable advice

Student Level: {request.user_level}
Learning Focus: {request.learning_focus}

Student says: "{request.message}"

Respond as their English teacher with short, clear paragraphs:"""

    # Use centralized Ollama configuration
    ollama_config = config.get_ollama_config()
    api_url = f"{ollama_config['base_url']}/api/generate"
    
    payload = {
        "model": ollama_config['model'],
        "prompt": teacher_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 250,  # Even shorter for focused responses
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    }

    try:
        response = requests.post(api_url, json=payload, timeout=ollama_config['timeout'])
        response.raise_for_status()
        data = response.json()

        bot_reply = data.get("response", "I'm here to help you learn English!")
        formatted_reply = format_teacher_response(bot_reply)
        
        return {
            "reply": formatted_reply,
            "student_level": request.user_level,
            "learning_focus": request.learning_focus,
            "teaching_tips": get_teaching_tips(request.learning_focus, request.user_level)
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Ollama connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def get_teaching_tips(focus: str, level: str) -> List[str]:
    """Provide additional teaching tips based on focus and level."""
    tips = {
        "grammar": {
            "beginner": ["Start with simple present tense", "Practice basic sentence structure", "Use visual aids"],
            "intermediate": ["Focus on perfect tenses", "Practice complex sentences", "Learn conditional structures"],
            "advanced": ["Master subjunctive mood", "Practice advanced conditionals", "Study formal writing structures"]
        },
        "vocabulary": {
            "beginner": ["Learn 10 new words daily", "Use flashcards", "Practice with images"],
            "intermediate": ["Study word families", "Learn phrasal verbs", "Practice collocations"],
            "advanced": ["Study idiomatic expressions", "Learn academic vocabulary", "Practice nuanced meanings"]
        },
        "pronunciation": {
            "beginner": ["Practice basic sounds", "Work on word stress", "Record yourself speaking"],
            "intermediate": ["Focus on sentence stress", "Practice linking sounds", "Work on intonation patterns"],
            "advanced": ["Master connected speech", "Practice accent reduction", "Work on presentation skills"]
        },
        "conversation": {
            "beginner": ["Practice basic greetings", "Learn simple questions", "Use everyday topics"],
            "intermediate": ["Practice expressing opinions", "Learn discussion phrases", "Work on fluency"],
            "advanced": ["Practice debate skills", "Learn formal register", "Master cultural references"]
        }
    }
    
    return tips.get(focus, {}).get(level, ["Keep practicing!", "Stay motivated!", "Ask questions!"])
