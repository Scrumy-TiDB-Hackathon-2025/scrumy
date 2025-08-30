#!/usr/bin/env python3
"""
Debug task extraction to see if it's working correctly
"""

import requests
import json

BASE_URL = "http://localhost:5167"

def test_very_explicit_tasks():
    """Test with extremely explicit task statements"""
    
    print("🔍 DEBUGGING TASK EXTRACTION")
    print("=" * 50)
    
    # Very explicit task examples
    test_cases = [
        {
            "name": "Simple Assignment",
            "transcript": "John, please update the documentation by Friday."
        },
        {
            "name": "Multiple Clear Tasks", 
            "transcript": """
            Action items from today's meeting:
            1. Sarah will review the code by Wednesday
            2. Mike needs to deploy the staging server by Thursday  
            3. Lisa must complete the user testing by Friday
            4. John should update the documentation by Monday
            """
        },
        {
            "name": "Meeting with Explicit Actions",
            "transcript": """
            Sarah: John, can you handle the database migration?
            John: Yes, I'll complete the database migration by Friday.
            Sarah: Great. Lisa, please test the new features.
            Lisa: I'll test the new features and report back by Wednesday.
            Mike: I need to deploy the staging environment.
            Sarah: Mike, please deploy staging by Thursday.
            """
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Transcript: {test_case['transcript'][:100]}...")
        
        try:
            # Test task extraction
            task_data = {"transcript": test_case['transcript']}
            response = requests.post(f"{BASE_URL}/extract-tasks", json=task_data, timeout=60)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                tasks = result.get('tasks', [])
                metadata = result.get('extraction_metadata', {})
                
                print(f"✅ Response received")
                print(f"📊 Tasks found: {len(tasks)}")
                print(f"📊 Metadata: {metadata}")
                
                if tasks:
                    print(f"📋 EXTRACTED TASKS:")
                    for j, task in enumerate(tasks, 1):
                        print(f"  {j}. {task.get('title', 'No title')}")
                        print(f"     Assignee: {task.get('assignee', 'None')}")
                        print(f"     Due: {task.get('due_date', 'None')}")
                        print(f"     Source: {task.get('source', 'None')}")
                else:
                    print("❌ NO TASKS EXTRACTED!")
                    print("🔍 Full response:")
                    print(json.dumps(result, indent=2))
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True

def test_ai_processor_directly():
    """Test if the AI processor is working at all"""
    
    print(f"\n🤖 TESTING AI PROCESSOR DIRECTLY")
    print("=" * 50)
    
    # Test a simple summary generation to see if GROQ is working
    try:
        meeting_data = {
            "text": "John will update the documentation by Friday. Sarah will review the code.",
            "model": "groq", 
            "model_name": "llama-3.1-70b-versatile",
            "meeting_id": "debug-test-001"
        }
        
        print("Testing complete meeting processing...")
        response = requests.post(f"{BASE_URL}/process-complete-meeting", json=meeting_data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI processor is working")
            print(f"Response keys: {list(result.keys())}")
            
            # Check if any tasks were found in the complete processing
            if 'tasks' in result:
                tasks = result.get('tasks', [])
                print(f"Tasks from complete processing: {len(tasks)}")
                for task in tasks:
                    print(f"  - {task}")
        else:
            print(f"❌ AI processor failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ AI processor error: {e}")

def check_backend_logs():
    """Check recent backend logs for clues"""
    
    print(f"\n📄 CHECKING BACKEND LOGS")
    print("=" * 50)
    
    try:
        import subprocess
        result = subprocess.run(['tail', '-20', 'backend.log'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("Recent backend logs:")
            print(result.stdout)
        else:
            print("Could not read backend logs")
            
    except Exception as e:
        print(f"Error reading logs: {e}")

if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend not running!")
            exit(1)
    except:
        print("❌ Backend not accessible!")
        exit(1)
    
    print("✅ Backend is running")
    
    # Run debug tests
    test_very_explicit_tasks()
    test_ai_processor_directly() 
    check_backend_logs()
    
    print(f"\n🔍 DEBUGGING COMPLETE")
    print("If no tasks are being extracted, the issue might be:")
    print("1. AI model being too conservative")
    print("2. GROQ API rate limiting")
    print("3. Prompt engineering needs adjustment")
    print("4. Response parsing issues")