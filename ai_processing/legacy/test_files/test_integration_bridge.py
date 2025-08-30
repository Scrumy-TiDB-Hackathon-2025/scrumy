"""
Test script for AI Processing Integration Bridge

This script tests the integration between AI processing and the integration system
without requiring the full AI processing pipeline.
"""

import asyncio
import sys
import os
from typing import Dict, List

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from integration_bridge import create_integration_bridge

async def test_integration_bridge():
    """Test the integration bridge with sample AI task data"""
    
    print("🚀 Testing AI Processing Integration Bridge")
    print("=" * 60)
    
    # Sample AI-extracted tasks (simulating what AI processing would generate)
    sample_ai_tasks = [
        {
            "title": "Follow up on budget discussion",
            "description": "Review Q1 budget allocations and prepare revised proposal based on meeting feedback",
            "assignee": "John Smith",
            "priority": "high"
            # Note: meeting_id and due_date excluded due to current database limitations
        },
        {
            "title": "Schedule team training session",
            "description": "Organize training on new project management tools discussed in meeting",
            "assignee": "Sarah Johnson", 
            "priority": "medium"
        },
        {
            "title": "Update project timeline",
            "description": "Revise project milestones based on resource availability discussion",
            "assignee": "Mike Chen",
            "priority": "urgent"
        }
    ]
    
    # Test configuration
    test_config = {
        "enabled": True,
        "platforms": ["notion", "slack", "clickup"],
        "mock_mode": False  # Set to True to test without real API calls
    }
    
    # Create integration bridge
    print("📋 Initializing integration bridge...")
    bridge = create_integration_bridge(test_config)
    
    if not bridge.enabled:
        print("❌ Integration bridge is disabled or not available")
        print("   Make sure the integration system is properly set up")
        return
    
    print(f"✅ Integration bridge initialized (enabled: {bridge.enabled})")
    print()
    
    # Test task creation
    print("🔧 Testing task creation from AI results...")
    print(f"   Processing {len(sample_ai_tasks)} sample tasks")
    print()
    
    meeting_context = {
        "meeting_id": "test_ai_integration_001",  # This won't be sent to integrations yet
        "meeting_title": "Weekly Team Sync",
        "platform": "zoom"
    }
    
    try:
        results = await bridge.create_tasks_from_ai_results(
            ai_tasks=sample_ai_tasks,
            meeting_context=meeting_context
        )
        
        print("📊 Integration Results:")
        print(f"   Integration enabled: {results['integration_enabled']}")
        print(f"   Tasks processed: {results['tasks_processed']}")
        print(f"   Tasks created: {results['tasks_created']}")
        print(f"   Successful integrations: {results['successful_integrations']}")
        print(f"   Failed integrations: {results['failed_integrations']}")
        
        if results.get('task_urls'):
            print("   Task URLs created:")
            for platform, urls in results['task_urls'].items():
                print(f"     {platform}: {len(urls)} tasks")
                for i, url in enumerate(urls[:2]):  # Show first 2 URLs
                    print(f"       - {url}")
        
        if results.get('errors'):
            print("   Errors encountered:")
            for error in results['errors']:
                print(f"     - {error}")
        
        print()
        
        # Test meeting summary notification
        print("📢 Testing meeting summary notification...")
        sample_summary = """
        Weekly team sync completed successfully. Key discussion points included:
        - Q1 budget review and resource allocation
        - New project management tool evaluation  
        - Timeline adjustments for current projects
        
        3 action items were identified and assigned to team members.
        """
        
        notification_result = await bridge.send_meeting_summary_notification(
            meeting_summary=sample_summary,
            tasks_created=results['tasks_created'],
            meeting_context=meeting_context
        )
        
        print(f"   Notification sent: {notification_result.get('notification_sent', False)}")
        if notification_result.get('error'):
            print(f"   Error: {notification_result['error']}")
        
        print()
        print("✅ Integration bridge test completed successfully!")
        
        return results
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_data_transformation():
    """Test the data transformation logic"""
    
    print("🔄 Testing Data Transformation")
    print("=" * 40)
    
    bridge = create_integration_bridge()
    
    # Test cases for data transformation
    test_cases = [
        {
            "name": "Complete task",
            "input": {
                "title": "Complete project proposal",
                "description": "Finalize the Q2 project proposal document",
                "assignee": "Alice Cooper",
                "priority": "high",
                "meeting_id": "meeting_123",  # Should be excluded
                "due_date": "2025-01-15"      # Should be excluded
            },
            "expected_fields": ["title", "description", "assignee", "priority"]
        },
        {
            "name": "Minimal task",
            "input": {
                "title": "Review documents"
            },
            "expected_fields": ["title", "description", "assignee", "priority"]
        },
        {
            "name": "Invalid priority",
            "input": {
                "title": "Test task",
                "priority": "super_urgent"  # Invalid, should default to medium
            },
            "expected_fields": ["title", "description", "assignee", "priority"]
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        try:
            result = bridge._transform_ai_task_to_integration_format(test_case["input"])
            
            # Check that expected fields are present
            for field in test_case["expected_fields"]:
                if field not in result:
                    print(f"   ❌ Missing field: {field}")
                else:
                    print(f"   ✅ {field}: {result[field]}")
            
            # Check that unsupported fields are excluded
            if "meeting_id" in result:
                print(f"   ❌ meeting_id should be excluded but found: {result['meeting_id']}")
            else:
                print(f"   ✅ meeting_id correctly excluded")
                
            if "due_date" in result:
                print(f"   ❌ due_date should be excluded but found: {result['due_date']}")
            else:
                print(f"   ✅ due_date correctly excluded")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Transformation failed: {e}")
            print()

if __name__ == "__main__":
    print("🤖 AI Processing Integration Bridge Test Suite")
    print("=" * 60)
    print()
    
    # Run tests
    asyncio.run(test_data_transformation())
    print()
    asyncio.run(test_integration_bridge())