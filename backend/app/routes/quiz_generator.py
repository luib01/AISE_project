# backend/app/routes/quiz_generator.py
import requests
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.config import config
from app.models.learning_model import get_user_profile, update_english_level
from app.routes.auth import get_current_user

router = APIRouter()

class AdaptiveQuizRequest(BaseModel):
    topic: str  # e.g., "Grammar", "Vocabulary", "Tenses", "Mixed"
    num_questions: int = 4
    force_difficulty: Optional[str] = None  # Optional override for difficulty
    previous_questions: Optional[List[str]] = []  # Previous questions to avoid repetition

class GeneratedQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    topic: str
    difficulty: str

@router.post("/generate-adaptive-quiz/")
async def generate_adaptive_quiz(
    request: AdaptiveQuizRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate an adaptive English quiz based on user's current level and performance.
    Takes into account previous questions to avoid repetition and ensures variety.
    
    IMPORTANT: The AI prompt is designed to ensure that the correct_answer field
    always contains exactly one of the provided options. This is critical for
    quiz validation and scoring. If modifying the prompt, maintain this requirement.
    """
    try:
        print(f"DEBUG: Starting quiz generation for user {current_user['user_id']}")
        
        # Use authenticated user's ID
        user_id = current_user["user_id"]
        
        print(f"DEBUG: Getting user profile for {user_id}")
        
        # Get user profile to determine current English level
        user_profile = get_user_profile(user_id)
        current_level = user_profile.get("english_level", "beginner")
        
        print(f"DEBUG: User level: {current_level}")
        
        # Use forced difficulty if provided, otherwise use user's level
        difficulty = request.force_difficulty or current_level
        
        # Get user's weak topics for targeted practice
        progress = user_profile.get("progress", {})
        weak_topics = [topic for topic, score in progress.items() if score < 70]
        
        # Get user's quiz history to analyze patterns
        quiz_history = user_profile.get("quiz_history", [])
        recent_topics = [quiz.get("topic", "") for quiz in quiz_history[-10:]]  # Last 10 quizzes
        recent_subtopics = []
        for quiz in quiz_history[-5:]:  # Last 5 quizzes
            recent_subtopics.extend(quiz.get("subtopics_covered", []))
        
        # Craft adaptive prompt based on level, weak areas, and previous questions
        level_descriptions = {
            "beginner": "basic English concepts, simple grammar, common vocabulary, present/past tense",
            "intermediate": "more complex grammar structures, intermediate vocabulary, context-dependent questions, conditional sentences, perfect tenses",
            "advanced": "advanced grammar, nuanced vocabulary, complex sentence structures, idiomatic expressions, subjunctive mood, advanced collocations"
        }
        
        # Build focus areas section
        focus_areas = ""
        if weak_topics:
            focus_areas = f"Focus especially on these areas where the student needs improvement: {', '.join(weak_topics[:3])}. "
        
        # Build variety instructions based on recent activity
        variety_instructions = ""
        if recent_topics:
            topic_counts = {}
            for topic in recent_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            most_frequent_topic = max(topic_counts, key=topic_counts.get) if topic_counts else None
            
            if most_frequent_topic and topic_counts[most_frequent_topic] >= 3:
                variety_instructions = f"The student has practiced '{most_frequent_topic}' frequently recently. "
                if request.topic.lower() == most_frequent_topic.lower():
                    variety_instructions += f"Since this is another {request.topic} quiz, focus on different subtopics or question types than usual. "
        
        if recent_subtopics:
            variety_instructions += f"Avoid these recently covered subtopics if possible: {', '.join(set(recent_subtopics[-8:]))}. "
        
        # Build previous questions avoidance section
        previous_questions_text = ""
        if request.previous_questions:
            previous_questions_text = f"""
        IMPORTANT: Avoid creating questions similar to these previous ones:
        {chr(10).join([f"- {q}" for q in request.previous_questions[-10:]])}
        
        Create completely different questions with different vocabulary, grammar points, and question formats.
        """
        
        # Topic-specific instructions
        topic_specific_instructions = {
            "Grammar": "Include varied grammar points: verb tenses, articles, prepositions, conditionals, passive voice, word order. Mix question types: fill-in-the-blank, error correction, sentence completion.",
            "Vocabulary": "Cover different aspects: word meanings, synonyms/antonyms, collocations, word formation, context clues. Include various word types: nouns, verbs, adjectives, adverbs.",
            "Reading": "For Reading comprehension, you MUST include a short passage (2-3 paragraphs, 150-250 words) followed by comprehension questions. The passage should be appropriate for the student's level and cover topics like: main ideas, specific details, inference, vocabulary in context, author's purpose. Include the passage text in the 'passage' field for each Reading question.",
            "Usage": "Focus on practical English: common expressions, idioms, formal vs informal language, appropriate register, cultural context.",
            "Mixed": "Create exactly 4 questions covering different English skills: Question 1 should be Grammar-focused, Question 2 should be Vocabulary-focused, Question 3 should be Reading comprehension (with a short passage), and Question 4 should be Usage-focused. This ensures comprehensive practice across all major English learning areas."
        }
        
        topic_instruction = topic_specific_instructions.get(request.topic, "Create diverse questions appropriate for English learners.")
        
        prompt = f"""
        You are an expert English teacher creating a personalized quiz for a {difficulty} level student.
        
        {focus_areas}
        {variety_instructions}
        
        TOPIC: {request.topic}
        LEVEL: {difficulty} - {level_descriptions.get(difficulty, 'appropriate for their level')}
        
        {topic_instruction}
        
        {previous_questions_text}
        
        Create EXACTLY 4 multiple choice questions for the topic: {request.topic}
        
        Requirements:
        - Questions MUST be {difficulty} level appropriate
        - Each question MUST have exactly 4 options (A, B, C, D)
        - The correct_answer MUST be EXACTLY one of the 4 options provided (word-for-word match)
        - NEVER create a correct_answer that is different from the options
        - The correct_answer field must contain the EXACT text from one of the options array
        - Provide clear, educational explanations for correct answers
        - Make questions engaging and practical for real-world English use
        - Ensure variety in question types and subtopics within {request.topic}
        - Questions should be progressive in difficulty within the {difficulty} level
        - Avoid repetition of concepts from previous questions provided above
        
        SPECIAL INSTRUCTIONS FOR READING QUESTIONS:
        If the topic is "Reading", you MUST include a "passage" field in each question containing a short reading passage (150-250 words) appropriate for {difficulty} level students. The passage should be engaging and educational, and all questions should be based on this passage. Include questions about main ideas, specific details, inference, vocabulary in context, or author's purpose.
        
        SPECIAL INSTRUCTIONS FOR MIXED TOPIC:
        If the topic is "Mixed", create exactly 4 questions with different focuses:
        - Question 1: Grammar-focused (verb tenses, articles, conditionals, etc.)
        - Question 2: Vocabulary-focused (word meanings, synonyms, collocations, etc.)
        - Question 3: Reading comprehension (include a "passage" field with 150-250 words and base the question on this passage)
        - Question 4: Usage-focused (expressions, idioms, formal/informal language, etc.)
        This ensures balanced coverage of all English learning areas.
        
        CRITICAL VALIDATION RULE:
        The "correct_answer" field MUST contain the EXACT same text as one of the four options in the "options" array. 
        Do NOT paraphrase, abbreviate, or modify the correct answer text. 
        Copy the exact text from the chosen option into the correct_answer field.
        
        Format your response as valid JSON only, with this exact structure:
        {{
            "questions": [
                {{
                    "passage": "Include this field ONLY for Reading questions or Question 3 in Mixed topics - a 150-250 word passage",
                    "question": "Question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Clear explanation of why this is correct and why other options are wrong",
                    "topic": "{request.topic}",
                    "subtopic": "Specific subtopic (e.g., 'Present Perfect', 'Synonyms', 'Main Ideas', 'Idioms')",
                    "difficulty": "{difficulty}",
                    "question_type": "Type of question (e.g., 'Fill-in-blank', 'Multiple choice', 'Error correction')"
                }},
                {{
                    "passage": "Include this field ONLY for Reading questions or Question 3 in Mixed topics",
                    "question": "Second question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option B",
                    "explanation": "Clear explanation of why this is correct and why other options are wrong",
                    "topic": "{request.topic}",
                    "subtopic": "Different subtopic from question 1",
                    "difficulty": "{difficulty}",
                    "question_type": "Different question type from question 1"
                }},
                {{
                    "passage": "For Mixed topics: include passage here for the Reading question (Question 3). For Reading topic: same passage as questions 1 and 2",
                    "question": "Third question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option C",
                    "explanation": "Clear explanation of why this is correct and why other options are wrong",
                    "topic": "{request.topic}",
                    "subtopic": "Different subtopic from questions 1 and 2",
                    "difficulty": "{difficulty}",
                    "question_type": "Different question type from questions 1 and 2"
                }},
                {{
                    "passage": "Include this field ONLY for Reading questions. For Mixed topics, Question 4 should NOT have a passage",
                    "question": "Fourth question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option D",
                    "explanation": "Clear explanation of why this is correct and why other options are wrong",
                    "topic": "{request.topic}",
                    "subtopic": "Different subtopic from questions 1, 2, and 3",
                    "difficulty": "{difficulty}",
                    "question_type": "Different question type from questions 1, 2, and 3"
                }}
            ]
        }}
        
        CRITICAL: You MUST generate exactly 4 questions. Each question must be unique and cover different aspects of {request.topic}.
        
        For Mixed topics: Question 1 = Grammar, Question 2 = Vocabulary, Question 3 = Reading (with passage), Question 4 = Usage.
        For Reading topics: All 4 questions based on the same reading passage.
        For other topics: Ensure maximum variety while staying within the {request.topic} topic and {difficulty} difficulty level.
        
        FINAL REMINDER: Double-check that each "correct_answer" is EXACTLY the same text as one of the four options in the "options" array.
        """
        
        # Use centralized Ollama configuration
        ollama_config = config.get_ollama_config()
        api_url = f"{ollama_config['base_url']}/api/generate"
        
        payload = {
            "model": ollama_config['model'],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,  # Increased for more variety
                "num_predict": ollama_config['options']['max_tokens'],
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        response = requests.post(api_url, json=payload, timeout=ollama_config['timeout'])
        response.raise_for_status()
        data = response.json()
        
        generated_text = data.get("response", "")
        
        # Parse JSON response
        try:
            # Extract JSON from response
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in response")
            
            json_str = generated_text[start_idx:end_idx]
            quiz_data = json.loads(json_str)
            
            # Validate that we have exactly 4 questions with proper structure
            questions = quiz_data.get("questions", [])
            valid_questions = 0
            
            for i, question in enumerate(questions):
                # Check if question has all required fields and 4 options
                required_fields = ['question', 'options', 'correct_answer', 'explanation', 'topic', 'difficulty']
                if (all(field in question for field in required_fields) and 
                    isinstance(question.get('options'), list) and 
                    len(question.get('options', [])) == 4):
                    
                    # Additional validation: correct_answer must be exactly one of the options
                    correct_answer = question.get('correct_answer', '')
                    options = question.get('options', [])
                    
                    if correct_answer in options:
                        valid_questions += 1
                    else:
                        print(f"DEBUG: Question {i+1} correct_answer '{correct_answer}' not found in options: {options}")
            
            if len(questions) != 4 or valid_questions != 4:
                # If not exactly 4 valid questions, create fallback quiz
                print(f"DEBUG: AI generated {len(questions)} questions, {valid_questions} valid. Using fallback.")
                quiz_data = create_adaptive_fallback_quiz(request.topic, difficulty, request.previous_questions, weak_topics)
            
            # Add comprehensive metadata
            quiz_data["user_level"] = current_level
            quiz_data["generated_for_level"] = difficulty
            quiz_data["weak_topics"] = weak_topics
            quiz_data["user_id"] = user_id
            quiz_data["model_used"] = ollama_config['model']
            quiz_data["topic_requested"] = request.topic
            quiz_data["questions_count"] = len(quiz_data.get("questions", []))
            quiz_data["previous_questions_considered"] = len(request.previous_questions) if request.previous_questions else 0
            quiz_data["recent_topics"] = recent_topics[-5:] if recent_topics else []
            quiz_data["avoided_subtopics"] = list(set(recent_subtopics[-8:])) if recent_subtopics else []
            
            # Extract subtopics covered for future reference
            subtopics_covered = []
            for question in quiz_data.get("questions", []):
                if "subtopic" in question:
                    subtopics_covered.append(question["subtopic"])
            quiz_data["subtopics_covered"] = subtopics_covered
            
            return quiz_data
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: create an adaptive quiz if JSON parsing fails
            return create_adaptive_fallback_quiz(request.topic, difficulty, request.previous_questions, weak_topics)
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {str(e)}")

@router.get("/model-info/")
async def get_model_info():
    """Get information about the current Ollama model and configuration."""
    ollama_config = config.get_ollama_config()
    return {
        "current_model": ollama_config['model'],
        "base_url": ollama_config['base_url'],
        "timeout": ollama_config['timeout'],
        "temperature": ollama_config['options']['temperature'],
        "num_predict": ollama_config['options']['max_tokens'],
        "available_models": config.get_available_models()
    }

def create_fallback_quiz(topic: str, difficulty: str, num_questions: int) -> Dict:
    """Create a fallback quiz when AI generation fails."""
    return create_adaptive_fallback_quiz(topic, difficulty, [], [])

def create_adaptive_fallback_quiz(topic: str, difficulty: str, previous_questions: List[str] = None, weak_topics: List[str] = None) -> Dict:
    """Create an adaptive fallback quiz when AI generation fails, considering previous questions and weak topics."""
    
    if previous_questions is None:
        previous_questions = []
    if weak_topics is None:
        weak_topics = []
    
    fallback_questions = {
        "Grammar": {
            "beginner": [
                {
                    "question": "Which sentence is correct?",
                    "options": ["I am student", "I am a student", "I am the student", "I student"],
                    "correct_answer": "I am a student",
                    "explanation": "We use 'a' before singular countable nouns when introducing them for the first time.",
                    "topic": "Grammar",
                    "subtopic": "Articles",
                    "difficulty": "beginner",
                    "question_type": "Multiple choice"
                },
                {
                    "question": "What is the past tense of 'go'?",
                    "options": ["goed", "went", "gone", "goes"],
                    "correct_answer": "went",
                    "explanation": "'Went' is the past tense of the irregular verb 'go'. 'Gone' is the past participle.",
                    "topic": "Grammar",
                    "subtopic": "Irregular Verbs",
                    "difficulty": "beginner",
                    "question_type": "Verb forms"
                },
                {
                    "question": "Choose the correct form: 'She _____ to work every day.'",
                    "options": ["go", "goes", "going", "gone"],
                    "correct_answer": "goes",
                    "explanation": "With third person singular (he/she/it), we add 's' to the verb in present simple.",
                    "topic": "Grammar",
                    "subtopic": "Present Simple",
                    "difficulty": "beginner",
                    "question_type": "Fill-in-blank"
                },
                {
                    "question": "Which is the correct plural form of 'child'?",
                    "options": ["childs", "children", "childes", "child"],
                    "correct_answer": "children",
                    "explanation": "'Children' is the irregular plural form of 'child'.",
                    "topic": "Grammar",
                    "subtopic": "Plural Forms",
                    "difficulty": "beginner",
                    "question_type": "Word forms"
                }
            ],
            "intermediate": [
                {
                    "question": "If I _____ you, I would study harder.",
                    "options": ["am", "was", "were", "be"],
                    "correct_answer": "were",
                    "explanation": "In second conditional sentences, we use 'were' for all persons after 'if'.",
                    "topic": "Grammar",
                    "subtopic": "Conditionals",
                    "difficulty": "intermediate",
                    "question_type": "Conditional sentences"
                },
                {
                    "question": "The report _____ by tomorrow morning.",
                    "options": ["must finish", "must be finished", "must have finished", "must finishing"],
                    "correct_answer": "must be finished",
                    "explanation": "We use passive voice (must be + past participle) when the action is done to the subject.",
                    "topic": "Grammar",
                    "subtopic": "Passive Voice",
                    "difficulty": "intermediate",
                    "question_type": "Passive construction"
                },
                {
                    "question": "I wish I _____ more time to finish the project.",
                    "options": ["have", "had", "will have", "would have"],
                    "correct_answer": "had",
                    "explanation": "After 'wish' for present situations, we use past tense to express regret about the present.",
                    "topic": "Grammar",
                    "subtopic": "Wish Sentences",
                    "difficulty": "intermediate",
                    "question_type": "Subjunctive mood"
                },
                {
                    "question": "She's been working here _____ five years.",
                    "options": ["since", "for", "during", "from"],
                    "correct_answer": "for",
                    "explanation": "We use 'for' with periods of time (five years), and 'since' with specific points in time.",
                    "topic": "Grammar",
                    "subtopic": "Prepositions of Time",
                    "difficulty": "intermediate",
                    "question_type": "Preposition usage"
                }
            ],
            "advanced": [
                {
                    "question": "Had she studied harder, she _____ the exam.",
                    "options": ["would pass", "would have passed", "will pass", "had passed"],
                    "correct_answer": "would have passed",
                    "explanation": "This is a third conditional with inversion. 'Had she studied' = 'If she had studied', so we need 'would have passed'.",
                    "topic": "Grammar",
                    "subtopic": "Advanced Conditionals",
                    "difficulty": "advanced",
                    "question_type": "Conditional inversion"
                },
                {
                    "question": "The committee insisted that he _____ present at the meeting.",
                    "options": ["is", "was", "be", "will be"],
                    "correct_answer": "be",
                    "explanation": "After verbs like 'insist', 'suggest', 'recommend', we use the subjunctive mood (base form of verb).",
                    "topic": "Grammar",
                    "subtopic": "Subjunctive Mood",
                    "difficulty": "advanced",
                    "question_type": "Subjunctive usage"
                },
                {
                    "question": "_____ the weather, we decided to proceed with the outdoor event.",
                    "options": ["Despite", "Although", "Even though", "In spite"],
                    "correct_answer": "Despite",
                    "explanation": "'Despite' is followed by a noun phrase. 'Although' and 'even though' are followed by clauses. 'In spite' needs 'of'.",
                    "topic": "Grammar",
                    "subtopic": "Concessive Connectors",
                    "difficulty": "advanced",
                    "question_type": "Connector usage"
                },
                {
                    "question": "No sooner _____ the announcement than chaos erupted.",
                    "options": ["had they made", "they had made", "did they make", "they made"],
                    "correct_answer": "had they made",
                    "explanation": "After 'no sooner' we use inversion with past perfect: 'No sooner had + subject + past participle'.",
                    "topic": "Grammar",
                    "subtopic": "Inversion",
                    "difficulty": "advanced",
                    "question_type": "Advanced inversion"
                }
            ]
        },
        "Vocabulary": {
            "beginner": [
                {
                    "question": "What does 'happy' mean?",
                    "options": ["sad", "angry", "joyful", "tired"],
                    "correct_answer": "joyful",
                    "explanation": "'Happy' means feeling pleasure or contentment, which is the same as 'joyful'.",
                    "topic": "Vocabulary",
                    "subtopic": "Basic Emotions",
                    "difficulty": "beginner",
                    "question_type": "Synonyms"
                },
                {
                    "question": "Choose the opposite of 'big':",
                    "options": ["large", "huge", "small", "tall"],
                    "correct_answer": "small",
                    "explanation": "'Small' is the opposite of 'big'. 'Large' and 'huge' are synonyms of 'big'.",
                    "topic": "Vocabulary",
                    "subtopic": "Size Adjectives",
                    "difficulty": "beginner",
                    "question_type": "Antonyms"
                },
                {
                    "question": "What do you use to write?",
                    "options": ["fork", "pen", "cup", "shoe"],
                    "correct_answer": "pen",
                    "explanation": "A pen is a tool used for writing. The other options are not writing instruments.",
                    "topic": "Vocabulary",
                    "subtopic": "Common Objects",
                    "difficulty": "beginner",
                    "question_type": "Word meanings"
                },
                {
                    "question": "Which word means 'very cold'?",
                    "options": ["warm", "hot", "freezing", "cool"],
                    "correct_answer": "freezing",
                    "explanation": "'Freezing' means extremely cold, below the temperature at which water turns to ice.",
                    "topic": "Vocabulary",
                    "subtopic": "Temperature",
                    "difficulty": "beginner",
                    "question_type": "Intensity adjectives"
                }
            ],
            "intermediate": [
                {
                    "question": "What does 'procrastinate' mean?",
                    "options": ["to hurry up", "to delay doing something", "to finish quickly", "to work hard"],
                    "correct_answer": "to delay doing something",
                    "explanation": "'Procrastinate' means to postpone or delay doing something, especially out of laziness or habit.",
                    "topic": "Vocabulary",
                    "subtopic": "Academic Vocabulary",
                    "difficulty": "intermediate",
                    "question_type": "Word definitions"
                },
                {
                    "question": "Choose the best synonym for 'meticulous':",
                    "options": ["careless", "detailed", "quick", "lazy"],
                    "correct_answer": "detailed",
                    "explanation": "'Meticulous' means showing great attention to detail, being very careful and precise.",
                    "topic": "Vocabulary",
                    "subtopic": "Descriptive Adjectives",
                    "difficulty": "intermediate",
                    "question_type": "Synonyms"
                },
                {
                    "question": "The company decided to _____ their outdated policies.",
                    "options": ["revise", "revive", "reverse", "reveal"],
                    "correct_answer": "revise",
                    "explanation": "'Revise' means to examine and make corrections or improvements to something.",
                    "topic": "Vocabulary",
                    "subtopic": "Business Vocabulary",
                    "difficulty": "intermediate",
                    "question_type": "Context usage"
                },
                {
                    "question": "What does the phrasal verb 'put off' mean?",
                    "options": ["to wear", "to postpone", "to turn on", "to remove"],
                    "correct_answer": "to postpone",
                    "explanation": "'Put off' is a phrasal verb meaning to delay or postpone something until later.",
                    "topic": "Vocabulary",
                    "subtopic": "Phrasal Verbs",
                    "difficulty": "intermediate",
                    "question_type": "Phrasal verb meanings"
                }
            ],
            "advanced": [
                {
                    "question": "The new policy has been _____ by the committee.",
                    "options": ["ratified", "justified", "clarified", "nullified"],
                    "correct_answer": "ratified",
                    "explanation": "'Ratified' means officially approved or confirmed, which fits the context of policy approval.",
                    "topic": "Vocabulary",
                    "subtopic": "Formal Vocabulary",
                    "difficulty": "advanced",
                    "question_type": "Context-dependent usage"
                },
                {
                    "question": "Her _____ for detail made her an excellent editor.",
                    "options": ["penchant", "pendant", "repentant", "attendant"],
                    "correct_answer": "penchant",
                    "explanation": "'Penchant' means a strong inclination or liking for something. The other words are unrelated.",
                    "topic": "Vocabulary",
                    "subtopic": "Advanced Nouns",
                    "difficulty": "advanced",
                    "question_type": "Word choice"
                },
                {
                    "question": "The CEO's decision was considered _____ by many shareholders.",
                    "options": ["prudent", "imprudent", "student", "incident"],
                    "correct_answer": "imprudent",
                    "explanation": "'Imprudent' means lacking wisdom or good judgment. The context suggests criticism from shareholders.",
                    "topic": "Vocabulary",
                    "subtopic": "Evaluative Adjectives",
                    "difficulty": "advanced",
                    "question_type": "Connotation"
                },
                {
                    "question": "What does 'ubiquitous' mean?",
                    "options": ["rare", "present everywhere", "ancient", "mysterious"],
                    "correct_answer": "present everywhere",
                    "explanation": "'Ubiquitous' means existing or being everywhere at the same time; omnipresent.",
                    "topic": "Vocabulary",
                    "subtopic": "Academic Adjectives",
                    "difficulty": "advanced",
                    "question_type": "Advanced definitions"
                }
            ]
        },
        "Reading": {
            "beginner": [
                {
                    "passage": "Sam lives near a big park. Every day, he goes to the park and plays football with his friends. Sam also has a small dog named Max. Max is very friendly and loves to run around the park. After playing football, Sam and his friends sit under a tree and eat sandwiches. Max sits with them and waits for some food. Sam always gives Max a small piece of his sandwich because he loves his dog very much.",
                    "question": "What does Sam do every day?",
                    "options": ["He goes to school", "He plays football in the park", "He stays at home", "He walks his dog"],
                    "correct_answer": "He plays football in the park",
                    "explanation": "According to the passage, 'Every day, he goes to the park and plays football with his friends.'",
                    "topic": "Reading",
                    "subtopic": "Main Ideas",
                    "difficulty": "beginner",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "Sam lives near a big park. Every day, he goes to the park and plays football with his friends. Sam also has a small dog named Max. Max is very friendly and loves to run around the park. After playing football, Sam and his friends sit under a tree and eat sandwiches. Max sits with them and waits for some food. Sam always gives Max a small piece of his sandwich because he loves his dog very much.",
                    "question": "What kind of animal is Max?",
                    "options": ["A cat", "A bird", "A dog", "A rabbit"],
                    "correct_answer": "A dog",
                    "explanation": "The passage clearly states 'Sam also has a small dog named Max.'",
                    "topic": "Reading",
                    "subtopic": "Specific Details",
                    "difficulty": "beginner",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "Sam lives near a big park. Every day, he goes to the park and plays football with his friends. Sam also has a small dog named Max. Max is very friendly and loves to run around the park. After playing football, Sam and his friends sit under a tree and eat sandwiches. Max sits with them and waits for some food. Sam always gives Max a small piece of his sandwich because he loves his dog very much.",
                    "question": "Why does Sam give Max food?",
                    "options": ["Because Max is hungry", "Because he loves his dog", "Because Max asks for it", "Because his friends tell him to"],
                    "correct_answer": "Because he loves his dog",
                    "explanation": "The passage ends with 'Sam always gives Max a small piece of his sandwich because he loves his dog very much.'",
                    "topic": "Reading",
                    "subtopic": "Inference",
                    "difficulty": "beginner",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "Sam lives near a big park. Every day, he goes to the park and plays football with his friends. Sam also has a small dog named Max. Max is very friendly and loves to run around the park. After playing football, Sam and his friends sit under a tree and eat sandwiches. Max sits with them and waits for some food. Sam always gives Max a small piece of his sandwich because he loves his dog very much.",
                    "question": "Where do Sam and his friends eat their sandwiches?",
                    "options": ["At home", "In the school", "Under a tree", "In a restaurant"],
                    "correct_answer": "Under a tree",
                    "explanation": "The passage states 'Sam and his friends sit under a tree and eat sandwiches.'",
                    "topic": "Reading",
                    "subtopic": "Specific Details",
                    "difficulty": "beginner",
                    "question_type": "Reading comprehension"
                }
            ],
            "intermediate": [
                {
                    "passage": "Working from home has become increasingly popular in recent years, especially after the global pandemic. Many employees have discovered that they can be just as productive, if not more so, when working from their own homes. This shift has brought both advantages and challenges. On the positive side, workers save time and money on commuting, have more flexibility in their schedules, and often report better work-life balance. However, some people struggle with distractions at home, miss the social interaction with colleagues, and find it difficult to separate work from personal life when both happen in the same space.",
                    "question": "What is the main topic of this passage?",
                    "options": ["The pandemic's effects", "Working from home", "Commuting problems", "Social interaction"],
                    "correct_answer": "Working from home",
                    "explanation": "The passage focuses on working from home, discussing its popularity, advantages, and challenges.",
                    "topic": "Reading",
                    "subtopic": "Main Ideas",
                    "difficulty": "intermediate",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "Working from home has become increasingly popular in recent years, especially after the global pandemic. Many employees have discovered that they can be just as productive, if not more so, when working from their own homes. This shift has brought both advantages and challenges. On the positive side, workers save time and money on commuting, have more flexibility in their schedules, and often report better work-life balance. However, some people struggle with distractions at home, miss the social interaction with colleagues, and find it difficult to separate work from personal life when both happen in the same space.",
                    "question": "According to the passage, what do workers save when working from home?",
                    "options": ["Energy and effort", "Time and money", "Space and resources", "Health and wellness"],
                    "correct_answer": "Time and money",
                    "explanation": "The passage specifically mentions 'workers save time and money on commuting.'",
                    "topic": "Reading",
                    "subtopic": "Specific Details",
                    "difficulty": "intermediate",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "Working from home has become increasingly popular in recent years, especially after the global pandemic. Many employees have discovered that they can be just as productive, if not more so, when working from their own homes. This shift has brought both advantages and challenges. On the positive side, workers save time and money on commuting, have more flexibility in their schedules, and often report better work-life balance. However, some people struggle with distractions at home, miss the social interaction with colleagues, and find it difficult to separate work from personal life when both happen in the same space.",
                    "question": "What can be inferred about productivity when working from home?",
                    "options": ["It always decreases", "It can be equal or better", "It depends on the job", "It's impossible to measure"],
                    "correct_answer": "It can be equal or better",
                    "explanation": "The passage states that employees 'can be just as productive, if not more so' when working from home.",
                    "topic": "Reading",
                    "subtopic": "Inference",
                    "difficulty": "intermediate",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "Working from home has become increasingly popular in recent years, especially after the global pandemic. Many employees have discovered that they can be just as productive, if not more so, when working from their own homes. This shift has brought both advantages and challenges. On the positive side, workers save time and money on commuting, have more flexibility in their schedules, and often report better work-life balance. However, some people struggle with distractions at home, miss the social interaction with colleagues, and find it difficult to separate work from personal life when both happen in the same space.",
                    "question": "What challenge is mentioned regarding working from home?",
                    "options": ["Higher costs", "Less productivity", "Difficulty separating work and personal life", "More commuting time"],
                    "correct_answer": "Difficulty separating work and personal life",
                    "explanation": "The passage mentions people 'find it difficult to separate work from personal life when both happen in the same space.'",
                    "topic": "Reading",
                    "subtopic": "Specific Details",
                    "difficulty": "intermediate",
                    "question_type": "Reading comprehension"
                }
            ],
            "advanced": [
                {
                    "passage": "The concept of artificial intelligence has evolved dramatically since its inception in the 1950s. Initially conceived as a means to replicate human cognitive processes, AI has transcended its original boundaries to encompass machine learning, neural networks, and deep learning algorithms. Contemporary AI systems demonstrate remarkable capabilities in pattern recognition, natural language processing, and decision-making processes that were once considered exclusively human domains. However, this rapid advancement has precipitated significant ethical debates regarding privacy, employment displacement, and the potential for autonomous systems to make consequential decisions without human oversight. As we stand at the precipice of an AI-driven future, society must grapple with balancing technological innovation with responsible implementation and regulation.",
                    "question": "What is the author's primary purpose in this passage?",
                    "options": ["To advocate for AI development", "To trace AI's evolution and current challenges", "To criticize artificial intelligence", "To predict future AI capabilities"],
                    "correct_answer": "To trace AI's evolution and current challenges",
                    "explanation": "The passage discusses AI's development from the 1950s to present and addresses current ethical debates and challenges.",
                    "topic": "Reading",
                    "subtopic": "Author's Purpose",
                    "difficulty": "advanced",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "The concept of artificial intelligence has evolved dramatically since its inception in the 1950s. Initially conceived as a means to replicate human cognitive processes, AI has transcended its original boundaries to encompass machine learning, neural networks, and deep learning algorithms. Contemporary AI systems demonstrate remarkable capabilities in pattern recognition, natural language processing, and decision-making processes that were once considered exclusively human domains. However, this rapid advancement has precipitated significant ethical debates regarding privacy, employment displacement, and the potential for autonomous systems to make consequential decisions without human oversight. As we stand at the precipice of an AI-driven future, society must grapple with balancing technological innovation with responsible implementation and regulation.",
                    "question": "What does 'precipitated' most likely mean in this context?",
                    "options": ["Prevented", "Caused or brought about", "Delayed", "Ignored"],
                    "correct_answer": "Caused or brought about",
                    "explanation": "'Precipitated' in this context means caused or triggered, referring to how AI advancement has brought about ethical debates.",
                    "topic": "Reading",
                    "subtopic": "Vocabulary in Context",
                    "difficulty": "advanced",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "The concept of artificial intelligence has evolved dramatically since its inception in the 1950s. Initially conceived as a means to replicate human cognitive processes, AI has transcended its original boundaries to encompass machine learning, neural networks, and deep learning algorithms. Contemporary AI systems demonstrate remarkable capabilities in pattern recognition, natural language processing, and decision-making processes that were once considered exclusively human domains. However, this rapid advancement has precipitated significant ethical debates regarding privacy, employment displacement, and the potential for autonomous systems to make consequential decisions without human oversight. As we stand at the precipice of an AI-driven future, society must grapple with balancing technological innovation with responsible implementation and regulation.",
                    "question": "Which of the following can be inferred about the author's perspective on AI development?",
                    "options": ["Completely optimistic", "Entirely pessimistic", "Cautiously balanced", "Completely neutral"],
                    "correct_answer": "Cautiously balanced",
                    "explanation": "The author acknowledges AI's remarkable capabilities while also emphasizing the need for responsible implementation and addressing ethical concerns.",
                    "topic": "Reading",
                    "subtopic": "Inference",
                    "difficulty": "advanced",
                    "question_type": "Reading comprehension"
                },
                {
                    "passage": "The concept of artificial intelligence has evolved dramatically since its inception in the 1950s. Initially conceived as a means to replicate human cognitive processes, AI has transcended its original boundaries to encompass machine learning, neural networks, and deep learning algorithms. Contemporary AI systems demonstrate remarkable capabilities in pattern recognition, natural language processing, and decision-making processes that were once considered exclusively human domains. However, this rapid advancement has precipitated significant ethical debates regarding privacy, employment displacement, and the potential for autonomous systems to make consequential decisions without human oversight. As we stand at the precipice of an AI-driven future, society must grapple with balancing technological innovation with responsible implementation and regulation.",
                    "question": "What metaphor does the author use to describe our current position regarding AI?",
                    "options": ["Standing at a crossroads", "Standing at the precipice", "Climbing a mountain", "Swimming in deep waters"],
                    "correct_answer": "Standing at the precipice",
                    "explanation": "The author uses the metaphor 'at the precipice of an AI-driven future' to describe our current position.",
                    "topic": "Reading",
                    "subtopic": "Literary Devices",
                    "difficulty": "advanced",
                    "question_type": "Reading comprehension"
                }
            ]
        },
        "Mixed": {
            "beginner": [
                {
                    "question": "Which sentence is correct?",
                    "options": ["I am student", "I am a student", "I am the student", "I student"],
                    "correct_answer": "I am a student",
                    "explanation": "We use 'a' before singular countable nouns when introducing them for the first time.",
                    "topic": "Mixed",
                    "subtopic": "Articles",
                    "difficulty": "beginner",
                    "question_type": "Grammar"
                },
                {
                    "question": "What does 'happy' mean?",
                    "options": ["sad", "angry", "joyful", "tired"],
                    "correct_answer": "joyful",
                    "explanation": "'Happy' means feeling pleasure or contentment, which is the same as 'joyful'.",
                    "topic": "Mixed",
                    "subtopic": "Basic Emotions",
                    "difficulty": "beginner",
                    "question_type": "Vocabulary"
                },
                {
                    "question": "What is the past tense of 'go'?",
                    "options": ["goed", "went", "gone", "goes"],
                    "correct_answer": "went",
                    "explanation": "'Went' is the past tense of the irregular verb 'go'. 'Gone' is the past participle.",
                    "topic": "Mixed",
                    "subtopic": "Irregular Verbs",
                    "difficulty": "beginner",
                    "question_type": "Grammar"
                },
                {
                    "question": "Choose the opposite of 'big':",
                    "options": ["large", "huge", "small", "tall"],
                    "correct_answer": "small",
                    "explanation": "'Small' is the opposite of 'big'. 'Large' and 'huge' are synonyms of 'big'.",
                    "topic": "Mixed",
                    "subtopic": "Size Adjectives",
                    "difficulty": "beginner",
                    "question_type": "Vocabulary"
                }
            ],
            "intermediate": [
                {
                    "question": "If I _____ you, I would study harder.",
                    "options": ["am", "was", "were", "be"],
                    "correct_answer": "were",
                    "explanation": "In second conditional sentences, we use 'were' for all persons after 'if'.",
                    "topic": "Mixed",
                    "subtopic": "Conditionals",
                    "difficulty": "intermediate",
                    "question_type": "Grammar"
                },
                {
                    "question": "What does 'procrastinate' mean?",
                    "options": ["to hurry up", "to delay doing something", "to finish quickly", "to work hard"],
                    "correct_answer": "to delay doing something",
                    "explanation": "'Procrastinate' means to postpone or delay doing something, especially out of laziness or habit.",
                    "topic": "Mixed",
                    "subtopic": "Academic Vocabulary",
                    "difficulty": "intermediate",
                    "question_type": "Vocabulary"
                },
                {
                    "question": "The report _____ by tomorrow morning.",
                    "options": ["must finish", "must be finished", "must have finished", "must finishing"],
                    "correct_answer": "must be finished",
                    "explanation": "We use passive voice (must be + past participle) when the action is done to the subject.",
                    "topic": "Mixed",
                    "subtopic": "Passive Voice",
                    "difficulty": "intermediate",
                    "question_type": "Grammar"
                },
                {
                    "question": "What does the phrasal verb 'put off' mean?",
                    "options": ["to wear", "to postpone", "to turn on", "to remove"],
                    "correct_answer": "to postpone",
                    "explanation": "'Put off' is a phrasal verb meaning to delay or postpone something until later.",
                    "topic": "Mixed",
                    "subtopic": "Phrasal Verbs",
                    "difficulty": "intermediate",
                    "question_type": "Vocabulary"
                }
            ],
            "advanced": [
                {
                    "question": "Had she studied harder, she _____ the exam.",
                    "options": ["would pass", "would have passed", "will pass", "had passed"],
                    "correct_answer": "would have passed",
                    "explanation": "This is a third conditional with inversion. 'Had she studied' = 'If she had studied', so we need 'would have passed'.",
                    "topic": "Mixed",
                    "subtopic": "Advanced Conditionals",
                    "difficulty": "advanced",
                    "question_type": "Grammar"
                },
                {
                    "question": "The new policy has been _____ by the committee.",
                    "options": ["ratified", "justified", "clarified", "nullified"],
                    "correct_answer": "ratified",
                    "explanation": "'Ratified' means officially approved or confirmed, which fits the context of policy approval.",
                    "topic": "Mixed",
                    "subtopic": "Formal Vocabulary",
                    "difficulty": "advanced",
                    "question_type": "Vocabulary"
                },
                {
                    "question": "The committee insisted that he _____ present at the meeting.",
                    "options": ["is", "was", "be", "will be"],
                    "correct_answer": "be",
                    "explanation": "After verbs like 'insist', 'suggest', 'recommend', we use the subjunctive mood (base form of verb).",
                    "topic": "Mixed",
                    "subtopic": "Subjunctive Mood",
                    "difficulty": "advanced",
                    "question_type": "Grammar"
                },
                {
                    "question": "Her _____ for detail made her an excellent editor.",
                    "options": ["penchant", "pendant", "repentant", "attendant"],
                    "correct_answer": "penchant",
                    "explanation": "'Penchant' means a strong inclination or liking for something. The other words are unrelated.",
                    "topic": "Mixed",
                    "subtopic": "Academic Adjectives",
                    "difficulty": "advanced",
                    "question_type": "Vocabulary"
                }
            ]
        }
    }
    
    # Get questions for the specific topic and difficulty
    topic_questions = fallback_questions.get(topic, fallback_questions["Grammar"])
    questions_pool = topic_questions.get(difficulty, topic_questions["beginner"])
    
    # Filter out questions similar to previous ones if provided
    filtered_questions = []
    if previous_questions:
        for question in questions_pool:
            question_text = question["question"].lower()
            is_similar = False
            for prev_q in previous_questions:
                prev_q_lower = prev_q.lower()
                # Check for similar keywords or concepts
                if (any(word in question_text for word in prev_q_lower.split() if len(word) > 3) or
                    question["subtopic"].lower() in prev_q_lower):
                    is_similar = True
                    break
            if not is_similar:
                filtered_questions.append(question)
    else:
        filtered_questions = questions_pool
    
    # If we filtered out too many, add some back
    if len(filtered_questions) < 4:
        filtered_questions = questions_pool
    
    # Select exactly 4 questions, prioritizing weak topics if available
    selected_questions = []
    weak_topic_questions = []
    other_questions = []
    
    for question in filtered_questions:
        if weak_topics and any(weak_topic.lower() in question["subtopic"].lower() for weak_topic in weak_topics):
            weak_topic_questions.append(question)
        else:
            other_questions.append(question)
    
    # Try to include questions from weak topics first
    selected_questions.extend(weak_topic_questions[:2])  # Max 2 from weak topics
    remaining_needed = 4 - len(selected_questions)
    selected_questions.extend(other_questions[:remaining_needed])
    
    # If still not enough, add more from any available
    if len(selected_questions) < 4:
        all_available = weak_topic_questions + other_questions
        for question in all_available:
            if question not in selected_questions and len(selected_questions) < 4:
                selected_questions.append(question)
    
    # Ensure we have exactly 4 questions
    while len(selected_questions) < 4:
        selected_questions.append(questions_pool[len(selected_questions) % len(questions_pool)])
    
    selected_questions = selected_questions[:4]  # Limit to exactly 4
    
    return {
        "questions": selected_questions,
        "generated_for_level": difficulty,
        "fallback": True,
        "topic_requested": topic,
        "questions_count": len(selected_questions),
        "subtopics_covered": [q["subtopic"] for q in selected_questions],
        "previous_questions_considered": len(previous_questions) if previous_questions else 0,
        "weak_topics_targeted": len(weak_topic_questions)
    }

@router.get("/user-profile/{user_id}")
async def get_user_english_profile(user_id: str):
    """Get user's English learning profile including level and progress."""
    try:
        profile = get_user_profile(user_id)
        return {
            "user_id": user_id,
            "english_level": profile.get("english_level", "beginner"),
            "progress": profile.get("progress", {}),
            "total_quizzes": profile.get("total_quizzes", 0),
            "average_score": profile.get("average_score", 0.0),
            "last_quiz_date": profile.get("last_quiz_date"),
            "level_changed": profile.get("level_changed", False),
            "previous_level": profile.get("previous_level")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user profile: {str(e)}")

@router.post("/update-user-level/")
async def manually_update_user_level(user_id: str, new_level: str):
    """Manually update user's English level (for admin use)."""
    if new_level not in ["beginner", "intermediate", "advanced"]:
        raise HTTPException(status_code=400, detail="Invalid level. Must be 'beginner', 'intermediate', or 'advanced'")
    
    try:
        update_english_level(user_id, new_level)
        return {"message": f"User {user_id} level updated to {new_level}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user level: {str(e)}")

@router.get("/quiz-topics/")
async def get_quiz_topics():
    """Get available English learning topics for quiz generation."""
    topics = [
        {
            "name": "Grammar",
            "subtopics": ["Verb Tenses", "Articles", "Prepositions", "Conditionals", "Passive Voice"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Vocabulary", 
            "subtopics": ["Synonyms", "Antonyms", "Idioms", "Phrasal Verbs", "Word Formation"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Reading",
            "subtopics": ["Main Ideas", "Details", "Inference", "Vocabulary in Context"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Usage",
            "subtopics": ["Common Expressions", "Collocations", "Formal vs Informal"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Mixed",
            "subtopics": ["All topics combined"],
            "levels": ["beginner", "intermediate", "advanced"]
        }
    ]
    
    return {"topics": topics}

@router.post("/change-model/")
async def change_model(new_model: str):
    """Change the Ollama model at runtime (for admin use)."""
    if not config.validate_model(new_model):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid model. Available models: {config.get_available_models()}"
        )
    
    try:
        # Test the new model with a simple prompt
        test_prompt = "Hello, can you respond with 'Model working correctly'?"
        
        api_url = f"{config.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": new_model,
            "prompt": test_prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 20}
        }
        
        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()
        
        # If successful, update the config (this would be temporary until app restart)
        # In a production environment, you'd want to update the .env file
        config.OLLAMA_MODEL = new_model
        
        return {
            "message": f"Model changed to {new_model}",
            "new_model": new_model,
            "note": "This change is temporary until application restart"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to test new model: {str(e)}"
        )

@router.get("/health-check/")
async def health_check():
    """Check if Ollama is running and the current model is available."""
    try:
        ollama_config = config.get_ollama_config()
        api_url = f"{ollama_config['base_url']}/api/generate"
        
        payload = {
            "model": ollama_config['model'],
            "prompt": "Test",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 5}
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "healthy",
            "model": ollama_config['model'],
            "base_url": ollama_config['base_url'],
            "message": "Ollama is running and model is available"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Ollama health check failed: {str(e)}"
        )
