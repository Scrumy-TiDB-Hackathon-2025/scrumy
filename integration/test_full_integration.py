#!/usr/bin/env python3
"""
Comprehensive Integration Test
Tests both Notion and ClickUp integrations working together with environment variables
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the app directory to the path
current_dir = Path(__file__).parent
app_dir = current_dir / 'app'
sys.path.insert(0, str(app_dir))

# Load environment variables
env_file = current_dir / '.env.integration'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment from: {env_file}")
else:
    print("⚠️  No .env.integration file found, using system environment")

class IntegrationTester:
    def __init__(self):
        self.test_results = {}
        self.created_tasks = []

    async def verify_environment(self):
        """Verify all required environment variables are set"""
        print("\n🔧 Environment Variables Check")
        print("=" * 50)

        required_vars = {
            'NOTION_TOKEN': 'Notion API token',
            'NOTION_DATABASE_ID': 'Notion database ID',
            'CLICKUP_TOKEN': 'ClickUp API token',
            'CLICKUP_TEAM_ID': 'ClickUp team ID',
            'CLICKUP_LIST_ID': 'ClickUp list ID'
        }

        missing_vars = []

        for var, description in required_vars.items():
            value = os.getenv(var)
            if value and value not in ['your_token_here', 'your_id_here', 'pk_your_token_here']:
                # Show partial value for security
                if 'TOKEN' in var:
                    display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                else:
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print(f"   ✅ {var}: {display_value}")
            else:
                missing_vars.append(var)
                print(f"   ❌ {var}: Not set or placeholder value")

        if missing_vars:
            print(f"\n❌ Missing variables: {missing_vars}")
            return False

        print("\n✅ All required environment variables are set")
        return True

    async def test_notion_integration(self):
        """Test Notion integration functionality"""
        print("\n📝 Notion Integration Test")
        print("=" * 50)

        try:
            from integrations import NotionIntegration

            notion = NotionIntegration()

            if notion.is_mock:
                print("   ⚠️  Notion is in mock mode")
                return False

            # Test task creation
            test_task = {
                "title": "[Integration Test] Notion Task Test",
                "description": "Testing Notion integration with environment variables",
                "priority": "high",
                "assignee": "ScrumAi"
            }

            print("   Creating Notion test task...")
            result = await notion.create_task(test_task)

            if result.get("success"):
                print("   ✅ Notion task creation successful")
                print(f"   🔗 Task URL: {result.get('notion_url')}")
                self.created_tasks.append(('notion', result.get('notion_page_id')))
                return True
            else:
                print(f"   ❌ Notion task creation failed: {result.get('error')}")
                return False

        except Exception as e:
            print(f"   ❌ Notion integration test failed: {str(e)}")
            return False

    async def test_clickup_integration(self):
        """Test ClickUp integration functionality"""
        print("\n📋 ClickUp Integration Test")
        print("=" * 50)

        try:
            from integrations import ClickUpIntegration

            clickup = ClickUpIntegration()

            if clickup.is_mock:
                print("   ⚠️  ClickUp is in mock mode, testing mock functionality")

                # Test mock task creation
                test_task = {
                    "title": "[Integration Test] ClickUp Mock Task",
                    "description": "Testing ClickUp mock integration",
                    "priority": "normal"
                }

                result = await clickup.create_task(test_task)

                if result.get("success") and result.get("mock"):
                    print("   ✅ ClickUp mock task creation successful")
                    print(f"   🔗 Mock Task URL: {result.get('clickup_url')}")
                    return True
                else:
                    print(f"   ❌ ClickUp mock task creation failed: {result.get('error')}")
                    return False
            else:
                # Test real task creation
                test_task = {
                    "title": "[Integration Test] ClickUp Task Test",
                    "description": "Testing ClickUp integration with environment variables",
                    "priority": "normal"
                }

                print("   Creating ClickUp test task...")
                result = await clickup.create_task(test_task)

                if result.get("success"):
                    print("   ✅ ClickUp task creation successful")
                    print(f"   🔗 Task URL: {result.get('clickup_url')}")
                    self.created_tasks.append(('clickup', result.get('clickup_task_id')))
                    return True
                else:
                    print(f"   ❌ ClickUp task creation failed: {result.get('error')}")
                    return False

        except Exception as e:
            print(f"   ❌ ClickUp integration test failed: {str(e)}")
            return False

    async def test_integration_manager(self):
        """Test integration manager with both platforms"""
        print("\n🔄 Integration Manager Test")
        print("=" * 50)

        try:
            from integrations import integration_manager

            # Check loaded integrations
            integrations = list(integration_manager.integrations.keys())
            print(f"   Loaded integrations: {integrations}")

            required_integrations = ['notion', 'clickup']
            missing = [i for i in required_integrations if i not in integrations]

            if missing:
                print(f"   ❌ Missing integrations: {missing}")
                return False

            print("   ✅ Both Notion and ClickUp integrations loaded")

            # Test creating task across all platforms
            test_task = {
                "title": "[Integration Test] Multi-Platform Task",
                "description": "Testing task creation across all integrated platforms",
                "assignee": "ScrumAi",
                "priority": "medium"
            }

            print("   Creating task across all platforms...")
            result = await integration_manager.create_task_all(test_task)

            if result.get("success"):
                successful = result.get("successful_integrations", 0)
                total = result.get("total_integrations", 0)

                print(f"   ✅ Integration manager success: {successful}/{total} platforms")

                # Check individual results
                results = result.get('results', {})

                notion_result = results.get('notion', {})
                if notion_result.get('success'):
                    print(f"   📝 Notion: {notion_result.get('notion_url')}")
                    self.created_tasks.append(('notion', notion_result.get('notion_page_id')))

                clickup_result = results.get('clickup', {})
                if clickup_result.get('success'):
                    print(f"   📋 ClickUp: {clickup_result.get('clickup_url')}")
                    self.created_tasks.append(('clickup', clickup_result.get('clickup_task_id')))

                return successful >= 2  # At least Notion and ClickUp should work
            else:
                print(f"   ❌ Integration manager failed: {result.get('error')}")
                return False

        except Exception as e:
            print(f"   ❌ Integration manager test failed: {str(e)}")
            return False

    async def test_notion_tools(self):
        """Test Notion tools functionality"""
        print("\n🛠️  Notion Tools Test")
        print("=" * 50)

        try:
            from notion_tools import create_notion_task

            result = await create_notion_task(
                title="[Integration Test] Notion Tools Test",
                description="Testing notion_tools function with environment variables",
                priority="low",
                assignee="ScrumAi"
            )

            if result.get('task_created'):
                print("   ✅ Notion tools function successful")
                print(f"   🔗 Task URL: {result.get('notion_url')}")
                self.created_tasks.append(('notion', result.get('task_id')))
                return True
            else:
                print(f"   ❌ Notion tools function failed: {result.get('error')}")
                return False

        except Exception as e:
            print(f"   ❌ Notion tools test failed: {str(e)}")
            return False

    async def test_tools_registration(self):
        """Test that tools are properly registered"""
        print("\n📋 Tools Registration Test")
        print("=" * 50)

        try:
            from tools import tools

            available_tools = tools.list_tools()
            print(f"   Available tools: {available_tools}")

            expected_tools = ['create_notion_task', 'create_task_everywhere']
            found_tools = [tool for tool in expected_tools if tool in available_tools]

            print(f"   Found expected tools: {found_tools}")

            if len(found_tools) >= 1:  # At least one tool should be available
                print("   ✅ Tools properly registered")

                # Test schema generation
                schema = tools.get_tools_schema()
                if len(schema) > 0:
                    print(f"   ✅ Generated schema for {len(schema)} tools")
                    return True
                else:
                    print("   ❌ No tool schemas generated")
                    return False
            else:
                print("   ❌ Expected tools not found")
                return False

        except Exception as e:
            print(f"   ❌ Tools registration test failed: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Comprehensive Integration Test Suite")
        print("Testing Notion + ClickUp + Integration Manager")
        print("=" * 70)

        # Test sequence
        tests = [
            ("Environment Check", self.verify_environment()),
            ("Notion Integration", self.test_notion_integration()),
            ("ClickUp Integration", self.test_clickup_integration()),
            ("Integration Manager", self.test_integration_manager()),
            ("Notion Tools", self.test_notion_tools()),
            ("Tools Registration", self.test_tools_registration())
        ]

        results = []
        for test_name, test_coro in tests:
            try:
                print(f"\n⏳ Running: {test_name}")
                result = await test_coro
                results.append((test_name, result))
                self.test_results[test_name] = result

                # Stop early if environment check fails
                if test_name == "Environment Check" and not result:
                    print("❌ Environment check failed, stopping tests")
                    break

            except Exception as e:
                print(f"   💥 {test_name} crashed: {str(e)}")
                results.append((test_name, False))
                self.test_results[test_name] = False

        # Generate summary
        await self.print_summary(results)

        # Return overall success
        passed = sum(1 for _, result in results if result)
        return passed >= 4  # At least 4/6 tests should pass for success

    async def print_summary(self, results):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        print(f"Tests passed: {passed}/{total}")
        if total > 0:
            print(f"Success rate: {(passed/total)*100:.1f}%")

        print("\nDetailed Results:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")

        if self.created_tasks:
            print(f"\n📋 Created {len(self.created_tasks)} test tasks:")
            for platform, task_id in self.created_tasks:
                print(f"   {platform}: {task_id}")

        print("\n🎯 Integration Status:")
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
            print("✨ Both Notion and ClickUp integrations are fully functional")
            print("🚀 Ready for production use")
        elif passed >= 4:
            print("✅ Most tests passed - integrations are working")
            print("🔧 Minor issues may need attention")
        elif passed >= 2:
            print("⚠️  Partial success - some integrations working")
            print("🛠️  Review failed tests and configuration")
        else:
            print("❌ Major issues detected")
            print("🔧 Check environment variables and API access")

        print("\n💡 Next Steps:")
        if passed >= 4:
            print("• Integration is ready for use")
            print("• Test with your actual workflows")
            print("• Monitor task creation in both platforms")
        else:
            print("• Review environment variables setup")
            print("• Check API credentials are correct")
            print("• Verify platform access permissions")

        print("\n" + "=" * 70)

async def main():
    """Main test execution"""
    tester = IntegrationTester()

    try:
        success = await tester.run_all_tests()
        return success
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
