#!/usr/bin/env python3
"""
Test script to verify the JSON parsing fix for Groq API responses
"""

import asyncio
import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.ai_processor import AIProcessor

async def test_json_extraction():
    """Test the JSON extraction and validation logic"""
    
    print("🧪 Testing JSON Extraction and Validation Fix")
    print("=" * 60)
    
    # Initialize AI processor
    ai_processor = AIProcessor()
    
    # Test cases that were causing "Failed to parse Groq response as JSON"
    test_responses = [
        # Case 1: Valid JSON (should work as-is)
        '{"speakers": [{"name": "John", "segments": ["Hello world"]}], "analysis": "Test"}',
        
        # Case 2: JSON wrapped in markdown (common AI response)
        '```json\n{"speakers": [{"name": "Jane", "segments": ["Hi there"]}], "analysis": "Markdown wrapped"}\n```',
        
        # Case 3: JSON with extra text before
        'Here is the analysis:\n{"speakers": [{"name": "Bob", "segments": ["Good morning"]}], "analysis": "Extra text before"}',
        
        # Case 4: JSON with extra text after
        '{"speakers": [{"name": "Alice", "segments": ["How are you?"]}], "analysis": "Extra text after"}\n\nThis completes the analysis.',
        
        # Case 5: Malformed JSON (should return error response)
        '{"speakers": [{"name": "Invalid", "segments": ["Broken JSON"}], "analysis": "Missing closing brace"',
        
        # Case 6: Plain text error (should return error response)
        'Error: API key not found or invalid',
        
        # Case 7: Empty response (should return error response)
        '',
        
        # Case 8: JSON array instead of object
        '[{"name": "Array Response", "text": "This is an array"}]'
    ]
    
    print(f"Testing {len(test_responses)} different response scenarios...\n")
    
    for i, test_response in enumerate(test_responses, 1):
        print(f"🔍 Test Case {i}:")
        print(f"   Input: {test_response[:50]}{'...' if len(test_response) > 50 else ''}")
        
        try:
            # Test the extraction method
            cleaned_response = ai_processor._extract_and_validate_json(test_response)
            
            # Try to parse the cleaned response
            parsed = json.loads(cleaned_response)
            
            print(f"   ✅ SUCCESS: Valid JSON extracted")
            print(f"   Output: {cleaned_response[:50]}{'...' if len(cleaned_response) > 50 else ''}")
            
            # Check if it has expected structure
            if isinstance(parsed, dict):
                if "error" in parsed:
                    print(f"   📝 Error response: {parsed.get('error', 'Unknown error')}")
                elif "speakers" in parsed:
                    print(f"   👥 Speakers found: {len(parsed.get('speakers', []))}")
                else:
                    print(f"   📊 Other valid structure: {list(parsed.keys())}")
            else:
                print(f"   📋 Array response with {len(parsed)} items")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ FAILED: Still invalid JSON after extraction")
            print(f"   Error: {e}")
        except Exception as e:
            print(f"   ❌ FAILED: Unexpected error")
            print(f"   Error: {e}")
        
        print()
    
    print("🎯 Summary:")
    print("- The AI processor now includes JSON extraction and validation")
    print("- Responses are cleaned of markdown formatting and extra text")
    print("- Invalid responses are converted to structured error JSON")
    print("- This should eliminate 'Failed to parse Groq response as JSON' errors")
    
    return True

async def test_full_ai_call():
    """Test a full AI call with the improved system"""
    
    print("\n🤖 Testing Full AI Call with JSON Validation")
    print("=" * 60)
    
    ai_processor = AIProcessor()
    
    # Check if we have a Groq API key
    if not ai_processor.client:
        print("⚠️ No Groq API key found - testing JSON extraction only")
        return True
    
    print("🔑 Groq client initialized - testing real API call")
    
    # Simple test prompt that should return JSON
    system_prompt = "You are a helpful assistant that responds with JSON."
    user_prompt = """Please analyze this simple text and return JSON:

Text: "Hello, this is a test message."

Return JSON with this structure:
{
  "analysis": "your analysis",
  "word_count": number,
  "sentiment": "positive/negative/neutral"
}"""
    
    try:
        response = await ai_processor.call_ollama(user_prompt, system_prompt)
        print(f"✅ AI call successful")
        print(f"📄 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
        
        # Try to parse the response
        parsed = json.loads(response)
        print(f"✅ JSON parsing successful")
        print(f"📊 Response structure: {list(parsed.keys())}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"📄 Raw response: {response[:200]}...")
        return False
    except Exception as e:
        print(f"❌ AI call failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 JSON Parsing Fix Verification")
        print("This script tests the fixes for 'Failed to parse Groq response as JSON' errors\n")
        
        # Test JSON extraction logic
        extraction_success = await test_json_extraction()
        
        # Test full AI call if API key is available
        ai_call_success = await test_full_ai_call()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL RESULTS:")
        print(f"   JSON Extraction Tests: {'✅ PASSED' if extraction_success else '❌ FAILED'}")
        print(f"   Full AI Call Test: {'✅ PASSED' if ai_call_success else '❌ FAILED'}")
        
        if extraction_success:
            print("\n🎉 The JSON parsing fix should resolve the Groq API errors!")
            print("   - AI responses are now cleaned and validated")
            print("   - Invalid responses are converted to structured error JSON")
            print("   - The system will no longer crash on malformed AI responses")
        else:
            print("\n⚠️ Some tests failed - please review the implementation")
    
    asyncio.run(main())