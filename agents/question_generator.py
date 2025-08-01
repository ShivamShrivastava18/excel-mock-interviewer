import os
from groq import Groq
from typing import Dict, Any
from models.session import QuestionType, QuestionFormat
import json
import re

class QuestionGenerator:
    def __init__(self):
        # Load API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        
        # Question templates and scenarios
        self.question_templates = {
            QuestionType.FORMULA_BASIC: {
                "beginner": ["SUM and AVERAGE functions", "simple COUNT functions", "basic cell references"],
                "intermediate": ["IF statements", "CONCATENATE", "basic logical functions (AND, OR)"],
                "advanced": ["nested IF statements", "complex logical combinations", "text manipulation functions"]
            },
            QuestionType.FORMULA_ADVANCED: {
                "beginner": ["simple VLOOKUP", "basic INDEX/MATCH"],
                "intermediate": ["VLOOKUP with approximate match", "nested lookup functions"],
                "advanced": ["array formulas", "dynamic arrays", "complex nested functions"]
            },
            QuestionType.DATA_ANALYSIS: {
                "beginner": ["sorting data", "basic filtering", "simple formatting"],
                "intermediate": ["advanced filters", "conditional formatting", "data validation"],
                "advanced": ["complex conditional formatting", "advanced data validation", "data analysis tools"]
            },
            QuestionType.PIVOT_TABLES: {
                "beginner": ["creating basic pivot tables", "simple field arrangements"],
                "intermediate": ["pivot table calculations", "grouping data", "pivot charts"],
                "advanced": ["calculated fields", "slicers and timelines", "advanced pivot features"]
            },
            QuestionType.CHARTS_VISUALIZATION: {
                "beginner": ["basic chart creation", "chart types selection"],
                "intermediate": ["chart formatting", "multiple data series", "chart customization"],
                "advanced": ["dashboard creation", "advanced chart types", "interactive visualizations"]
            },
            QuestionType.MCQ_BASIC: {
                "beginner": ["basic Excel functions", "cell references", "simple formulas"],
                "intermediate": ["intermediate functions", "data formatting", "basic analysis"],
                "advanced": ["advanced functions", "complex formulas", "data manipulation"]
            },
            QuestionType.MCQ_ADVANCED: {
                "beginner": ["pivot table basics", "chart creation", "data validation"],
                "intermediate": ["advanced pivot tables", "complex charts", "data analysis"],
                "advanced": ["macros and VBA", "advanced analysis", "automation"]
            }
        }
    
    async def generate_question(self, skill_area: QuestionType, difficulty: float, context: Dict[str, Any], 
                              question_format: QuestionFormat = QuestionFormat.OPEN_ENDED) -> Dict[str, Any]:
        """Generate a contextual question for the specified skill area and format"""
        
        if question_format == QuestionFormat.MULTIPLE_CHOICE:
            return await self._generate_mcq_question(skill_area, difficulty, context)
        else:
            return await self._generate_open_ended_question(skill_area, difficulty, context)
    
    async def _generate_mcq_question(self, skill_area: QuestionType, difficulty: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a multiple choice question"""
        
        difficulty_text = self._get_difficulty_text(difficulty)
        position_level = context.get('position_level', 'intermediate')
        
        # Get level-appropriate topics
        skill_templates = self.question_templates.get(skill_area, {})
        if isinstance(skill_templates, dict):
            topics = skill_templates.get(position_level, skill_templates.get('intermediate', ["general Excel skills"]))
        else:
            topics = skill_templates
        
        prompt = f"""
        Create a multiple choice question for Excel skills at {difficulty_text} difficulty level.

        Skill Focus: {skill_area.value.replace('_', ' ')} - {', '.join(topics)}
        Difficulty: {difficulty_text}
        Position Level: {position_level}

        Requirements:
        1. Create a clear, practical Excel question
        2. Provide exactly 4 answer options (A, B, C, D)
        3. Make sure only ONE option is clearly correct
        4. Include plausible but incorrect distractors
        5. Focus on real-world Excel scenarios

        Return your response in this exact JSON format:
        {{
            "question": "Your question text here",
            "options": [
                "A) First option",
                "B) Second option", 
                "C) Third option",
                "D) Fourth option"
            ],
            "correct_answer": "A",
            "explanation": "Brief explanation of why this answer is correct"
        }}

        Make the question practical and job-relevant. Avoid overly technical jargon.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group())
                
                # Validate the structure
                required_fields = ["question", "options", "correct_answer", "explanation"]
                if all(field in question_data for field in required_fields):
                    question_data["format"] = "multiple_choice"
                    return question_data
            
            # Fallback if JSON parsing fails
            return self._create_fallback_mcq(skill_area, difficulty_text)
            
        except Exception as e:
            print(f"Error generating MCQ: {e}")
            return self._create_fallback_mcq(skill_area, difficulty_text)
    
    async def _generate_open_ended_question(self, skill_area: QuestionType, difficulty: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an open-ended question (existing logic)"""
        
        difficulty_text = self._get_difficulty_text(difficulty)
        position_level = context.get('position_level', 'intermediate')
        
        # Get level-appropriate topics
        skill_templates = self.question_templates.get(skill_area, {})
        if isinstance(skill_templates, dict):
            topics = skill_templates.get(position_level, skill_templates.get('intermediate', ["general Excel skills"]))
        else:
            topics = skill_templates
        
        # Create difficulty-specific prompts
        if difficulty < 0.4:  # Beginner
            complexity_instruction = "Keep the scenario simple with basic data. Focus on fundamental concepts."
            example_instruction = "Example: A small table with 10-20 rows of data."
        elif difficulty < 0.7:  # Intermediate  
            complexity_instruction = "Use moderate complexity with realistic business scenarios."
            example_instruction = "Example: A dataset with 50-100 rows requiring multiple steps."
        else:  # Advanced
            complexity_instruction = "Create complex, multi-step scenarios requiring advanced techniques."
            example_instruction = "Example: Large datasets with multiple conditions and advanced formulas."
        
        prompt = f"""
        Create a clear, well-structured Excel question for {skill_area.value.replace('_', ' ')} at {difficulty_text} difficulty level.

        Skill Focus: {', '.join(topics)}
        Difficulty: {difficulty_text} ({complexity_instruction})
        Position Level: {position_level}

        Requirements:
        1. Start with a clear business scenario
        2. Provide specific data context (column names, data types, row counts)
        3. Ask for a specific solution with explanation
        4. {example_instruction}
        5. End with "Please explain your approach and the formulas you would use."

        Format:
        - Use clear paragraphs
        - No meta-commentary or prefixes
        - No asterisks or formatting markers
        - Return ONLY the question content

        {complexity_instruction}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        
        # Clean up the response
        question = response.choices[0].message.content.strip()
        
        # Remove common AI response artifacts
        artifacts_to_remove = [
            "Here's your intermediate difficulty question:",
            "Here's your beginner difficulty question:", 
            "Here's your advanced difficulty question:",
            "Here's a question:",
            "**Question:**",
            "Question:",
            "Here's your question:",
            "Here is a",
            "Here's a"
        ]
        
        for artifact in artifacts_to_remove:
            if question.startswith(artifact):
                question = question[len(artifact):].strip()
                break
        
        # Remove asterisks and formatting markers
        question = question.replace("**", "").replace("*", "")
        
        # Clean up any remaining formatting issues
        question = question.replace("  ", " ").strip()
        
        return {
            "question": question,
            "format": "open_ended"
        }
    
    def _create_fallback_mcq(self, skill_area: QuestionType, difficulty_text: str) -> Dict[str, Any]:
        """Create a fallback MCQ when AI generation fails"""
        
        fallback_questions = {
            "formula_basic": {
                "question": "Which Excel function would you use to calculate the average of values in cells A1 through A10?",
                "options": [
                    "A) =AVERAGE(A1:A10)",
                    "B) =AVG(A1:A10)", 
                    "C) =MEAN(A1:A10)",
                    "D) =SUM(A1:A10)/10"
                ],
                "correct_answer": "A",
                "explanation": "AVERAGE is the correct Excel function to calculate the mean of a range of cells."
            },
            "data_analysis": {
                "question": "What is the keyboard shortcut to apply an AutoFilter to a data range in Excel?",
                "options": [
                    "A) Ctrl+Shift+L",
                    "B) Ctrl+Alt+F",
                    "C) Ctrl+F",
                    "D) Alt+D+F"
                ],
                "correct_answer": "A",
                "explanation": "Ctrl+Shift+L is the keyboard shortcut to toggle AutoFilter on and off."
            }
        }
        
        # Get appropriate fallback or use default
        skill_key = skill_area.value.replace("mcq_", "").replace("_advanced", "").replace("_basic", "")
        fallback = fallback_questions.get(skill_key, fallback_questions["formula_basic"])
        fallback["format"] = "multiple_choice"
        
        return fallback
    
    def _get_difficulty_text(self, difficulty: float) -> str:
        """Convert difficulty score to text description"""
        if difficulty < 0.4:
            return "beginner"
        elif difficulty < 0.7:
            return "intermediate"  
        else:
            return "advanced"
    
    def _build_performance_context(self, skill_scores: Dict[str, float]) -> str:
        """Build context string from previous performance"""
        strong_areas = [skill for skill, score in skill_scores.items() if score > 0.7]
        weak_areas = [skill for skill, score in skill_scores.items() if score < 0.5]
        
        context_parts = []
        if strong_areas:
            context_parts.append(f"Strong in: {', '.join(strong_areas)}")
        if weak_areas:
            context_parts.append(f"Needs improvement in: {', '.join(weak_areas)}")
        
        return "; ".join(context_parts) if context_parts else "Consistent performance"