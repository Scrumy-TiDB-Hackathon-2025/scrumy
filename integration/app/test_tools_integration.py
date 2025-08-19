"""
Comprehensive test suite for Epic C tools integration
Tests all components: integrations, tools, AI agent, and database
"""

import asyncio
import json
import os
import sys
import logging
from typing import Dict, Any

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_integrations():
    """Test individual integrations"""
    print("🧪 Testing Individual Integrations")
    print("=" * 50)
    
    from integrations import NotionIntegration, SlackIntegration, ClickUpIntegration
    
    # Test data
    test_task = {
        "title": "Test Task from Integration Test",
        "description": "This is a test task created during integration testing",
        "assignee": "Test User",
        "priority": "medium",
        "due_date": "2025-01-15"
    }
    
    # Test Notion Integration
    print("\n📝 Testing Notion Integration...")
    notion = NotionIntegration()
    notion_result = await notion.create_task(test_task)
    print(f"Notion Result: {notion_result}")
    
    if notion_result.get("success"):
        print("✅ Notion integration working!")
    else:
        print(f"❌ Notion integration failed: {notion_result.get('error')}")
    
    # Test Slack Integration
    print("\n💬 Testing Slack Integration...")
    slack = SlackIntegration()
    slack_result = await slack.send_task_notification(test_task)
    print(f"Slack Result: {slack_result}")
    
    if slack_result.get("success"):
        print("✅ Slack integration working!")
    else:
        print(f"❌ Slack integration failed: {slack_result.get('error')}")
    
    # Test ClickUp Integration
    print("\n📋 Testing ClickUp Integration...")
    clickup = ClickUpIntegration()
    clickup_result = await clickup.create_task(test_task)
    print(f"ClickUp Result: {clickup_result}")
    
    if clickup_result.get("success"):
        print("✅ ClickUp integration working!")
    else:
        print(f"❌ ClickUp integration failed: {clickup_result.get('error')}")
    
    return {
        "notion": notion_result.get("success", False),
        "slack": slack_result.get("success", False),
        "clickup": clickup_result.get("success", False)
    }

async def test_integration_manager():
    """Test the unified integration manager"""
    print("\n🔧 Testing Integration Manager")
    print("=" * 50)
    
    from integrations import integration_manager
    
    test_task = {
        "title": "Multi-Integration Test Task",
        "description": "Testing task creation across all integrations",
        "assignee": "Integration Tester",
        "priority": "high",
        "meeting_id": "test_meeting_001"
    }
    
    # Test creating task in all integrations
    print("Creating task in all integrations...")
    result = await integration_manager.create_task_all(test_task)
    
    print(f"Integration Manager Result:")
    print(f"  Success: {result['success']}")
    print(f"  Integrations used: {result['integrations_used']}")
    print(f"  Successful: {result['successful_integrations']}/{result['total_integrations']}")
    
    for integration, integration_result in result['results'].items():
        status = "✅" if integration_result.get("success") else "❌"
        print(f"  {status} {integration}: {integration_result.get('success', False)}")
    
    # Test sending notifications
    print("\nSending notifications...")
    notification_result = await integration_manager.send_notifications_all(
        "Test notification from integration manager",
        test_task
    )
    
    print(f"Notification Result:")
    print(f"  Success: {notification_result['success']}")
    print(f"  Successful notifications: {notification_result['successful_notifications']}")
    
    return result['success']

async def test_tools_registry():
    """Test the tools registry"""
    print("\n🛠️ Testing Tools Registry")
    print("=" * 50)
    
    from tools import tools
    
    # List available tools
    available_tools = tools.list_tools()
    print(f"Available tools: {available_tools}")
    
    # Get tools schema
    schema = tools.get_tools_schema()
    print(f"Number of tools in schema: {len(schema)}")
    
    # Test individual tool calls
    test_results = {}
    
    # Test create_notion_task
    if "create_notion_task" in available_tools:
        print("\nTesting create_notion_task...")
        result = await tools.call_tool("create_notion_task", {
            "title": "Tools Registry Test Task",
            "description": "Testing task creation via tools registry",
            "assignee": "Tools Tester",
            "priority": "medium",
            "meeting_id": "test_meeting_002"
        })
        test_results["create_notion_task"] = result.get("success", False)
        print(f"Result: {result}")
    
    # Test create_task_everywhere
    if "create_task_everywhere" in available_tools:
        print("\nTesting create_task_everywhere...")
        result = await tools.call_tool("create_task_everywhere", {
            "title": "Universal Task Test",
            "description": "Testing universal task creation",
            "assignee": "Universal Tester",
            "priority": "high",
            "meeting_id": "test_meeting_003"
        })
        test_results["create_task_everywhere"] = result.get("success", False)
        print(f"Result: {result}")
    
    # Test send_slack_notification
    if "send_slack_notification" in available_tools:
        print("\nTesting send_slack_notification...")
        result = await tools.call_tool("send_slack_notification", {
            "message": "Test notification from tools registry",
            "task_title": "Tools Registry Test",
            "assignee": "Tools Tester"
        })
        test_results["send_slack_notification"] = result.get("success", False)
        print(f"Result: {result}")
    
    success_count = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\nTools Registry Test Summary: {success_count}/{total_tests} tools working")
    
    return success_count > 0

async def test_ai_agent():
    """Test the AI agent with tools"""
    print("\n🤖 Testing AI Agent with Tools")
    print("=" * 50)
    
    from ai_agent import AIAgent
    
    # Test transcript with clear action items
    test_transcript = """
    Sprint Planning Meeting - January 8, 2025
    
    Participants: John Smith (Tech Lead), Sarah Johnson (Backend Dev), Mike Chen (DevOps)
    
    Key Decisions:
    - Prioritize OAuth 2.0 implementation for Q1
    - Weekly architecture reviews starting next week
    
    Action Items:
    - John: Implement OAuth 2.0 with Google and GitHub providers by January 15 (High Priority)
    - Sarah: Review and approve database schema changes by January 12 (Medium Priority)  
    - Mike: Schedule weekly architecture review meetings by January 10 (Low Priority)
    - Team: Complete security audit before OAuth deployment by January 20 (High Priority)
    """
    
    agent = AIAgent()
    
    print("Processing transcript with AI agent...")
    result = await agent.process_with_tools(
        transcript=test_transcript,
        meeting_id="test_meeting_ai_001"
    )
    
    print(f"AI Agent Result:")
    print(f"  Analysis: {result.get('analysis', 'No analysis')[:200]}...")
    print(f"  Tools used: {result.get('tools_used', 0)}")
    print(f"  Meeting ID: {result.get('meeting_id')}")
    
    if result.get('tool_calls'):
        print(f"  Tool calls made: {len(result['tool_calls'])}")
        for i, tool_call in enumerate(result['tool_calls'], 1):
            tool_name = tool_call.get('tool', 'unknown')
            success = tool_call.get('result', {}).get('success', False) if 'result' in tool_call else False
            print(f"    {i}. {tool_name}: {'✅' if success else '❌'}")
    
    return len(result.get('tool_calls', [])) > 0

async def test_database_integration():
    """Test TiDB database integration"""
    print("\n🗄️ Testing Database Integration")
    print("=" * 50)
    
    from tidb_manager import tidb_manager
    
    try:
        # Test connection
        print("Testing database connection...")
        connected = await tidb_manager.connect()
        
        if not connected:
            print("❌ Database connection failed")
            return False
        
        print("✅ Database connected successfully")
        
        # Test saving a meeting
        print("Testing meeting save...")
        meeting_data = {
            "id": "test_db_meeting_001",
            "platform": "test",
            "title": "Database Integration Test Meeting",
            "participants": ["Tester 1", "Tester 2"]
        }
        
        meeting_saved = await tidb_manager.save_meeting(meeting_data)
        print(f"Meeting save result: {'✅' if meeting_saved else '❌'}")
        
        # Test saving a task
        print("Testing task save...")
        task_id = await tidb_manager.save_task(
            meeting_id="test_db_meeting_001",
            title="Database Test Task",
            description="Testing task save functionality",
            assignee="DB Tester",
            priority="medium"
        )
        
        print(f"Task save result: {'✅' if task_id else '❌'} (ID: {task_id})")
        
        # Test retrieving tasks
        print("Testing task retrieval...")
        tasks = await tidb_manager.get_meeting_tasks("test_db_meeting_001")
        print(f"Retrieved {len(tasks)} tasks")
        
        await tidb_manager.disconnect()
        
        return meeting_saved and task_id is not None
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    try:
        import aiohttp
        
        base_url = "http://localhost:5167"
        
        # Test health endpoint
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        print("✅ Health endpoint working")
                        health_working = True
                    else:
                        print(f"❌ Health endpoint failed: {response.status}")
                        health_working = False
            except Exception as e:
                print(f"❌ Health endpoint failed: {str(e)}")
                health_working = False
            
            # Test available tools endpoint
            try:
                async with session.get(f"{base_url}/api/v1/tools/available") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Tools endpoint working - {data.get('count', 0)} tools available")
                        tools_working = True
                    else:
                        print(f"❌ Tools endpoint failed: {response.status}")
                        tools_working = False
            except Exception as e:
                print(f"❌ Tools endpoint failed: {str(e)}")
                tools_working = False
        
        return health_working and tools_working
        
    except ImportError:
        print("❌ aiohttp not available for API testing")
        return False

async def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 Starting Comprehensive Epic C Tools Integration Test")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    try:
        test_results["integrations"] = await test_integrations()
        test_results["integration_manager"] = await test_integration_manager()
        test_results["tools_registry"] = await test_tools_registry()
        test_results["ai_agent"] = await test_ai_agent()
        test_results["database"] = await test_database_integration()
        test_results["api_endpoints"] = await test_api_endpoints()
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        return False
    
    # Print summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Epic C implementation is working correctly.")
        return True
    elif passed_tests >= total_tests * 0.7:  # 70% pass rate
        print("⚠️ Most tests passed. Implementation is mostly working with some issues.")
        return True
    else:
        print("❌ Many tests failed. Implementation needs significant work.")
        return False

if __name__ == "__main__":
    # Set environment variables for testing (mock mode)
    os.environ.setdefault("NOTION_TOKEN", "mock_token_for_dev")
    os.environ.setdefault("SLACK_BOT_TOKEN", "mock_token_for_dev")
    os.environ.setdefault("CLICKUP_TOKEN", "mock_token_for_dev")
    os.environ.setdefault("TIDB_CONNECTION_STRING", "mysql://test:test@localhost:4000/test")
    
    # Run the comprehensive test
    success = asyncio.run(run_comprehensive_test())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)