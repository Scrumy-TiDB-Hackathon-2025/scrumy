#!/usr/bin/env python3
"""
Test the full pipeline with a meeting transcript that contains actual tasks
"""

import requests
import json

BASE_URL = "http://localhost:5167"

def test_pipeline_with_meeting_tasks():
    """Test pipeline with a realistic meeting transcript containing tasks"""
    
    print("🎯 Testing Pipeline with Task-Rich Meeting")
    print("=" * 50)
    
    # Sample meeting transcript with clear action items
    meeting_transcript = """
    Sarah: Good morning everyone. Let's review our project status. 
    
    John: The database migration is 80% complete. I'll finish it by Friday and send the completion report to the team.
    
    Sarah: Great. Lisa, can you handle the user interface testing once John's done?
    
    Lisa: Absolutely. I'll start the UI testing on Monday and aim to complete it by Wednesday. I'll also need to coordinate with the QA team.
    
    Mike: I'll prepare the deployment scripts this week. Sarah, can you review them before we go live?
    
    Sarah: Sure, I'll review the deployment scripts by Thursday. Also, we need someone to update the documentation.
    
    Lisa: I can take care of the documentation update after the UI testing is done.
    
    John: Don't forget we need to schedule the client demo. Who's handling that?
    
    Sarah: I'll reach out to the client today to schedule the demo for next week. Mike, can you prepare the demo environment?
    
    Mike: Yes, I'll set up the demo environment by Friday.
    
    Sarah: Perfect. Let's also make sure we backup the current system before deployment. John, can you handle that?
    
    John: Will do. I'll create the system backup on Thursday night.
    """
    
    try:
        # Step 1: Test AI Processing
        print("\n🤖 Step 1: AI Processing...")
        
        meeting_data = {
            "text": meeting_transcript,
            "model": "groq",
            "model_name": "llama-3.1-70b-versatile",
            "meeting_id": "task-rich-meeting-001"
        }
        
        response = requests.post(f"{BASE_URL}/process-complete-meeting", json=meeting_data, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ AI processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        processing_result = response.json()
        print(f"✅ AI Processing successful!")
        
        # Step 2: Extract tasks specifically
        print("\n📋 Step 2: Task Extraction...")
        
        task_data = {"transcript": meeting_transcript}
        response = requests.post(f"{BASE_URL}/extract-tasks", json=task_data, timeout=90)
        
        if response.status_code != 200:
            print(f"❌ Task extraction failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        task_result = response.json()
        tasks = task_result.get('tasks', [])
        
        print(f"✅ Task extraction successful!")
        print(f"📝 Tasks extracted: {len(tasks)}")
        
        # Display results
        print("\n" + "=" * 50)
        print("🎉 PIPELINE RESULTS")
        print("=" * 50)
        
        print(f"\n📄 MEETING TRANSCRIPT:")
        print(f"{meeting_transcript[:300]}...")
        
        print(f"\n📋 EXTRACTED TASKS:")
        for i, task in enumerate(tasks, 1):
            print(f"\n{i}. {task.get('title', 'Untitled Task')}")
            print(f"   👤 Assignee: {task.get('assignee', 'Unassigned')}")
            print(f"   📅 Due Date: {task.get('due_date', 'No deadline')}")
            print(f"   🔥 Priority: {task.get('priority', 'medium')}")
            print(f"   📝 Description: {task.get('description', 'No description')}")
        
        # Performance metrics
        print(f"\n⚡ PERFORMANCE:")
        print(f"Transcript length: {len(meeting_transcript)} characters")
        print(f"Tasks extracted: {len(tasks)}")
        print(f"Task extraction metadata: {task_result.get('extraction_metadata', {})}")
        
        # Validate we found some tasks
        if len(tasks) == 0:
            print("\n⚠️  WARNING: No tasks were extracted from a meeting that clearly contains action items!")
            return False
        
        print(f"\n✅ SUCCESS: Found {len(tasks)} tasks in the meeting!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🚀 Pipeline Test with Task-Rich Meeting")
    print("=" * 50)
    
    # Check backend status
    if not check_backend_status():
        print("❌ Backend not running! Please start with:")
        print("   ./clean_start_backend.sh")
        exit(1)
    
    print("✅ Backend is running")
    
    # Run the test
    success = test_pipeline_with_meeting_tasks()
    
    if success:
        print("\n🎉 Task-rich pipeline test completed successfully!")
    else:
        print("\n❌ Pipeline test failed!")
        exit(1)