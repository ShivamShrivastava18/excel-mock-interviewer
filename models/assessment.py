from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class SkillAssessment(BaseModel):
    skill_area: str
    score: float  # 0.0 to 1.0
    level: str  # "Beginner", "Intermediate", "Advanced", "Expert"
    strengths: List[str]
    areas_for_improvement: List[str]

class AssessmentResult(BaseModel):
    overall_score: float
    overall_level: str
    skill_assessments: List[SkillAssessment]
    key_strengths: List[str]
    improvement_recommendations: List[str]
    next_steps: List[str]
    interview_summary: str
    generated_at: datetime
