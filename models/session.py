from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

class SessionState(Enum):
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class QuestionType(Enum):
    FORMULA_BASIC = "formula_basic"
    FORMULA_ADVANCED = "formula_advanced"
    DATA_ANALYSIS = "data_analysis"
    PIVOT_TABLES = "pivot_tables"
    CHARTS_VISUALIZATION = "charts_visualization"
    DATA_VALIDATION = "data_validation"
    MACROS_VBA = "macros_vba"
    SCENARIO_BASED = "scenario_based"
    MCQ_BASIC = "mcq_basic"
    MCQ_ADVANCED = "mcq_advanced"

class QuestionFormat(Enum):
    OPEN_ENDED = "open_ended"
    MULTIPLE_CHOICE = "multiple_choice"

class InterviewSession:
    def __init__(self, session_id: str, candidate_name: str, position_level: str,
                 orchestrator, question_generator, answer_evaluator, feedback_generator):
        self.session_id = session_id
        self.candidate_name = candidate_name
        self.position_level = position_level
        self.state = SessionState.INITIALIZED
        self.created_at = datetime.now()
        
        # Agents
        self.orchestrator = orchestrator
        self.question_generator = question_generator
        self.answer_evaluator = answer_evaluator
        self.feedback_generator = feedback_generator
        
        # Interview data
        self.questions_asked: List[Dict[str, Any]] = []
        self.answers_given: List[Dict[str, Any]] = []
        self.skill_scores: Dict[str, float] = {}
        self.current_question_index = 0
        self.adaptive_difficulty = self._get_initial_difficulty()
        
        # Interview flow control
        self.max_questions = self._get_max_questions()
        self.skill_areas_to_cover = self._get_skill_areas()
        self.mcq_count = 0
        self.target_mcq_count = 5  # At least 5 MCQ questions
    
    def _get_initial_difficulty(self) -> float:
        """Set initial difficulty based on position level"""
        difficulty_map = {
            "beginner": 0.25,      # Clearly beginner level
            "intermediate": 0.55,   # Clearly intermediate level  
            "advanced": 0.8        # Clearly advanced level
        }
        return difficulty_map.get(self.position_level, 0.55)
    
    def _get_max_questions(self) -> int:
        """Determine number of questions based on position level"""
        question_map = {
            "beginner": 8,         # Include MCQs for beginners
            "intermediate": 10,    # Standard length with MCQs
            "advanced": 12         # More comprehensive with MCQs
        }
        return question_map.get(self.position_level, 10)
    
    def _get_skill_areas(self) -> List[QuestionType]:
        """Define skill areas to assess based on position level"""
        base_areas = [
            QuestionType.FORMULA_BASIC,
            QuestionType.DATA_ANALYSIS,
            QuestionType.CHARTS_VISUALIZATION,
            QuestionType.MCQ_BASIC  # Always include basic MCQs
        ]
        
        if self.position_level in ["intermediate", "advanced"]:
            base_areas.extend([
                QuestionType.FORMULA_ADVANCED,
                QuestionType.PIVOT_TABLES,
                QuestionType.DATA_VALIDATION,
                QuestionType.MCQ_ADVANCED
            ])
        
        if self.position_level == "advanced":
            base_areas.extend([
                QuestionType.MACROS_VBA,
                QuestionType.SCENARIO_BASED
            ])
        
        return base_areas
    
    async def start_interview(self):
        """Initialize the interview and generate first question"""
        self.state = SessionState.IN_PROGRESS
        
        welcome_message = await self.orchestrator.generate_welcome_message(
            self.candidate_name, self.position_level
        )
        
        # Start with an open-ended question
        first_question_data = await self.question_generator.generate_question(
            skill_area=self.skill_areas_to_cover[0],
            difficulty=self.adaptive_difficulty,
            context={"position_level": self.position_level},
            question_format=QuestionFormat.OPEN_ENDED
        )
        
        self.questions_asked.append({
            "question": first_question_data["question"],
            "skill_area": self.skill_areas_to_cover[0].value,
            "difficulty": self.adaptive_difficulty,
            "format": QuestionFormat.OPEN_ENDED.value,
            "options": first_question_data.get("options"),
            "correct_answer": first_question_data.get("correct_answer"),
            "timestamp": datetime.now().isoformat()
        })
        
        return welcome_message, first_question_data["question"]
    
    async def process_answer(self, answer: str) -> Dict[str, Any]:
        """Process candidate's answer and determine next step"""
        if self.current_question_index >= len(self.questions_asked):
            raise ValueError("No active question to answer")
        
        current_question = self.questions_asked[self.current_question_index]
        
        print(f"Processing answer for question {self.current_question_index + 1}")
        print(f"Answer: {answer}")
        print(f"Question format: {current_question.get('format', 'open_ended')}")
        print(f"Skill area: {current_question['skill_area']}")
        
        # Evaluate the answer
        evaluation = await self.answer_evaluator.evaluate_answer(
            question=current_question["question"],
            answer=answer,
            skill_area=current_question["skill_area"],
            expected_difficulty=current_question["difficulty"],
            question_format=current_question.get("format", "open_ended"),
            options=current_question.get("options"),
            correct_answer=current_question.get("correct_answer")
        )
        
        print(f"Evaluation score: {evaluation.get('overall_score', 'N/A')}")
        
        # Store the answer and evaluation
        self.answers_given.append({
            "answer": answer,
            "evaluation": evaluation,
            "question_index": self.current_question_index,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update skill scores - use actual evaluation score
        skill_area = current_question["skill_area"]
        new_score = evaluation.get("overall_score", 0.5)
        
        if skill_area not in self.skill_scores:
            self.skill_scores[skill_area] = new_score
        else:
            # Weighted average: give more weight to recent performance
            current_score = self.skill_scores[skill_area]
            self.skill_scores[skill_area] = (current_score * 0.4) + (new_score * 0.6)
        
        print(f"Updated skill score for {skill_area}: {self.skill_scores[skill_area]}")
        
        # Adapt difficulty based on performance
        self._adapt_difficulty(new_score)
        
        self.current_question_index += 1
        
        # Check if interview should continue
        if self._should_continue_interview():
            next_question_data = await self._generate_next_question()
            return {
                "message": evaluation.get("feedback", "Thank you for your answer."),
                "next_question": next_question_data["question"],
                "question_format": next_question_data.get("format", "open_ended"),
                "options": next_question_data.get("options"),
                "is_complete": False
            }
        else:
            self.state = SessionState.COMPLETED
            return {
                "message": "Thank you for completing the Excel skills interview. Generating your detailed feedback report...",
                "is_complete": True
            }
    
    def _adapt_difficulty(self, score: float):
        """Adjust difficulty based on candidate performance"""
        if score >= 0.8:
            self.adaptive_difficulty = min(1.0, self.adaptive_difficulty + 0.15)
        elif score <= 0.4:
            self.adaptive_difficulty = max(0.1, self.adaptive_difficulty - 0.15)
        
        print(f"Adapted difficulty to: {self.adaptive_difficulty}")
    
    def _should_continue_interview(self) -> bool:
        """Determine if interview should continue"""
        if self.current_question_index >= self.max_questions:
            return False
        
        # Ensure we have at least the target number of MCQ questions
        if self.mcq_count < self.target_mcq_count:
            return True
        
        # Check if we've covered all required skill areas
        covered_areas = set(q["skill_area"] for q in self.questions_asked)
        required_areas = set(area.value for area in self.skill_areas_to_cover)
        
        if len(covered_areas) < len(required_areas):
            return True
        
        # Continue if we haven't reached minimum questions
        return self.current_question_index < max(6, len(self.skill_areas_to_cover))
    
    async def _generate_next_question(self) -> Dict[str, Any]:
        """Generate the next question based on current state"""
        # Determine question format - prioritize MCQ if we haven't reached target
        should_generate_mcq = (
            self.mcq_count < self.target_mcq_count or 
            (self.current_question_index % 3 == 0 and self.mcq_count < self.max_questions // 2)
        )
        
        question_format = QuestionFormat.MULTIPLE_CHOICE if should_generate_mcq else QuestionFormat.OPEN_ENDED
        
        # Determine which skill area to focus on next
        covered_areas = [q["skill_area"] for q in self.questions_asked]
        uncovered_areas = [area for area in self.skill_areas_to_cover 
                          if area.value not in covered_areas]
        
        if uncovered_areas:
            next_skill_area = uncovered_areas[0]
        else:
            # Focus on areas with lower scores, but prefer MCQ areas if we need more MCQs
            if should_generate_mcq:
                mcq_areas = [area for area in self.skill_areas_to_cover 
                           if "mcq" in area.value.lower()]
                if mcq_areas:
                    next_skill_area = mcq_areas[0]
                else:
                    # Convert regular area to MCQ
                    if self.skill_scores:
                        lowest_score_area = min(self.skill_scores.items(), key=lambda x: x[1])
                        next_skill_area = QuestionType(lowest_score_area[0])
                    else:
                        next_skill_area = self.skill_areas_to_cover[0]
            else:
                if self.skill_scores:
                    lowest_score_area = min(self.skill_scores.items(), key=lambda x: x[1])
                    next_skill_area = QuestionType(lowest_score_area[0])
                else:
                    next_skill_area = self.skill_areas_to_cover[0]
        
        question_data = await self.question_generator.generate_question(
            skill_area=next_skill_area,
            difficulty=self.adaptive_difficulty,
            context={
                "position_level": self.position_level,
                "previous_questions": self.questions_asked,
                "performance_so_far": self.skill_scores
            },
            question_format=question_format
        )
        
        # Update MCQ count if this is an MCQ
        if question_format == QuestionFormat.MULTIPLE_CHOICE:
            self.mcq_count += 1
        
        self.questions_asked.append({
            "question": question_data["question"],
            "skill_area": next_skill_area.value,
            "difficulty": self.adaptive_difficulty,
            "format": question_format.value,
            "options": question_data.get("options"),
            "correct_answer": question_data.get("correct_answer"),
            "timestamp": datetime.now().isoformat()
        })
        
        return question_data
    
    async def generate_final_assessment(self):
        """Generate comprehensive assessment report"""
        print(f"Generating final assessment with skill scores: {self.skill_scores}")
        print(f"Total MCQ questions: {self.mcq_count}")
        
        return await self.feedback_generator.generate_assessment_report(
            candidate_name=self.candidate_name,
            position_level=self.position_level,
            questions_asked=self.questions_asked,
            answers_given=self.answers_given,
            skill_scores=self.skill_scores,
            session_duration=(datetime.now() - self.created_at).total_seconds()
        )
