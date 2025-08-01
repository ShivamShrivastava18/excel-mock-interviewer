import os
from groq import Groq
from typing import Dict, Any
import json
import re

class AnswerEvaluator:
    def __init__(self):
        # Load API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    async def evaluate_answer(self, question: str, answer: str, skill_area: str, expected_difficulty: float,
                            question_format: str = "open_ended", options: list = None, correct_answer: str = None) -> Dict[str, Any]:
        """Evaluate candidate's answer with detailed scoring and feedback"""
        
        if question_format == "multiple_choice":
            return await self._evaluate_mcq_answer(question, answer, skill_area, options, correct_answer)
        else:
            return await self._evaluate_open_ended_answer(question, answer, skill_area, expected_difficulty)
    
    async def _evaluate_mcq_answer(self, question: str, answer: str, skill_area: str, 
                                 options: list, correct_answer: str) -> Dict[str, Any]:
        """Evaluate multiple choice question answer"""
        
        # Clean the answer to extract just the letter (A, B, C, D)
        answer_letter = self._extract_answer_letter(answer)
        is_correct = answer_letter.upper() == correct_answer.upper()
        
        # Score: 1.0 for correct, 0.0 for incorrect (MCQs are binary)
        score = 1.0 if is_correct else 0.0
        
        # Generate feedback based on correctness
        if is_correct:
            feedback = f"Correct! You selected the right answer for this {skill_area.replace('_', ' ')} question."
            strengths = ["Accurate knowledge demonstrated", "Correct understanding of the concept"]
            improvements = ["Continue building on this knowledge", "Practice similar concepts"]
        else:
            feedback = f"Incorrect. The correct answer was {correct_answer}. This {skill_area.replace('_', ' ')} question tests fundamental knowledge."
            strengths = ["Attempted the question", "Engaged with the material"]
            improvements = ["Review this concept area", "Practice more questions on this topic", "Study the fundamentals"]
        
        return {
            "technical_accuracy": score * 10,
            "completeness": score * 10,
            "practical_understanding": score * 10,
            "communication_clarity": 10,  # MCQ doesn't test communication
            "overall_score": score,
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "feedback": feedback,
            "follow_up_suggestions": self._get_mcq_suggestions(is_correct, skill_area),
            "is_mcq": True,
            "selected_answer": answer_letter,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        }
    
    async def _evaluate_open_ended_answer(self, question: str, answer: str, skill_area: str, expected_difficulty: float) -> Dict[str, Any]:
        """Evaluate open-ended answer (existing logic)"""
        
        # First, do a quick assessment to determine if this is a good or poor answer
        quality_prompt = f"""
        Evaluate this Excel skills answer on a scale of 0-10:

        QUESTION: {question}
        ANSWER: {answer}

        Rate the answer considering:
        - Technical accuracy of Excel knowledge
        - Completeness of the response
        - Practical understanding shown
        - Quality of explanation

        Respond with just a number from 0-10, where:
        0-2 = Very poor/incorrect
        3-4 = Poor with major issues  
        5-6 = Average/basic understanding
        7-8 = Good with solid knowledge
        9-10 = Excellent/expert level

        Just return the number, nothing else.
        """
        
        try:
            quality_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": quality_prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            # Extract the numeric score
            quality_text = quality_response.choices[0].message.content.strip()
            quality_score = float(re.findall(r'\d+', quality_text)[0]) if re.findall(r'\d+', quality_text) else 5
            quality_score = max(0, min(10, quality_score))  # Clamp between 0-10
            
        except Exception as e:
            print(f"Error in quality assessment: {e}")
            quality_score = 5  # Default to middle score
        
        # Now generate detailed evaluation based on the quality score
        detailed_prompt = f"""
        Provide a detailed evaluation of this Excel skills answer.

        QUESTION: {question}
        ANSWER: {answer}
        SKILL AREA: {skill_area}
        QUALITY SCORE: {quality_score}/10

        Based on the quality score of {quality_score}/10, provide evaluation in this exact JSON format:
        {{
            "technical_accuracy": {quality_score},
            "completeness": {max(0, quality_score - 1)},
            "practical_understanding": {max(0, quality_score - 0.5)},
            "communication_clarity": {min(10, quality_score + 1)},
            "overall_score": {quality_score / 10},
            "strengths": {self._get_strengths_for_score(quality_score)},
            "areas_for_improvement": {self._get_improvements_for_score(quality_score)},
            "feedback": "{self._get_feedback_for_score(quality_score, skill_area)}",
            "follow_up_suggestions": {self._get_suggestions_for_score(quality_score, skill_area)}
        }}

        Make the feedback specific to the actual answer quality. If the score is low, be honest about deficiencies.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": detailed_prompt}],
                temperature=0.3,
                max_tokens=600
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            # Ensure score is normalized to 0-1 range
            if evaluation.get("overall_score", 0) > 1:
                evaluation["overall_score"] = evaluation["overall_score"] / 10
            
            # Ensure all required fields exist
            evaluation = self._ensure_complete_evaluation(evaluation, quality_score, skill_area)
            evaluation["is_mcq"] = False
            
            return evaluation
        
        except Exception as e:
            print(f"Error in detailed evaluation: {e}")
            # Return a proper evaluation based on quality score
            return self._create_fallback_evaluation(quality_score, skill_area, answer)
    
    def _extract_answer_letter(self, answer: str) -> str:
        """Extract the letter choice (A, B, C, D) from the answer"""
        answer = answer.strip().upper()
        
        # Look for patterns like "A)", "A.", "A", "(A)", etc.
        patterns = [
            r'^([ABCD])\)',
            r'^([ABCD])\.',
            r'^$$([ABCD])$$',
            r'^([ABCD])$',
            r'OPTION\s+([ABCD])',
            r'ANSWER\s+([ABCD])',
            r'([ABCD])\s*[-:]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, answer)
            if match:
                return match.group(1)
        
        # If no clear pattern, look for any A, B, C, D in the answer
        for letter in ['A', 'B', 'C', 'D']:
            if letter in answer:
                return letter
        
        # Default to A if nothing found
        return 'A'
    
    def _get_mcq_suggestions(self, is_correct: bool, skill_area: str) -> list:
        """Generate suggestions for MCQ answers"""
        if is_correct:
            return [
                "Continue practicing similar questions",
                "Build on this knowledge with more advanced topics",
                "Apply this concept in practical scenarios"
            ]
        else:
            return [
                f"Review {skill_area.replace('_', ' ')} fundamentals",
                "Practice more multiple choice questions on this topic",
                "Study Excel documentation for this concept",
                "Try hands-on practice with Excel"
            ]
    
    def _get_strengths_for_score(self, score: float) -> list:
        """Generate strengths based on score"""
        if score >= 8:
            return ["Excellent technical knowledge", "Clear and detailed explanation", "Practical approach demonstrated"]
        elif score >= 6:
            return ["Good understanding of concepts", "Adequate explanation provided", "Shows practical awareness"]
        elif score >= 4:
            return ["Basic understanding shown", "Attempted to address the question", "Some relevant points made"]
        else:
            return ["Participated in the assessment", "Provided a response"]
    
    def _get_improvements_for_score(self, score: float) -> list:
        """Generate improvement areas based on score"""
        if score >= 8:
            return ["Could explore more advanced techniques", "Consider edge cases in solutions"]
        elif score >= 6:
            return ["Could provide more detailed explanations", "Practice more complex scenarios"]
        elif score >= 4:
            return ["Need to improve technical accuracy", "Should provide more complete explanations", "Practice fundamental concepts"]
        else:
            return ["Requires significant improvement in Excel knowledge", "Need to study basic Excel functions", "Should practice with guided tutorials"]
    
    def _get_feedback_for_score(self, score: float, skill_area: str) -> str:
        """Generate feedback based on score"""
        skill_name = skill_area.replace('_', ' ').title()
        
        if score >= 8:
            return f"Excellent work on this {skill_name} question! Your answer demonstrates strong technical knowledge and practical understanding."
        elif score >= 6:
            return f"Good response to this {skill_name} question. You show solid understanding with room for more detail in your explanations."
        elif score >= 4:
            return f"Your answer shows basic understanding of {skill_name}, but there are some technical inaccuracies that need attention."
        else:
            return f"This {skill_name} answer needs significant improvement. The response shows limited understanding of the concepts involved."
    
    def _get_suggestions_for_score(self, score: float, skill_area: str) -> list:
        """Generate suggestions based on score"""
        if score >= 8:
            return ["Explore advanced Excel features", "Consider teaching others these concepts"]
        elif score >= 6:
            return ["Practice explaining solutions step-by-step", "Try more complex scenarios"]
        elif score >= 4:
            return ["Review Excel documentation for this topic", "Practice with simpler examples first"]
        else:
            return ["Start with basic Excel tutorials", "Practice fundamental concepts daily", "Consider taking a structured Excel course"]
    
    def _ensure_complete_evaluation(self, evaluation: dict, quality_score: float, skill_area: str) -> dict:
        """Ensure evaluation has all required fields"""
        defaults = {
            "technical_accuracy": quality_score,
            "completeness": max(0, quality_score - 1),
            "practical_understanding": max(0, quality_score - 0.5),
            "communication_clarity": min(10, quality_score + 1),
            "overall_score": quality_score / 10,
            "strengths": self._get_strengths_for_score(quality_score),
            "areas_for_improvement": self._get_improvements_for_score(quality_score),
            "feedback": self._get_feedback_for_score(quality_score, skill_area),
            "follow_up_suggestions": self._get_suggestions_for_score(quality_score, skill_area)
        }
        
        for key, default_value in defaults.items():
            if key not in evaluation:
                evaluation[key] = default_value
        
        return evaluation
    
    def _create_fallback_evaluation(self, quality_score: float, skill_area: str, answer: str) -> dict:
        """Create a complete evaluation when AI parsing fails"""
        
        # Determine if answer is very short or empty
        if len(answer.strip()) < 10:
            quality_score = min(quality_score, 2)
        
        return {
            "technical_accuracy": quality_score,
            "completeness": max(0, quality_score - 1),
            "practical_understanding": max(0, quality_score - 0.5),
            "communication_clarity": min(10, quality_score + 1),
            "overall_score": quality_score / 10,
            "strengths": self._get_strengths_for_score(quality_score),
            "areas_for_improvement": self._get_improvements_for_score(quality_score),
            "feedback": self._get_feedback_for_score(quality_score, skill_area),
            "follow_up_suggestions": self._get_suggestions_for_score(quality_score, skill_area),
            "is_mcq": False
        }
    
    async def evaluate_overall_performance(self, all_evaluations: list) -> Dict[str, Any]:
        """Evaluate overall performance across all questions"""
        if not all_evaluations:
            return {"overall_score": 0.0, "level": "Insufficient data"}
        
        # Calculate weighted averages
        total_score = sum(eval_data["overall_score"] for eval_data in all_evaluations)
        average_score = total_score / len(all_evaluations)
        
        # Count MCQ vs open-ended performance
        mcq_scores = [eval_data["overall_score"] for eval_data in all_evaluations if eval_data.get("is_mcq", False)]
        open_ended_scores = [eval_data["overall_score"] for eval_data in all_evaluations if not eval_data.get("is_mcq", False)]
        
        # Determine skill level based on actual performance
        if average_score >= 0.85:
            level = "Expert"
        elif average_score >= 0.7:
            level = "Advanced"
        elif average_score >= 0.5:
            level = "Intermediate"
        else:
            level = "Beginner"
        
        # Aggregate strengths and improvement areas
        all_strengths = []
        all_improvements = []
        
        for evaluation in all_evaluations:
            all_strengths.extend(evaluation.get("strengths", []))
            all_improvements.extend(evaluation.get("areas_for_improvement", []))
        
        # Remove duplicates while preserving order
        unique_strengths = list(dict.fromkeys(all_strengths))
        unique_improvements = list(dict.fromkeys(all_improvements))
        
        return {
            "overall_score": average_score,
            "level": level,
            "strengths": unique_strengths[:5],  # Top 5 strengths
            "areas_for_improvement": unique_improvements[:5],  # Top 5 areas
            "total_questions": len(all_evaluations),
            "mcq_count": len(mcq_scores),
            "open_ended_count": len(open_ended_scores),
            "mcq_average": sum(mcq_scores) / len(mcq_scores) if mcq_scores else 0,
            "open_ended_average": sum(open_ended_scores) / len(open_ended_scores) if open_ended_scores else 0,
            "consistency": self._calculate_consistency(all_evaluations)
        }
    
    def _calculate_consistency(self, evaluations: list) -> float:
        """Calculate consistency of performance across questions"""
        if len(evaluations) < 2:
            return 1.0
        
        scores = [eval_data["overall_score"] for eval_data in evaluations]
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        consistency = max(0, 1 - (variance * 4))  # Scale factor of 4
        return round(consistency, 2)