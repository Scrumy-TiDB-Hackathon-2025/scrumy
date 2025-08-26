import groq
import os

class AIProcessor:
    """
    AIProcessor using Groq as the AI provider with fallback mode.
    """
    def __init__(self, model: str = "llama3-8b-8192"):
        self.model = model
        self.api_key = os.getenv('GROQ_API_KEY')
        self.fallback_mode = not self.api_key

        if not self.fallback_mode:
            try:
                self.client = groq.Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Groq client initialization failed, using fallback mode: {e}")
                self.fallback_mode = True
                self.client = None
        else:
            print("Warning: No GROQ_API_KEY found, running in fallback mode")
            self.client = None

    async def call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        # Use Groq's chat completion API or fallback mode
        if self.fallback_mode:
            return self._generate_fallback_response(prompt, system_prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2048,
                top_p=1,
                stream=False
            )
            # Return the content of the first choice
            return response.choices[0].message.content
        except Exception as e:
            return self._generate_fallback_response(prompt, system_prompt, f"API Error: {str(e)}")

    def _generate_fallback_response(self, prompt: str, system_prompt: str = "", error_msg: str = "") -> str:
        """Generate a mock response when API is not available"""

        # Detect what type of analysis is being requested
        if "speaker" in prompt.lower() or "identify" in prompt.lower():
            return '''
{
    "speakers": [
        {
            "id": "speaker_1",
            "name": "Demo Speaker 1",
            "segments": ["This is a demo response for speaker identification."],
            "confidence": 0.75
        }
    ],
    "confidence": 0.75,
    "total_speakers": 1,
    "identification_method": "fallback_demo"
}'''

        elif "task" in prompt.lower() or "action" in prompt.lower():
            return '''
{
    "tasks": [
        {
            "id": "demo_task_1",
            "title": "Demo Task - API Key Configuration",
            "description": "Configure GROQ_API_KEY environment variable for full functionality",
            "assignee": "System Administrator",
            "priority": "high",
            "due_date": null,
            "status": "pending"
        }
    ]
}'''

        elif "priority" in prompt.lower():
            return '''
{
    "task_priorities": [
        {
            "task_reference": "API Configuration",
            "priority": "high",
            "urgency_score": 0.9,
            "importance_score": 0.9,
            "business_impact": "high",
            "reasoning": "System requires API key configuration for full functionality"
        }
    ]
}'''

        elif "dependencies" in prompt.lower():
            return '''
{
    "dependencies": [],
    "critical_path": ["Configure API Keys"],
    "parallel_tracks": []
}'''

        else:
            # General summary or other requests
            return f'''
{{
    "summary": "Demo mode active - Configure GROQ_API_KEY for full AI functionality",
    "status": "fallback_mode",
    "note": "This is a fallback response. {error_msg if error_msg else 'API key not configured.'}"
}}'''
