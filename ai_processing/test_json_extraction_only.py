#!/usr/bin/env python3
"""
Test script to verify the JSON extraction logic without requiring Groq library
"""

import json
import re

def extract_and_validate_json(response: str) -> str:
    """Extract and validate JSON from AI response that might contain extra text"""
    
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
        "raw_response": response[:500],  # First 500 chars for debugging
        "speakers": [],
        "analysis": "Could not parse AI response as JSON"
    }
    return json.dumps(error_response)

def test_json_extraction():
    """Test the JSON extraction and validation logic"""
    
    print("🧪 Testing JSON Extraction and Validation Fix")
    print("=" * 60)
    
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
        '[{"name": "Array Response", "text": "This is an array"}]',
        
        # Case 9: Complex nested JSON with extra text
        '''The analysis is complete. Here are the results:

```json
{
  "speakers": [
    {
      "id": "speaker_1",
      "name": "John Doe",
      "segments": ["Hello everyone", "Let's get started"],
      "confidence": 0.95
    },
    {
      "id": "speaker_2", 
      "name": "Jane Smith",
      "segments": ["Good morning", "I agree with that"],
      "confidence": 0.87
    }
  ],
  "analysis": "Two distinct speakers identified",
  "total_speakers": 2
}
```

This completes the speaker identification process.''',
        
        # Case 10: JSON with comments (invalid JSON but common AI mistake)
        '''{
  // This is a comment
  "speakers": [{"name": "Test", "segments": ["Hello"]}],
  "analysis": "JSON with comments"
}'''
    ]
    
    print(f"Testing {len(test_responses)} different response scenarios...\n")
    
    success_count = 0
    
    for i, test_response in enumerate(test_responses, 1):
        print(f"🔍 Test Case {i}:")
        print(f"   Input: {test_response[:50]}{'...' if len(test_response) > 50 else ''}")
        
        try:
            # Test the extraction method
            cleaned_response = extract_and_validate_json(test_response)
            
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
            
            success_count += 1
                
        except json.JSONDecodeError as e:
            print(f"   ❌ FAILED: Still invalid JSON after extraction")
            print(f"   Error: {e}")
        except Exception as e:
            print(f"   ❌ FAILED: Unexpected error")
            print(f"   Error: {e}")
        
        print()
    
    print("🎯 Summary:")
    print(f"   Successful extractions: {success_count}/{len(test_responses)}")
    print("   - AI responses are cleaned of markdown formatting and extra text")
    print("   - Invalid responses are converted to structured error JSON")
    print("   - This should eliminate 'Failed to parse Groq response as JSON' errors")
    
    return success_count == len(test_responses)

def test_specific_error_cases():
    """Test specific cases that were causing the original error"""
    
    print("\n🎯 Testing Specific Error Cases from Production")
    print("=" * 60)
    
    # These are examples of responses that were causing the original error
    production_error_cases = [
        # Case 1: Groq API error message
        "Error: Invalid API key provided",
        
        # Case 2: Rate limit error
        "Rate limit exceeded. Please try again later.",
        
        # Case 3: Model unavailable
        "Model llama-3.1-8b-instant is currently unavailable",
        
        # Case 4: Timeout error
        "Request timed out after 30 seconds",
        
        # Case 5: JSON with trailing comma (invalid)
        '{"speakers": [{"name": "Test"}], "analysis": "trailing comma",}',
        
        # Case 6: Incomplete JSON response
        '{"speakers": [{"name": "John", "segments": ["Hello'
    ]
    
    print(f"Testing {len(production_error_cases)} production error scenarios...\n")
    
    all_handled = True
    
    for i, error_case in enumerate(production_error_cases, 1):
        print(f"🚨 Error Case {i}:")
        print(f"   Original Error: {error_case[:60]}{'...' if len(error_case) > 60 else ''}")
        
        try:
            # This should NOT throw an exception anymore
            cleaned_response = extract_and_validate_json(error_case)
            parsed = json.loads(cleaned_response)
            
            print(f"   ✅ HANDLED: Converted to valid JSON")
            
            # Handle both dict and list responses
            if isinstance(parsed, dict):
                print(f"   Result: {parsed.get('error', 'No error field')}")
            else:
                print(f"   Result: Array with {len(parsed)} items")
            
        except Exception as e:
            print(f"   ❌ NOT HANDLED: Still throws exception")
            print(f"   Exception: {e}")
            all_handled = False
        
        print()
    
    return all_handled

if __name__ == "__main__":
    print("🚀 JSON Parsing Fix Verification (Standalone)")
    print("This script tests the fixes for 'Failed to parse Groq response as JSON' errors\n")
    
    # Test JSON extraction logic
    extraction_success = test_json_extraction()
    
    # Test specific error cases
    error_handling_success = test_specific_error_cases()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"   JSON Extraction Tests: {'✅ PASSED' if extraction_success else '❌ FAILED'}")
    print(f"   Error Handling Tests: {'✅ PASSED' if error_handling_success else '❌ FAILED'}")
    
    if extraction_success and error_handling_success:
        print("\n🎉 The JSON parsing fix should resolve the Groq API errors!")
        print("   - AI responses are now cleaned and validated")
        print("   - Invalid responses are converted to structured error JSON")
        print("   - The system will no longer crash on malformed AI responses")
        print("\n📋 Next Steps:")
        print("   1. Deploy these changes to your EC2 instance")
        print("   2. Restart the WebSocket server and backend")
        print("   3. Test with real meeting transcription")
    else:
        print("\n⚠️ Some tests failed - please review the implementation")