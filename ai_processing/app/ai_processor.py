import groq
import os

class AIProcessor:
    """
    AIProcessor using Groq as the AI provider.
    """
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.model = model
        self.api_key = os.getenv('GROQ_API_KEY')
        self.client = groq.Groq(api_key=self.api_key)

    async def call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        # Use Groq's chat completion API
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
            return f'{{"error": "{str(e)}"}}'
