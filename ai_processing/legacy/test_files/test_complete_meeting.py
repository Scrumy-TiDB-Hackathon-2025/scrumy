#!/usr/bin/env python3
"""
Test script for the complete meeting processing endpoint
"""

import requests
import json

def test_complete_meeting():
    """Test the process-complete-meeting endpoint"""
    
    # Test data that matches the TranscriptRequest schema
    test_data = {
        "text": "Hello everyone, welcome to today's meeting. Let's discuss the quarterly results and plan for next quarter.",
        "meeting_id": "test-meeting-001",
        "model": "gpt-3.5-turbo",
        "model_name": "GPT-3.5 Turbo"
    }
    
    url = "http://localhost:5167/process-complete-meeting"
    headers = {"Content-Type": "application/json"}
    
    print("🧪 Testing complete meeting processing...")
    print(f"📡 URL: {url}")
    print(f"📝 Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
            result = response.json()
            print(f"📋 Response: {json.dumps(result, indent=2)}")
        else:
            print("❌ Error!")
            print(f"📋 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_complete_meeting()