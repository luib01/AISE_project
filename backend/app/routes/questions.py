# backend/app/routes/questions.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.question_model import answer_question, save_question_answer

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str
    context: str

@router.post("/ask-question/")
async def ask_question(request: QuestionRequest):
    try:
        # Validate request
        if not request.question or request.question.strip() == "":
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if not request.context or request.context.strip() == "":
            raise HTTPException(status_code=400, detail="Context cannot be empty")
        
        ans = answer_question(request.question, request.context)
        
        # Enhance short answers for better user experience
        if len(ans) < 20:
            enhanced_ans = f"The answer is: {ans}. This is a brief response based on the provided context."
        else:
            enhanced_ans = ans
        
        save_question_answer(request.question, request.context, enhanced_ans)
        return {"question": request.question, "answer": enhanced_ans}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
