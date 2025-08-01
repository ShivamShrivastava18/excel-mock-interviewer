import os
from groq import Groq
from typing import Dict, List, Any
from datetime import datetime
from models.assessment import AssessmentResult, SkillAssessment

class FeedbackGenerator:
    def __init__(self):
        # Load API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    async def generate_assessment_report(self, candidate_name: str, position_level: str,
                                       questions_asked: List[Dict], answers_given: List[Dict],
                                       skill_scores: Dict[str, float], session_duration: float) -> AssessmentResult:
        """Generate comprehensive assessment report"""
        
        # Calculate overall metrics
        overall_score = sum(skill_scores.values()) / len(skill_scores) if skill_scores else 0.0
        overall_level = self._determine_skill_level(overall_score)
        
        print(f"Generating assessment for {candidate_name} with overall score: {overall_score}")
        print(f"Skill scores: {skill_scores}")
        
        # Generate skill-specific assessments
        skill_assessments = []
        for skill_area, score in skill_scores.items():
            skill_assessment = await self._generate_skill_assessment(
                skill_area, score, questions_asked, answers_given
            )
            skill_assessments.append(skill_assessment)
        
        # Generate overall insights based on actual performance
        insights = await self._generate_performance_based_insights(
            candidate_name, position_level, overall_score, skill_scores, session_duration
        )
        
        return AssessmentResult(
            overall_score=overall_score,
            overall_level=overall_level,
            skill_assessments=skill_assessments,
            key_strengths=insights["key_strengths"],
            improvement_recommendations=insights["improvement_recommendations"],
            next_steps=insights["next_steps"],
            interview_summary=insights["interview_summary"],
            generated_at=datetime.now()
        )
    
    async def _generate_performance_based_insights(self, candidate_name: str, position_level: str,
                                                 overall_score: float, skill_scores: Dict[str, float], 
                                                 session_duration: float) -> Dict[str, Any]:
        """Generate insights based on actual performance data"""
        
        duration_minutes = session_duration / 60
        performance_level = self._determine_skill_level(overall_score)
        
        # Determine strongest and weakest areas
        if skill_scores:
            strongest_skill = max(skill_scores.items(), key=lambda x: x[1])
            weakest_skill = min(skill_scores.items(), key=lambda x: x[1])
        else:
            strongest_skill = ("general", 0.5)
            weakest_skill = ("general", 0.5)
        
        prompt = f"""
        Generate specific, performance-based feedback for an Excel skills assessment.

        CANDIDATE: {candidate_name}
        POSITION LEVEL: {position_level}
        OVERALL SCORE: {overall_score:.1%} ({performance_level} level)
        DURATION: {duration_minutes:.1f} minutes
        STRONGEST AREA: {strongest_skill[0].replace('_', ' ')} ({strongest_skill[1]:.1%})
        WEAKEST AREA: {weakest_skill[0].replace('_', ' ')} ({weakest_skill[1]:.1%})
        
        ALL SKILL SCORES:
        {self._format_skill_scores(skill_scores)}

        Based on this ACTUAL performance data, provide specific feedback in JSON format:
        {{
            "key_strengths": [
                "strength based on high-scoring areas",
                "specific skill demonstrated well", 
                "performance-based strength"
            ],
            "improvement_recommendations": [
                "specific area needing work based on low scores",
                "targeted improvement suggestion",
                "skill-specific recommendation"
            ],
            "next_steps": [
                "actionable next step based on performance level",
                "specific learning recommendation",
                "career-relevant suggestion"
            ],
            "interview_summary": "2-3 sentence summary of actual performance, mentioning specific scores and skill levels demonstrated"
        }}

        IMPORTANT: 
        - Base ALL feedback on the actual scores provided
        - If score is high (>70%), focus on advanced skills and expertise shown
        - If score is low (<40%), focus on fundamental gaps and basic improvements needed
        - If score is medium (40-70%), focus on building on existing knowledge
        - Mention specific skill areas by name
        - NO generic responses like "completed assessment" or "showed engagement"
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=600
            )
            
            import json
            import re
            
            response_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                insights = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            return insights
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            # Return performance-based fallback
            return self._create_performance_based_fallback(overall_score, skill_scores, candidate_name)
    
    def _create_performance_based_fallback(self, overall_score: float, skill_scores: Dict[str, float], candidate_name: str) -> Dict[str, Any]:
        """Create performance-specific fallback when AI generation fails"""
        
        if overall_score >= 0.8:
            return {
                "key_strengths": [
                    f"Demonstrated expert-level Excel knowledge with {overall_score:.0%} overall score",
                    f"Excelled in {max(skill_scores.items(), key=lambda x: x[1])[0].replace('_', ' ')} with strong technical skills",
                    "Provided detailed, accurate explanations showing deep understanding"
                ],
                "improvement_recommendations": [
                    "Continue exploring advanced Excel features and automation",
                    "Consider sharing knowledge through mentoring or training others",
                    "Stay updated with latest Excel updates and Power Platform integration"
                ],
                "next_steps": [
                    "Pursue advanced Excel certifications or Power BI training",
                    "Take on complex data analysis projects requiring advanced Excel skills",
                    "Consider roles requiring expert-level spreadsheet and data analysis capabilities"
                ],
                "interview_summary": f"{candidate_name} demonstrated exceptional Excel proficiency with a {overall_score:.0%} score, showing expert-level skills across multiple areas and providing comprehensive, technically accurate responses."
            }
        elif overall_score >= 0.6:
            return {
                "key_strengths": [
                    f"Solid Excel foundation with {overall_score:.0%} overall performance",
                    f"Strong performance in {max(skill_scores.items(), key=lambda x: x[1])[0].replace('_', ' ')}",
                    "Good understanding of core Excel concepts and practical applications"
                ],
                "improvement_recommendations": [
                    f"Focus on strengthening {min(skill_scores.items(), key=lambda x: x[1])[0].replace('_', ' ')} skills",
                    "Practice more complex scenarios and advanced functions",
                    "Develop deeper understanding of Excel's analytical capabilities"
                ],
                "next_steps": [
                    "Take intermediate to advanced Excel courses",
                    "Practice with real-world datasets and business scenarios",
                    "Learn advanced functions like INDEX/MATCH, pivot table calculations"
                ],
                "interview_summary": f"{candidate_name} showed good Excel competency with a {overall_score:.0%} score, demonstrating solid understanding in most areas with room for growth in advanced features."
            }
        elif overall_score >= 0.3:
            return {
                "key_strengths": [
                    f"Basic Excel knowledge foundation with {overall_score:.0%} score",
                    "Understanding of fundamental spreadsheet concepts",
                    "Willingness to engage with Excel-based tasks"
                ],
                "improvement_recommendations": [
                    "Focus on mastering basic Excel functions and formulas",
                    "Practice fundamental data manipulation and formatting",
                    "Learn essential features like sorting, filtering, and basic charts"
                ],
                "next_steps": [
                    "Enroll in beginner Excel training courses",
                    "Practice daily with guided Excel tutorials",
                    "Start with simple datasets to build confidence and skills"
                ],
                "interview_summary": f"{candidate_name} demonstrated basic Excel awareness with a {overall_score:.0%} score, showing foundational understanding but requiring significant skill development for professional Excel use."
            }
        else:
            return {
                "key_strengths": [
                    "Participated in the complete assessment process",
                    "Showed willingness to attempt Excel-related questions"
                ],
                "improvement_recommendations": [
                    "Start with fundamental Excel basics and core concepts",
                    "Learn essential spreadsheet navigation and data entry",
                    "Focus on understanding basic formulas and cell references"
                ],
                "next_steps": [
                    "Begin with introductory Excel courses or tutorials",
                    "Practice basic spreadsheet operations daily",
                    "Consider one-on-one Excel training or mentoring"
                ],
                "interview_summary": f"{candidate_name} completed the assessment with a {overall_score:.0%} score, indicating the need for comprehensive Excel training starting from fundamental concepts."
            }
    
    def _format_skill_scores(self, skill_scores: Dict[str, float]) -> str:
        """Format skill scores for prompt"""
        formatted = []
        for skill, score in skill_scores.items():
            formatted.append(f"- {skill.replace('_', ' ').title()}: {score:.1%}")
        return "\n".join(formatted)
    
    async def _generate_skill_assessment(self, skill_area: str, score: float,
                                       questions_asked: List[Dict], answers_given: List[Dict]) -> SkillAssessment:
        """Generate assessment for a specific skill area"""
        
        # Find relevant questions and answers for this skill area
        relevant_qa = []
        for i, question_data in enumerate(questions_asked):
            if question_data["skill_area"] == skill_area and i < len(answers_given):
                relevant_qa.append({
                    "question": question_data["question"],
                    "answer": answers_given[i]["answer"],
                    "evaluation": answers_given[i]["evaluation"]
                })
        
        # Generate performance-specific strengths and improvements
        if score >= 0.8:
            strengths = [
                f"Excellent {skill_area.replace('_', ' ')} knowledge demonstrated",
                "Provided detailed, accurate technical explanations",
                "Showed advanced understanding of complex concepts"
            ]
            improvements = [
                "Continue exploring cutting-edge features in this area",
                "Consider advanced certifications or specializations"
            ]
        elif score >= 0.6:
            strengths = [
                f"Good grasp of {skill_area.replace('_', ' ')} fundamentals",
                "Solid understanding of key concepts",
                "Practical approach to problem-solving"
            ]
            improvements = [
                f"Deepen knowledge of advanced {skill_area.replace('_', ' ')} features",
                "Practice more complex scenarios in this area"
            ]
        elif score >= 0.3:
            strengths = [
                f"Basic understanding of {skill_area.replace('_', ' ')} concepts",
                "Awareness of fundamental principles"
            ]
            improvements = [
                f"Strengthen core {skill_area.replace('_', ' ')} skills",
                "Practice fundamental operations and functions",
                "Focus on building confidence in this area"
            ]
        else:
            strengths = [
                "Attempted to address the questions in this area"
            ]
            improvements = [
                f"Requires comprehensive training in {skill_area.replace('_', ' ')}",
                "Start with basic tutorials and guided practice",
                "Focus on fundamental concepts before advancing"
            ]
        
        return SkillAssessment(
            skill_area=skill_area.replace('_', ' ').title(),
            score=score,
            level=self._determine_skill_level(score),
            strengths=strengths,
            areas_for_improvement=improvements
        )
    
    def _determine_skill_level(self, score: float) -> str:
        """Convert numeric score to skill level"""
        if score >= 0.85:
            return "Expert"
        elif score >= 0.7:
            return "Advanced"
        elif score >= 0.5:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _format_qa_for_analysis(self, qa_pairs: List[Dict]) -> str:
        """Format question-answer pairs for analysis"""
        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            formatted.append(f"""
            Q{i}: {qa['question']}
            A{i}: {qa['answer']}
            Score: {qa['evaluation'].get('overall_score', 0):.2f}
            """)
        return "\n".join(formatted)