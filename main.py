from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from agents.interview_orchestrator import InterviewOrchestrator
from agents.question_generator import QuestionGenerator
from agents.answer_evaluator import AnswerEvaluator
from agents.feedback_generator import FeedbackGenerator
from models.session import InterviewSession, SessionState
from models.assessment import AssessmentResult

app = FastAPI(title="Excel Skills Interview API", version="1.0.0")

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
sessions: Dict[str, InterviewSession] = {}

class StartInterviewRequest(BaseModel):
    candidate_name: str
    position_level: str = "intermediate"  # beginner, intermediate, advanced

class InterviewResponse(BaseModel):
    session_id: str
    message: str
    question: Optional[str] = None
    question_format: Optional[str] = "open_ended"
    options: Optional[List[str]] = None
    is_complete: bool = False
    assessment_result: Optional[AssessmentResult] = None

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

@app.get("/")
async def root():
    return {"message": "Excel Skills Interview API", "status": "running"}

@app.post("/start-interview", response_model=InterviewResponse)
async def start_interview(request: StartInterviewRequest):
    """Initialize a new Excel skills interview"""
    
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize agents
        orchestrator = InterviewOrchestrator()
        question_generator = QuestionGenerator()
        answer_evaluator = AnswerEvaluator()
        feedback_generator = FeedbackGenerator()
        
        # Create session
        session = InterviewSession(
            session_id=session_id,
            candidate_name=request.candidate_name,
            position_level=request.position_level,
            orchestrator=orchestrator,
            question_generator=question_generator,
            answer_evaluator=answer_evaluator,
            feedback_generator=feedback_generator
        )
        
        sessions[session_id] = session
        
        # Start the interview
        welcome_message, first_question = await session.start_interview()
        
        return InterviewResponse(
            session_id=session_id,
            message=welcome_message,
            question=first_question,
            question_format="open_ended",
            is_complete=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")

@app.post("/submit-answer", response_model=InterviewResponse)
async def submit_answer(request: AnswerRequest):
    """Submit an answer and get the next question or final assessment"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[request.session_id]
    
    try:
        result = await session.process_answer(request.answer)
        
        if result["is_complete"]:
            # Generate final assessment
            assessment = await session.generate_final_assessment()
            return InterviewResponse(
                session_id=request.session_id,
                message=result["message"],
                is_complete=True,
                assessment_result=assessment
            )
        else:
            return InterviewResponse(
                session_id=request.session_id,
                message=result["message"],
                question=result["next_question"],
                question_format=result.get("question_format", "open_ended"),
                options=result.get("options"),
                is_complete=False
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")

@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session status and progress"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "candidate_name": session.candidate_name,
        "position_level": session.position_level,
        "current_question": session.current_question_index,
        "total_questions": len(session.questions_asked),
        "mcq_count": session.mcq_count,
        "target_mcq_count": session.target_mcq_count,
        "state": session.state.value,
        "skill_areas_covered": list(session.skill_scores.keys())
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
