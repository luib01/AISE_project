from fastapi import FastAPI
from app.cors import add_cors_middleware
from app.routes.evaluations import router as evaluations_router
from app.routes.questions import router as questions_router
from app.routes.chat import router as chat_router
from app.routes.performance import router as performance_router
from app.routes.quiz_generator import router as quiz_generator_router
from app.routes.auth import router as auth_router

app = FastAPI(title="English Learning Platform", description="AI-powered English learning platform")
add_cors_middleware(app)

@app.get("/")
async def root():
    return {"message": "Hello, English Learning Platform is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}

app.include_router(evaluations_router, prefix="/api", tags=["evaluations"])
app.include_router(questions_router, prefix="/api", tags=["questions"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(performance_router, prefix="/api", tags=["performance"])
app.include_router(quiz_generator_router, prefix="/api", tags=["quiz_generator"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])

