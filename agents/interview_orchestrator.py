import os
from groq import Groq
from typing import Dict, Any

class InterviewOrchestrator:
    def __init__(self):
        # Load API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    async def generate_welcome_message(self, candidate_name: str, position_level: str) -> str:
        """Generate personalized welcome message"""
        prompt = f"""
        Generate a warm, professional welcome message for {candidate_name} starting an Excel skills assessment at {position_level} level.

        Requirements:
        - Address them by name
        - Briefly explain the process (8-15 questions, adapts to skill level)
        - Encourage detailed explanations
        - Keep it natural and conversational
        - NO placeholder text or formatting instructions
        - 2-3 sentences maximum

        Return ONLY the welcome message, nothing else.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=150
        )
        
        # Clean up the response to remove any meta-commentary
        message = response.choices[0].message.content.strip()
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "Here is a warm and professional welcome message:",
            "Here's a welcome message:",
            "Welcome message:",
            "Here is the message:",
            "Here's the welcome message:"
        ]
        
        for prefix in prefixes_to_remove:
            if message.startswith(prefix):
                message = message[len(prefix):].strip()
                break
        
        # Remove quotes if the entire message is wrapped in them
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        
        return message
    
    async def should_continue_interview(self, context: Dict[str, Any]) -> bool:
        """Determine if interview should continue based on current context"""
        # This could use AI to make more sophisticated decisions
        # For now, using rule-based logic in the session class
        return True
    
    async def generate_transition_message(self, from_skill: str, to_skill: str, performance: float) -> str:
        """Generate smooth transitions between different skill areas"""
        performance_text = "excellent" if performance > 0.8 else "good" if performance > 0.6 else "developing"
        
        prompt = f"""
        Generate a brief, encouraging transition message for an Excel skills interview.
        The candidate just finished questions about {from_skill} with {performance_text} performance.
        Now moving to questions about {to_skill}.
        
        Keep it to 1-2 sentences, professional but encouraging.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()