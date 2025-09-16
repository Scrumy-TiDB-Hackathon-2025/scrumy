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
            
            # Enhance system prompt to ensure JSON response
            enhanced_system_prompt = system_prompt + "\n\nIMPORTANT: You must respond with valid JSON only. Do not include any explanatory text before or after the JSON. Do not wrap the JSON in markdown code blocks."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": prompt + "\n\nRemember: Respond with valid JSON only, no additional text or formatting."}
                ],
                temperature=0.2,
                max_tokens=2048,
                top_p=1,
                stream=False
            )
            
            # Get the raw response content
            raw_result = response.choices[0].message.content
            print(f"✅ Groq API response received: {len(raw_result)} characters")
            
            # Log first 200 characters for debugging
            print(f"📄 Raw response preview: {raw_result[:200]}...")
            
            # Extract and validate JSON from the response
            cleaned_result = self._extract_and_validate_json(raw_result)
            
            print(f"📄 Cleaned response preview: {cleaned_result[:200]}...")
            
            return cleaned_result
            
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
    
    def _extract_and_validate_json(self, response: str) -> str:
        """Extract and validate JSON from AI response that might contain extra text"""
        import json
        import re
        
        if not response or not response.strip():
            return '{"error": "Empty response", "speakers": [], "analysis": "No content received"}'
        
        # Try to parse as-is first
        try:
            json.loads(response.strip())
            return response.strip()
        except json.JSONDecodeError:
            pass
        
        # Remove markdown code blocks if present
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Try parsing after removing markdown
        try:
            json.loads(cleaned.strip())
            return cleaned.strip()
        except json.JSONDecodeError:
            pass
        
        # Look for JSON object in the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            potential_json = json_match.group(0)
            try:
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass
        
        # Look for JSON array in the response
        json_array_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_array_match:
            potential_json = json_array_match.group(0)
            try:
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass
        
        # If all else fails, return a structured error response
        print(f"⚠️ Could not extract valid JSON from response: {response[:100]}...")
        error_response = {
            "error": "Invalid JSON response from AI",
            "raw_response": response[:500] if response else "Empty response",  # First 500 chars for debugging
            "speakers": [],
            "analysis": "Could not parse AI response as JSON"
        }
        return json.dumps(error_response)
