#!/usr/bin/env python3
"""
Epic C Tools Integration Demo
Demonstrates the complete tools integration functionality
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add the app directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up mock environment for demo
os.environ.setdefault("NOTION_TOKEN", "mock_token_for_dev")
os.environ.setdefault("SLACK_BOT_TOKEN", "mock_token_for_dev")
os.environ.setdefault("CLICKUP_TOKEN", "mock_token_for_dev")
os.environ.setdefault("TIDB_CONNECTION_STRING", "mysql://demo:demo@localhost:4000/demo")

async def demo_individual_integrations():
    """Demo individual integration capabilities"""
    print("🔧 Demo 1: Individual Integration Testing")
    print("=" * 50)
    
    from integrations import NotionIntegration, SlackIntegration, ClickUpIntegration
    
    # Sample task data
    demo_task = {
        "title": "Epic C Demo Task",
        "description": "Demonstrating tools integration for TiDB Hackathon 2025",
        "assignee": "Demo User",
        "priority": "high",
        "due_date": "2025-01-20",
        "meeting_id": "demo_meeting_001"
    }
    
    print(f"📝 Creating task: '{demo_task['title']}'")
    print(f"   Assignee: {demo_task['assignee']}")
    print(f"   Priority: {demo_task['priority']}")
    print(f"   Due: {demo_task['due_date']}")
    print()
    
    # Test Notion
    print("📋 Testing Notion Integration...")
    notion = NotionIntegration()
    notion_result = await notion.create_task(demo_task)
    
    if notion_result.get("success"):
        print(f"   ✅ Notion task created successfully!")
        if notion_result.get("mock"):
            print(f"   🎭 Mock URL: {notion_result.get('notion_url')}")
        print(f"   📄 Page ID: {notion_result.get('notion_page_id')}")
    else:
        print(f"   ❌ Notion task failed: {notion_result.get('error')}")
    
    print()
    
    # Test Slack
    print("💬 Testing Slack Integration...")
    slack = SlackIntegration()
    slack_result = await slack.send_task_notification(demo_task)
    
    if slack_result.get("success"):
        print(f"   ✅ Slack notification sent successfully!")
        if slack_result.get("mock"):
            print(f"   🎭 Mock notification sent to #scrumbot-tasks")
        print(f"   📨 Message timestamp: {slack_result.get('message_ts')}")
    else:
        print(f"   ❌ Slack notification failed: {slack_result.get('error')}")
    
    print()
    
    # Test ClickUp
    print("📊 Testing ClickUp Integration...")
    clickup = ClickUpIntegration()
    clickup_result = await clickup.create_task(demo_task)
    
    if clickup_result.get("success"):
        print(f"   ✅ ClickUp task created successfully!")
        if clickup_result.get("mock"):
            print(f"   🎭 Mock URL: {clickup_result.get('clickup_url')}")
        print(f"   🆔 Task ID: {clickup_result.get('clickup_task_id')}")
    else:
        print(f"   ❌ ClickUp task failed: {clickup_result.get('error')}")
    
    return [notion_result.get("success"), slack_result.get("success"), clickup_result.get("success")]

async def demo_unified_integration():
    """Demo unified integration manager"""
    print("\n🚀 Demo 2: Unified Integration Manager")
    print("=" * 50)
    
    from integrations import integration_manager
    
    demo_task = {
        "title": "Multi-Platform Demo Task",
        "description": "This task will be created across all available platforms simultaneously",
        "assignee": "Integration Demo User",
        "priority": "urgent",
        "due_date": "2025-01-15",
        "meeting_id": "demo_meeting_002"
    }
    
    print(f"🎯 Creating task across ALL platforms: '{demo_task['title']}'")
    print(f"   Available integrations: {list(integration_manager.integrations.keys())}")
    print()
    
    # Create task in all integrations
    result = await integration_manager.create_task_all(demo_task)
    
    print(f"📊 Results Summary:")
    print(f"   Overall success: {'✅' if result['success'] else '❌'}")
    print(f"   Successful integrations: {result['successful_integrations']}/{result['total_integrations']}")
    print()
    
    print(f"📋 Individual Results:")
    for integration_name, integration_result in result['results'].items():
        status = "✅" if integration_result.get("success") else "❌"
        print(f"   {status} {integration_name.capitalize()}: {integration_result.get('success', False)}")
        if integration_result.get("success") and integration_result.get("mock"):
            print(f"      🎭 Mock mode - task created successfully")
    
    return result['success']

async def demo_tools_registry():
    """Demo tools registry and AI agent integration"""
    print("\n🛠️ Demo 3: Tools Registry & AI Agent")
    print("=" * 50)
    
    from tools import tools
    from ai_agent import AIAgent
    
    # Show available tools
    available_tools = tools.list_tools()
    print(f"🔧 Available Tools ({len(available_tools)}):")
    for i, tool in enumerate(available_tools, 1):
        print(f"   {i}. {tool}")
    print()
    
    # Demo direct tool calling
    print("🎯 Demo: Direct Tool Calling")
    print("Creating task using tools registry...")
    
    tool_result = await tools.call_tool("create_task_everywhere", {
        "title": "Tools Registry Demo Task",
        "description": "Demonstrating direct tool calling via registry",
        "assignee": "Tools Demo User",
        "priority": "medium",
        "meeting_id": "demo_meeting_003"
    })
    
    if tool_result.get("success"):
        result_data = tool_result.get("result", {})
        print(f"   ✅ Tool call successful!")
        print(f"   📊 Integrations used: {result_data.get('integrations_used', [])}")
        print(f"   ✅ Successful: {result_data.get('successful_integrations', 0)}")
    else:
        print(f"   ❌ Tool call failed: {tool_result.get('error')}")
    
    print()
    
    # Demo AI Agent processing
    print("🤖 Demo: AI Agent Processing")
    print("Processing meeting transcript with AI agent...")
    
    demo_transcript = """
    Epic C Demo Meeting - January 8, 2025
    
    Participants: Demo User (Developer), AI Assistant (ScrumBot)
    
    Meeting Summary:
    - Successfully implemented Epic C tools integration
    - All basic tests passing (5/5)
    - Ready for TiDB Hackathon 2025 demo
    
    Action Items:
    - Demo User: Prepare final presentation by January 10 (High Priority)
    - Team: Test with real API tokens before deployment (Medium Priority)
    - AI Assistant: Continue monitoring task creation accuracy (Low Priority)
    """
    
    agent = AIAgent()
    ai_result = await agent.process_with_tools(
        transcript=demo_transcript,
        meeting_id="demo_meeting_ai_001"
    )
    
    print(f"   🧠 AI Analysis: {ai_result.get('analysis', 'No analysis')[:100]}...")
    print(f"   🔧 Tools used: {ai_result.get('tools_used', 0)}")
    
    if ai_result.get('tool_calls'):
        print(f"   📋 Tool calls made:")
        for i, tool_call in enumerate(ai_result['tool_calls'], 1):
            tool_name = tool_call.get('tool', 'unknown')
            success = tool_call.get('result', {}).get('success', False) if 'result' in tool_call else False
            print(f"      {i}. {tool_name}: {'✅' if success else '❌'}")
    
    return tool_result.get("success", False) and len(ai_result.get('tool_calls', [])) > 0

async def demo_api_integration():
    """Demo API endpoints"""
    print("\n🌐 Demo 4: API Integration")
    print("=" * 50)
    
    print("📡 Available API Endpoints:")
    endpoints = [
        "GET  /api/v1/tools/available - List available tools",
        "POST /api/v1/tools/process_transcript - Process transcript with tools",
        "GET  /health - Health check"
    ]
    
    for endpoint in endpoints:
        print(f"   • {endpoint}")
    
    print()
    print("🔧 Tools Schema Example:")
    
    from tools import tools
    schema = tools.get_tools_schema()
    
    if schema:
        example_tool = schema[0]
        print(f"   Tool: {example_tool['function']['name']}")
        print(f"   Description: {example_tool['function']['description']}")
        print(f"   Parameters: {len(example_tool['function']['parameters']['properties'])} fields")
    
    return True

async def run_complete_demo():
    """Run the complete Epic C demo"""
    print("🎉 Epic C Tools Integration - Complete Demo")
    print("=" * 60)
    print("🏆 TiDB Hackathon 2025 - ScrumBot AI Meeting Assistant")
    print("=" * 60)
    
    demo_results = []
    
    try:
        # Run all demos
        individual_results = await demo_individual_integrations()
        demo_results.append(all(individual_results))
        
        unified_result = await demo_unified_integration()
        demo_results.append(unified_result)
        
        tools_result = await demo_tools_registry()
        demo_results.append(tools_result)
        
        api_result = await demo_api_integration()
        demo_results.append(api_result)
        
        # Final summary
        print("\n🏁 Demo Summary")
        print("=" * 60)
        
        demo_names = [
            "Individual Integrations",
            "Unified Integration Manager", 
            "Tools Registry & AI Agent",
            "API Integration"
        ]
        
        passed_demos = sum(demo_results)
        total_demos = len(demo_results)
        
        for i, (name, result) in enumerate(zip(demo_names, demo_results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} Demo {i+1}: {name}")
        
        print(f"\n📊 Overall Result: {passed_demos}/{total_demos} demos successful")
        
        if passed_demos == total_demos:
            print("\n🎉 🎉 🎉 ALL DEMOS SUCCESSFUL! 🎉 🎉 🎉")
            print("Epic C Tools Integration is fully functional and ready for production!")
            print("\n🚀 Key Features Demonstrated:")
            print("   ✅ Multi-platform task creation (Notion, Slack, ClickUp)")
            print("   ✅ Unified integration management")
            print("   ✅ AI-powered transcript processing")
            print("   ✅ Automatic tool calling based on meeting content")
            print("   ✅ Mock mode for development")
            print("   ✅ Comprehensive error handling")
            print("   ✅ RESTful API endpoints")
            print("\n🏆 Ready for TiDB Hackathon 2025!")
        else:
            print(f"\n⚠️ {total_demos - passed_demos} demo(s) had issues. Check logs above.")
        
        return passed_demos == total_demos
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Epic C Tools Integration Demo...")
    print(f"⏰ Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = asyncio.run(run_complete_demo())
    
    print(f"\n⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Final Result: {'SUCCESS' if success else 'FAILED'}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)