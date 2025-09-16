#!/usr/bin/env python3
"""
Test script with a more realistic meeting transcript
"""

import requests
import json

def test_realistic_meeting():
    """Test with a realistic meeting transcript"""
    
    # More realistic meeting transcript
    realistic_transcript = """
    John: Good morning everyone, thanks for joining today's quarterly review meeting. 
    
    Sarah: Morning John. I have the Q3 numbers ready to present.
    
    John: Perfect. Let's start with Sarah presenting the quarterly results, then we'll discuss the action items for Q4.
    
    Sarah: So our Q3 revenue was $2.3 million, which is 15% above our target. The main drivers were the new product launch and increased customer retention. However, we did see some challenges in the European market.
    
    Mike: That's great news on the revenue! What specific challenges are we seeing in Europe?
    
    Sarah: Mainly regulatory compliance issues and slower adoption rates. I think we need to assign someone to focus specifically on the European market strategy.
    
    John: Good point. Mike, can you take ownership of the European market analysis? We need a comprehensive report by October 15th.
    
    Mike: Absolutely, I'll get started on that immediately. I'll need to coordinate with our legal team for the compliance aspects.
    
    Sarah: Also, for Q4, we should prioritize the mobile app development. Our customer surveys show 78% want mobile access.
    
    John: Agreed. Sarah, can you work with the development team to create a mobile app roadmap? Target completion by end of November.
    
    Sarah: Will do. I'll schedule meetings with the dev team next week.
    
    Mike: One more thing - we should also review our pricing strategy. Competitors have been aggressive lately.
    
    John: Good catch. Let's schedule a separate pricing strategy meeting for next Friday. Mike, can you prepare a competitive analysis beforehand?
    
    Mike: Sure thing, I'll have that ready.
    
    John: Excellent. So to summarize: Mike handles European analysis by Oct 15, Sarah leads mobile app roadmap by November, and we meet next Friday for pricing strategy. Any questions?
    
    Sarah: No questions from me. This was very productive.
    
    Mike: All clear. Thanks everyone.
    
    John: Great meeting everyone. Talk to you all next week.
    """
    
    test_data = {
        "text": realistic_transcript.strip(),
        "meeting_id": "quarterly-review-q3-2024",
        "model": "llama3-8b-8192",
        "model_name": "Llama 3 8B"
    }
    
    url = "http://localhost:5167/process-complete-meeting"
    headers = {"Content-Type": "application/json"}
    
    print("🧪 Testing with realistic meeting transcript...")
    print(f"📡 URL: {url}")
    print(f"📝 Transcript length: {len(realistic_transcript)} characters")
    
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=60)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
            result = response.json()
            
            # Pretty print key sections
            print("\n🎯 PROCESSING RESULTS:")
            print("=" * 50)
            
            # Executive Summary
            if "processing_results" in result and "summary" in result["processing_results"]:
                summary = result["processing_results"]["summary"]
                if "executive_summary" in summary:
                    exec_summary = summary["executive_summary"]
                    print(f"📋 Executive Summary:")
                    print(f"   Overview: {exec_summary.get('overview', 'N/A')[:200]}...")
                    print(f"   Business Impact: {exec_summary.get('business_impact', 'N/A')}")
                    print(f"   Urgency: {exec_summary.get('urgency_level', 'N/A')}")
            
            # Tasks
            if "processing_results" in result and "tasks" in result["processing_results"]:
                tasks = result["processing_results"]["tasks"]
                if "tasks" in tasks and tasks["tasks"]:
                    print(f"\n📋 Extracted Tasks ({len(tasks['tasks'])}):")
                    for i, task in enumerate(tasks["tasks"][:3], 1):  # Show first 3
                        print(f"   {i}. {task.get('title', 'N/A')}")
                        print(f"      Assignee: {task.get('assignee', 'N/A')}")
                        print(f"      Due: {task.get('due_date', 'N/A')}")
                else:
                    print(f"\n📋 Tasks: None extracted")
            
            # Speakers
            if "processing_results" in result and "speakers" in result["processing_results"]:
                speakers = result["processing_results"]["speakers"]
                if "speakers" in speakers:
                    print(f"\n👥 Speakers ({speakers.get('total_speakers', 0)}):")
                    for speaker in speakers["speakers"][:3]:  # Show first 3
                        print(f"   - {speaker.get('name', 'Unknown')}")
            
            # Integration Results
            if "integration_results" in result:
                integration = result["integration_results"]
                print(f"\n🔗 Integration: {integration.get('tasks_created', 0)} tasks created")
            
            print(f"\n📊 Metadata:")
            if "metadata" in result:
                metadata = result["metadata"]
                print(f"   Model: {metadata.get('ai_model', 'N/A')}")
                print(f"   Transcript Length: {metadata.get('transcript_length', 'N/A')} chars")
                print(f"   Processed At: {metadata.get('processed_at', 'N/A')}")
            
        else:
            print("❌ Error!")
            print(f"📋 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_realistic_meeting()