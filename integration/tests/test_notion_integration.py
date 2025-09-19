import pytest
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_notion_connection(notion_integration, test_config):
    """Test basic Notion API connection"""
    # Check if we're in mock mode
    if test_config["use_mock"]:
        assert notion_integration.is_mock
        pytest.skip("Running in mock mode - skipping real API test")

    # Verify we have required configuration
    assert notion_integration.token is not None, "NOTION_TOKEN is required"
    assert notion_integration.database_id is not None, "NOTION_DATABASE_ID is required"

    # Check that we're not in mock mode with real credentials
    assert not notion_integration.is_mock, "Should not be in mock mode with real token"

    logger.info(f"Testing Notion connection with database: {notion_integration.database_id}")


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_notion_create_basic_task(notion_integration, sample_task_data, test_config, cleanup_tasks):
    """Test creating a basic task in Notion"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    logger.info(f"Creating basic task: {sample_task_data['title']}")

    result = await notion_integration.create_task(sample_task_data)

    # Verify success
    assert result["success"] is True, f"Task creation failed: {result.get('error', 'Unknown error')}"
    assert "task_id" in result, "Result should contain task_id"
    assert "task_url" in result, "Result should contain task_url"

    # Log the created task
    logger.info(f"✅ Created Notion task: {result['task_id']}")
    logger.info(f"📝 Task URL: {result['task_url']}")

    # Track for cleanup
    cleanup_tasks("notion", result["task_id"], sample_task_data)


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_notion_create_task_with_all_fields(notion_integration, test_config, cleanup_tasks):
    """Test creating a task with all possible fields"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    # Create a comprehensive task with all fields
    comprehensive_task = {
        "title": f"{test_config['test_prefix']} Comprehensive Test Task",
        "description": "This is a comprehensive test task with all fields populated. It includes a longer description to test text handling, special characters like émojis 🚀, and various formatting.",
        "priority": "high",
        "due_date": "2025-01-25",
        "assignee": "Test User",
        "status": "In Progress",
        "meeting_id": "comprehensive_test_001",
        "meeting_title": "Comprehensive Feature Testing Meeting",
        "tags": ["testing", "comprehensive", "scrumbot"],
        "estimated_hours": 4
    }

    logger.info(f"Creating comprehensive task: {comprehensive_task['title']}")

    result = await notion_integration.create_task(comprehensive_task)

    # Verify success
    assert result["success"] is True, f"Comprehensive task creation failed: {result.get('error', 'Unknown error')}"
    assert "task_id" in result
    assert "task_url" in result

    logger.info(f"✅ Created comprehensive Notion task: {result['task_id']}")

    # Track for cleanup
    cleanup_tasks("notion", result["task_id"], comprehensive_task)


@pytest.mark.notion
@pytest.mark.asyncio
async def test_notion_task_validation(notion_integration):
    """Test task data validation"""
    # Test missing title
    invalid_task = {
        "description": "This task has no title"
    }

    result = await notion_integration.create_task(invalid_task)
    assert result["success"] is False
    assert "title is required" in result["error"].lower()

    # Test empty title
    empty_title_task = {
        "title": "",
        "description": "This task has an empty title"
    }

    result = await notion_integration.create_task(empty_title_task)
    assert result["success"] is False
    assert "title is required" in result["error"].lower()


@pytest.mark.notion
@pytest.mark.asyncio
async def test_notion_invalid_priority(notion_integration, sample_task_data):
    """Test handling of invalid priority values"""
    invalid_task = sample_task_data.copy()
    invalid_task["priority"] = "super_urgent"  # Invalid priority

    result = await notion_integration.create_task(invalid_task)
    assert result["success"] is False
    assert "priority must be one of" in result["error"].lower()


@pytest.mark.notion
@pytest.mark.asyncio
async def test_notion_invalid_date_format(notion_integration, sample_task_data):
    """Test handling of invalid date formats"""
    invalid_task = sample_task_data.copy()
    invalid_task["due_date"] = "invalid-date-format"

    result = await notion_integration.create_task(invalid_task)
    assert result["success"] is False
    assert "invalid due_date format" in result["error"].lower()


@pytest.mark.notion
@pytest.mark.asyncio
async def test_notion_long_content_handling(notion_integration, test_config):
    """Test handling of content that exceeds limits"""
    long_task = {
        "title": f"{test_config['test_prefix']} " + "x" * 1900,  # Close to limit
        "description": "y" * 1900,  # Close to limit
        "priority": "low"
    }

    # This should succeed (within limits)
    result = await notion_integration.create_task(long_task)
    if not test_config["use_mock"]:
        assert result["success"] is True, f"Long content task failed: {result.get('error')}"

    # Test exceeding limits
    too_long_task = {
        "title": f"{test_config['test_prefix']} " + "x" * 2500,  # Exceeds limit
        "description": "Valid description",
        "priority": "low"
    }

    result = await notion_integration.create_task(too_long_task)
    assert result["success"] is False
    assert "too long" in result["error"].lower()


@pytest.mark.notion
@pytest.mark.asyncio
async def test_notion_mock_mode(test_config):
    """Test that mock mode works correctly"""
    from app.integrations import NotionIntegration

    # Create integration in mock mode
    mock_integration = NotionIntegration(token="mock_token_for_dev")
    assert mock_integration.is_mock is True

    # Test mock task creation
    mock_task = {
        "title": "Mock Test Task",
        "description": "This is a mock task",
        "priority": "medium"
    }

    result = await mock_integration.create_task(mock_task)

    # Mock should always succeed
    assert result["success"] is True
    assert result["platform"] == "notion"
    assert "mock" in result["task_id"]
    assert "This is a mock response" in result["message"]


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.asyncio
async def test_notion_error_handling(notion_integration, test_config):
    """Test error handling with invalid database ID"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API error test")

    from app.integrations import NotionIntegration

    # Create integration with invalid database ID
    invalid_integration = NotionIntegration(
        token=notion_integration.token,
        database_id="invalid-database-id"
    )

    task_data = {
        "title": f"{test_config['test_prefix']} Error Test Task",
        "description": "This task should fail due to invalid database ID"
    }

    result = await invalid_integration.create_task(task_data)

    # Should fail gracefully
    assert result["success"] is False
    assert result.get("status_code") in [400, 404], f"Expected 400/404 error, got {result.get('status_code')}"
    assert "error" in result

    logger.info(f"✅ Error handling test passed: {result['error']}")


@pytest.mark.notion
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_notion_batch_task_creation(notion_integration, test_config, cleanup_tasks):
    """Test creating multiple tasks in sequence"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    tasks = []
    for i in range(3):
        task = {
            "title": f"{test_config['test_prefix']} Batch Task {i+1}",
            "description": f"This is batch task number {i+1} for testing sequential creation",
            "priority": ["low", "medium", "high"][i],
            "due_date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
        }
        tasks.append(task)

    created_tasks = []

    for i, task in enumerate(tasks):
        logger.info(f"Creating batch task {i+1}/3: {task['title']}")

        result = await notion_integration.create_task(task)

        assert result["success"] is True, f"Batch task {i+1} failed: {result.get('error')}"

        created_tasks.append(result)
        cleanup_tasks("notion", result["task_id"], task)

        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)

    logger.info(f"✅ Successfully created {len(created_tasks)} batch tasks")

    # Verify all tasks were created
    assert len(created_tasks) == 3
    for result in created_tasks:
        assert "task_id" in result
        assert "task_url" in result


@pytest.mark.notion
@pytest.mark.asyncio
async def test_notion_special_characters(notion_integration, test_config, cleanup_tasks):
    """Test handling of special characters and unicode"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    special_task = {
        "title": f"{test_config['test_prefix']} Special Chars: émojis 🚀🎉, quotes \"test\", & symbols",
        "description": "Testing special characters:\n- Unicode: café, naïve, résumé\n- Emojis: 🔥💡🚀\n- Quotes: \"double\" and 'single'\n- Symbols: & < > % @ #\n- Line breaks and formatting",
        "priority": "medium"
    }

    result = await notion_integration.create_task(special_task)

    assert result["success"] is True, f"Special characters task failed: {result.get('error')}"

    logger.info(f"✅ Created task with special characters: {result['task_id']}")
    cleanup_tasks("notion", result["task_id"], special_task)
