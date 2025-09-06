#!/usr/bin/env python3
"""
Test script for Groq API integration
This script tests the Groq API connection and JSON parsing
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from ai_processor import AIProcessor

async def test_groq_integration():
    """Test Groq API integration with various scenarios"""
    
    print("🧪 Testing Groq API Integration")
    print("=" * 50)
    
    # Load test environment if available
    test_env_path = os.path.join(os.path.dirname(__file__), '.env.test')
    if os.path.exists(test_env_path):
        load_dotenv(test_env_path)
        print("✅ Loaded test environment variables")
    else:
        print("⚠️ No test environment file found")
    
    # Check API key
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        print(f"✅ Groq API key found: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("❌ Groq API key not found")
    
    # Initialize AI processor
    print("\n🤖 Initializing AI Processor...")
    processor = AIProcessor()
    
    # Test 1: Simple JSON request
    print("\n📝 Test 1: Simple JSON Response Request")
    test_prompt = """
    Please analyze this meeting transcript and return a JSON response with speaker identification:
    
    "Hello everyone, this is John speaking. I think we should focus on the quarterly results."
    "Thanks John, this is Sarah. I agree with your assessment."
    
    Return JSON format: {"speakers": [{"name": "John", "segments": [0]}, {"name": "Sarah", "segments": [1]}]}
    """
    
    system_prompt = "You are an expert at analyzing meeting transcripts. Always return valid JSON."
    
    try:
        response = await processor.call_ollama(test_prompt, system_prompt)
        print(f"📄 Raw response: {response}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response)
            print("✅ JSON parsing successful!")
            print(f"📊 Parsed data: {json.dumps(parsed, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("🔍 This is the issue we're fixing!")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
    
    # Test 2: Error handling
    print("\n📝 Test 2: Error Handling")
    if not processor.client:
        print("✅ Error handling test - client not available")
        error_response = await processor.call_ollama("test", "test")
        try:
            parsed_error = json.loads(error_response)
            print("✅ Error response is valid JSON!")
            print(f"📊 Error data: {json.dumps(parsed_error, indent=2)}")
        except json.JSONDecodeError:
            print("❌ Error response is not valid JSON")
    
    print("\n🎯 Test Summary:")
    print("- This script helps identify and fix the 'Failed to parse Groq response as JSON' error")
    print("- The fixes ensure all responses are valid JSON, even error responses")
    print("- Enhanced logging helps debug API issues")

if __name__ == "__main__":
    asyncio.run(test_groq_integration())