import pytest
import asyncio
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the integration module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables for testing
env_file = Path(__file__).parent.parent / ".env.integration"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Try parent directory
    env_file_parent = Path(__file__).parent.parent.parent / ".env.integration"
    if env_file_parent.exists():
        load_dotenv(env_file_parent)
    else:
        # Fallback to regular .env
        load_dotenv()

# Configure pytest for async tests
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config():
    """Test configuration from environment variables"""
    return {
        # Notion config
        "notion_token": os.getenv("NOTION_TOKEN"),
        "notion_database_id": os.getenv("NOTION_DATABASE_ID"),

        # ClickUp config
        "clickup_token": os.getenv("CLICKUP_TOKEN"),
        "clickup_list_id": os.getenv("CLICKUP_LIST_ID"),
        "clickup_team_id": os.getenv("CLICKUP_TEAM_ID"),

        # Testing config
        "use_mock": os.getenv("USE_MOCK_INTEGRATIONS", "false").lower() == "true",
        "test_prefix": os.getenv("TEST_TASK_PREFIX", "[ScrumBot Test]"),
        "cleanup_enabled": os.getenv("TEST_CLEANUP_ENABLED", "true").lower() == "true",
        "api_timeout": int(os.getenv("API_TIMEOUT", "30")),
        "max_retries": int(os.getenv("MAX_RETRIES", "3"))
    }

@pytest.fixture
def notion_integration(test_config):
    """Create NotionIntegration instance for testing"""
    from app.integrations import NotionIntegration

    if not test_config["notion_token"] and not test_config["use_mock"]:
        pytest.skip("NOTION_TOKEN not provided and not in mock mode")

    return NotionIntegration(
        token=test_config["notion_token"],
        database_id=test_config["notion_database_id"]
    )

@pytest.fixture
def clickup_integration(test_config):
    """Create ClickUpIntegration instance for testing"""
    from app.integrations import ClickUpIntegration

    if not test_config["clickup_token"] and not test_config["use_mock"]:
        pytest.skip("CLICKUP_TOKEN not provided and not in mock mode")

    return ClickUpIntegration(
        token=test_config["clickup_token"],
        list_id=test_config["clickup_list_id"],
        team_id=test_config["clickup_team_id"]
    )

@pytest.fixture
def sample_task_data(test_config):
    """Sample task data for testing"""
    return {
        "title": f"{test_config['test_prefix']} Integration Test Task",
        "description": "This is a test task created during integration testing. It should be safe to delete.",
        "priority": "medium",
        "due_date": "2025-01-20",
        "meeting_id": "test_meeting_001",
        "meeting_title": "Integration Test Meeting"
    }

@pytest.fixture
def sample_meeting_data(test_config):
    """Sample meeting data for testing"""
    return {
        "meeting_id": "test_meeting_001",
        "meeting_title": f"{test_config['test_prefix']} Sprint Planning",
        "participants": [
            {"name": "Test User 1", "email": "test1@example.com"},
            {"name": "Test User 2", "email": "test2@example.com"}
        ],
        "tasks": [
            {
                "title": f"{test_config['test_prefix']} Review API documentation",
                "description": "Go through the new API endpoints and update integration tests",
                "priority": "high",
                "assignee": "ScrumAi",
                "due_date": "2025-01-15"
            },
            {
                "title": f"{test_config['test_prefix']} Update UI components",
                "description": "Modify the dashboard to show integration status",
                "priority": "medium",
                "assignee": "ScrumAi",
                "due_date": "2025-01-17"
            }
        ]
    }

@pytest.fixture
def invalid_task_data():
    """Invalid task data for error testing"""
    return [
        {"description": "No title test"},  # Missing title
        {"title": "", "description": "Empty title"},  # Empty title
        {"title": "x" * 3000, "description": "Title too long"},  # Exceeds limits
        {"title": "Valid title", "priority": "invalid_priority"},  # Invalid priority
        {"title": "Valid title", "due_date": "invalid-date-format"},  # Invalid date
    ]

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests"""
    import logging

    # Set up basic logging
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Reduce noise from HTTP libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

@pytest.fixture
def cleanup_tasks():
    """Track created tasks for cleanup"""
    created_tasks = []

    def add_task(platform, task_id, task_data=None):
        created_tasks.append({
            "platform": platform,
            "task_id": task_id,
            "task_data": task_data
        })

    yield add_task

    # Cleanup logic would go here
    # For now, just log the tasks that were created
    if created_tasks:
        print(f"\n📋 Created {len(created_tasks)} test tasks:")
        for task in created_tasks:
            print(f"  - {task['platform']}: {task['task_id']}")
        print("🧹 Please manually clean up test tasks if needed")

# Skip all tests if no credentials provided and not in mock mode
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real APIs"
    )
    config.addinivalue_line(
        "markers", "notion: mark test as requiring Notion API access"
    )
    config.addinivalue_line(
        "markers", "clickup: mark test as requiring ClickUp API access"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_runtest_setup(item):
    """Skip tests based on available configuration"""
    use_mock = os.getenv("USE_MOCK_INTEGRATIONS", "false").lower() == "true"

    if item.get_closest_marker("notion"):
        if not os.getenv("NOTION_TOKEN") and not use_mock:
            pytest.skip("NOTION_TOKEN not provided and not in mock mode")

    if item.get_closest_marker("clickup"):
        if not os.getenv("CLICKUP_TOKEN") and not use_mock:
            pytest.skip("CLICKUP_TOKEN not provided and not in mock mode")
