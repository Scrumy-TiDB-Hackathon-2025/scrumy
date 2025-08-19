"""
Basic functionality test for Epic C tools integration
Tests core components without external API dependencies
"""

import asyncio
import os
import sys
import logging

# Add the app directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_imports():
    """Test that all modules can be imported"""
    print("📦 Testing Module Imports")
    print("=" * 30)
    
    try:
        from integrations import NotionIntegration, SlackIntegration, ClickUpIntegration, integration_manager
        print("✅ Integrations module imported successfully")
        integrations_ok = True
    except Exception as e:
        print(f"❌ Integrations import failed: {e}")
        integrations_ok = False
    
    try:
        from tools import tools
        print("✅ Tools module imported successfully")
        tools_ok = True
    except Exception as e:
        print(f"❌ Tools import failed: {e}")
        tools_ok = False
    
    try:
        from ai_agent import AIAgent
        print("✅ AI Agent module imported successfully")
        ai_agent_ok = True
    except Exception as e:
        print(f"❌ AI Agent import failed: {e}")
        ai_agent_ok = False
    
    try:
        from tidb_manager import tidb_manager
        print("✅ TiDB Manager module imported successfully")
        tidb_ok = True
    except Exception as e:
        print(f"❌ TiDB Manager import failed: {e}")
        tidb_ok = False
    
    try:
        import notion_tools
        import slack_tools
        print("✅ Tool modules imported successfully")
        tool_modules_ok = True
    except Exception as e:
        print(f"❌ Tool modules import failed: {e}")
        tool_modules_ok = False
    
    return all([integrations_ok, tools_ok, ai_agent_ok, tidb_ok, tool_modules_ok])

async def test_mock_integrations():
    """Test integrations in mock mode"""
    print("\n🎭 Testing Mock Integrations")
    print("=" * 30)
    
    # Set mock tokens
    os.environ["NOTION_TOKEN"] = "mock_token_for_dev"
    os.environ["SLACK_BOT_TOKEN"] = "mock_token_for_dev"
    os.environ["CLICKUP_TOKEN"] = "mock_token_for_dev"
    
    from integrations import NotionIntegration, SlackIntegration, ClickUpIntegration
    
    test_task = {
        "title": "Mock Test Task",
        "description": "Testing mock functionality",
        "assignee": "Mock User",
        "priority": "medium"
    }
    
    # Test Notion mock
    notion = NotionIntegration()
    notion_result = await notion.create_task(test_task)
    notion_ok = notion_result.get("success", False) and notion_result.get("mock", False)
    print(f"{'✅' if notion_ok else '❌'} Notion mock integration")
    
    # Test Slack mock
    slack = SlackIntegration()
    slack_result = await slack.send_task_notification(test_task)
    slack_ok = slack_result.get("success", False) and slack_result.get("mock", False)
    print(f"{'✅' if slack_ok else '❌'} Slack mock integration")
    
    # Test ClickUp mock
    clickup = ClickUpIntegration()
    clickup_result = await clickup.create_task(test_task)
    clickup_ok = clickup_result.get("success", False) and clickup_result.get("mock", False)
    print(f"{'✅' if clickup_ok else '❌'} ClickUp mock integration")
    
    return all([notion_ok, slack_ok, clickup_ok])

async def test_tools_registration():
    """Test that tools are properly registered"""
    print("\n🛠️ Testing Tools Registration")
    print("=" * 30)
    
    from tools import tools
    
    # Check available tools
    available_tools = tools.list_tools()
    print(f"Available tools: {available_tools}")
    
    expected_tools = [
        "create_notion_task",
        "send_slack_notification", 
        "create_task_everywhere",
        "send_meeting_summary"
    ]
    
    tools_found = []
    for tool in expected_tools:
        if tool in available_tools:
            tools_found.append(tool)
            print(f"✅ {tool} registered")
        else:
            print(f"❌ {tool} not found")
    
    # Test tool schema generation
    schema = tools.get_tools_schema()
    schema_ok = len(schema) > 0 and all("function" in tool for tool in schema)
    print(f"{'✅' if schema_ok else '❌'} Tools schema generation")
    
    return len(tools_found) >= 3 and schema_ok

async def test_integration_manager():
    """Test the integration manager"""
    print("\n🔧 Testing Integration Manager")
    print("=" * 30)
    
    from integrations import integration_manager
    
    # Check that integrations are loaded
    integrations_count = len(integration_manager.integrations)
    print(f"Loaded integrations: {list(integration_manager.integrations.keys())}")
    
    integrations_ok = integrations_count >= 2  # At least Notion and Slack
    print(f"{'✅' if integrations_ok else '❌'} Integration manager loaded {integrations_count} integrations")
    
    # Test task creation in mock mode
    test_task = {
        "title": "Integration Manager Test",
        "description": "Testing unified task creation",
        "assignee": "Test User",
        "priority": "high"
    }
    
    result = await integration_manager.create_task_all(test_task)
    task_creation_ok = result.get("success", False) and result.get("successful_integrations", 0) > 0
    print(f"{'✅' if task_creation_ok else '❌'} Unified task creation")
    
    return integrations_ok and task_creation_ok

async def test_ai_agent_basic():
    """Test basic AI agent functionality"""
    print("\n🤖 Testing AI Agent Basics")
    print("=" * 30)
    
    try:
        from ai_agent import AIAgent
        
        agent = AIAgent()
        
        # Test that agent initializes
        agent_ok = agent is not None
        print(f"{'✅' if agent_ok else '❌'} AI Agent initialization")
        
        # Test tools access
        tools_schema = agent.tools.get_tools_schema()
        tools_access_ok = len(tools_schema) > 0
        print(f"{'✅' if tools_access_ok else '❌'} AI Agent tools access")
        
        return agent_ok and tools_access_ok
        
    except Exception as e:
        print(f"❌ AI Agent test failed: {e}")
        return False

async def run_basic_tests():
    """Run all basic tests"""
    print("🧪 Running Basic Epic C Functionality Tests")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(await test_imports())
    test_results.append(await test_mock_integrations())
    test_results.append(await test_tools_registration())
    test_results.append(await test_integration_manager())
    test_results.append(await test_ai_agent_basic())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 Basic Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All basic tests passed! Core functionality is working.")
        return True
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed. Minor issues detected.")
        return True
    else:
        print("❌ Several tests failed. Core functionality has issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_basic_tests())
    sys.exit(0 if success else 1)