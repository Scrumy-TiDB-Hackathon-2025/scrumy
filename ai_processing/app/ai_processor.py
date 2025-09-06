import groq
import os

class AIProcessor:
    """
    AIProcessor using Groq as the AI provider.
    """
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.model = model
        self.api_key = os.getenv('GROQ_API_KEY')
        
        # Initialize client only if API key is available
        if self.api_key:
            try:
                self.client = groq.Groq(api_key=self.api_key)
                print(f"✅ Groq client initialized with model: {self.model}")
            except Exception as e:
                print(f"❌ Failed to initialize Groq client: {e}")
                self.client = None
        else:
            print("⚠️ Groq API key not found in environment variables")
            self.client = None

    async def call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        # Use Groq's chat completion API
        try:
            # Check if client is available
            if not self.client:
                print("⚠️ Groq client not available - skipping AI processing")
                return '{"error": "Groq client not initialized", "speakers": [], "analysis": "Client unavailable"}'
            
            print(f"🤖 Making Groq API call with model: {self.model}")
            print(f"📝 Prompt length: {len(prompt)} characters")
            
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
            result = response.choices[0].message.content
            print(f"✅ Groq API response received: {len(result)} characters")
            
            # Log first 200 characters for debugging
            print(f"📄 Response preview: {result[:200]}...")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Groq API error: {error_msg}")
            
            # Return valid JSON error response
            import json
            error_response = {
                "error": error_msg,
                "speakers": [],
                "analysis": "API call failed",
                "model": self.model
            }
            return json.dumps(error_response)
