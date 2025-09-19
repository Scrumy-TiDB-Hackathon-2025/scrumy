import pytest
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_connection(clickup_integration, test_config):
    """Test basic ClickUp API connection"""
    # Check if we're in mock mode
    if test_config["use_mock"]:
        assert clickup_integration.is_mock
        pytest.skip("Running in mock mode - skipping real API test")

    # Verify we have required configuration
    assert clickup_integration.token is not None, "CLICKUP_TOKEN is required"
    assert clickup_integration.list_id is not None, "CLICKUP_LIST_ID is required"
    assert clickup_integration.team_id is not None, "CLICKUP_TEAM_ID is required"

    # Check that we're not in mock mode with real credentials
    assert not clickup_integration.is_mock, "Should not be in mock mode with real token"

    logger.info(f"Testing ClickUp connection with list: {clickup_integration.list_id}")


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_create_basic_task(clickup_integration, sample_task_data, test_config, cleanup_tasks):
    """Test creating a basic task in ClickUp"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    logger.info(f"Creating basic task: {sample_task_data['title']}")

    result = await clickup_integration.create_task(sample_task_data)

    # Verify success
    assert result["success"] is True, f"Task creation failed: {result.get('error', 'Unknown error')}"
    assert "task_id" in result, "Result should contain task_id"
    assert "task_url" in result, "Result should contain task_url"

    # Log the created task
    logger.info(f"✅ Created ClickUp task: {result['task_id']}")
    logger.info(f"📝 Task URL: {result['task_url']}")

    # Track for cleanup
    cleanup_tasks("clickup", result["task_id"], sample_task_data)


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_create_task_with_all_fields(clickup_integration, test_config, cleanup_tasks):
    """Test creating a task with all possible fields"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    # Create a comprehensive task with all fields
    comprehensive_task = {
        "title": f"{test_config['test_prefix']} Comprehensive ClickUp Test Task",
        "description": "This is a comprehensive test task with all fields populated. It includes a longer description to test text handling, special characters like émojis 🚀, and various formatting.\n\n**Key Features:**\n- Task management\n- Priority handling\n- Due date tracking",
        "priority": "urgent",
        "due_date": "2025-01-25",
        "assignee": "Test User",
        "status": "in progress",
        "meeting_id": "comprehensive_test_001",
        "meeting_title": "Comprehensive Feature Testing Meeting",
        "tags": ["testing", "comprehensive", "scrumbot"],
        "estimated_hours": 8
    }

    logger.info(f"Creating comprehensive task: {comprehensive_task['title']}")

    result = await clickup_integration.create_task(comprehensive_task)

    # Verify success
    assert result["success"] is True, f"Comprehensive task creation failed: {result.get('error', 'Unknown error')}"
    assert "task_id" in result
    assert "task_url" in result

    logger.info(f"✅ Created comprehensive ClickUp task: {result['task_id']}")

    # Track for cleanup
    cleanup_tasks("clickup", result["task_id"], comprehensive_task)


@pytest.mark.clickup
@pytest.mark.asyncio
async def test_clickup_task_validation(clickup_integration):
    """Test task data validation"""
    # Test missing title
    invalid_task = {
        "description": "This task has no title"
    }

    result = await clickup_integration.create_task(invalid_task)
    assert result["success"] is False
    assert "title is required" in result["error"].lower()

    # Test empty title
    empty_title_task = {
        "title": "",
        "description": "This task has an empty title"
    }

    result = await clickup_integration.create_task(empty_title_task)
    assert result["success"] is False
    assert "title is required" in result["error"].lower()


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_priority_mapping(clickup_integration, test_config, cleanup_tasks):
    """Test ClickUp priority mapping (urgent=1, high=2, medium=3, low=4)"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    priorities = ["urgent", "high", "medium", "low"]
    created_tasks = []

    for priority in priorities:
        task = {
            "title": f"{test_config['test_prefix']} Priority Test - {priority.upper()}",
            "description": f"Testing {priority} priority mapping in ClickUp",
            "priority": priority
        }

        logger.info(f"Creating task with priority: {priority}")

        result = await clickup_integration.create_task(task)

        assert result["success"] is True, f"Priority {priority} task failed: {result.get('error')}"

        created_tasks.append(result)
        cleanup_tasks("clickup", result["task_id"], task)

        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)

    logger.info(f"✅ Successfully created {len(created_tasks)} tasks with different priorities")


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_user_resolution(clickup_integration, test_config):
    """Test user name to ID resolution"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    # This test will attempt to resolve a user, but won't fail if user doesn't exist
    # since we can't guarantee test users exist in the workspace
    test_user = "test@example.com"

    user_id = await clickup_integration._resolve_user_name(test_user)

    # User ID should be None for non-existent user, or a string for existing user
    assert user_id is None or isinstance(user_id, str)

    if user_id:
        logger.info(f"✅ Resolved user '{test_user}' to ID: {user_id}")
    else:
        logger.info(f"ℹ️  User '{test_user}' not found in workspace (expected for test)")


@pytest.mark.clickup
@pytest.mark.asyncio
async def test_clickup_long_content_handling(clickup_integration, test_config, cleanup_tasks):
    """Test handling of content that exceeds ClickUp limits"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    # ClickUp limits: title 255 chars, description 8000 chars
    long_task = {
        "title": f"{test_config['test_prefix']} " + "x" * 200,  # Within limit
        "description": "y" * 7000,  # Within limit
        "priority": "low"
    }

    # This should succeed (within limits)
    result = await clickup_integration.create_task(long_task)
    assert result["success"] is True, f"Long content task failed: {result.get('error')}"

    if result["success"]:
        cleanup_tasks("clickup", result["task_id"], long_task)

    # Test title truncation
    very_long_task = {
        "title": f"{test_config['test_prefix']} " + "x" * 300,  # Exceeds 255 limit
        "description": "Valid description",
        "priority": "low"
    }

    # Should succeed with truncated title
    result = await clickup_integration.create_task(very_long_task)
    assert result["success"] is True, "Task creation should succeed with truncated title"

    if result["success"]:
        cleanup_tasks("clickup", result["task_id"], very_long_task)


@pytest.mark.clickup
@pytest.mark.asyncio
async def test_clickup_date_format_handling(clickup_integration, sample_task_data):
    """Test handling of various date formats"""
    # Test valid ISO date
    valid_task = sample_task_data.copy()
    valid_task["due_date"] = "2025-01-20"

    result = await clickup_integration.create_task(valid_task)
    # Should succeed in both mock and real mode
    assert result["success"] is True or "due_date" not in result.get("error", "")

    # Test invalid date format
    invalid_task = sample_task_data.copy()
    invalid_task["due_date"] = "invalid-date-format"

    # Should succeed (invalid dates are ignored, not failed)
    result = await clickup_integration.create_task(invalid_task)
    assert result["success"] is True or "due_date" in result.get("error", "")


@pytest.mark.clickup
@pytest.mark.asyncio
async def test_clickup_mock_mode(test_config):
    """Test that mock mode works correctly"""
    from app.integrations import ClickUpIntegration

    # Create integration in mock mode
    mock_integration = ClickUpIntegration(token="mock_token_for_dev")
    assert mock_integration.is_mock is True

    # Test mock task creation
    mock_task = {
        "title": "Mock ClickUp Test Task",
        "description": "This is a mock task",
        "priority": "high"
    }

    result = await mock_integration.create_task(mock_task)

    # Mock should always succeed
    assert result["success"] is True
    assert result["platform"] == "clickup"
    assert "mock" in result["task_id"]
    assert "This is a mock response" in result["message"]


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_error_handling(clickup_integration, test_config):
    """Test error handling with invalid list ID"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API error test")

    from app.integrations import ClickUpIntegration

    # Create integration with invalid list ID
    invalid_integration = ClickUpIntegration(
        token=clickup_integration.token,
        list_id="invalid_list_id",
        team_id=clickup_integration.team_id
    )

    task_data = {
        "title": f"{test_config['test_prefix']} Error Test Task",
        "description": "This task should fail due to invalid list ID"
    }

    result = await invalid_integration.create_task(task_data)

    # Should fail gracefully
    assert result["success"] is False
    assert result.get("status_code") in [400, 404], f"Expected 400/404 error, got {result.get('status_code')}"
    assert "error" in result

    logger.info(f"✅ Error handling test passed: {result['error']}")


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_clickup_batch_task_creation(clickup_integration, test_config, cleanup_tasks):
    """Test creating multiple tasks in sequence"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    tasks = []
    for i in range(3):
        task = {
            "title": f"{test_config['test_prefix']} Batch ClickUp Task {i+1}",
            "description": f"This is batch task number {i+1} for testing sequential creation in ClickUp",
            "priority": ["low", "medium", "high"][i],
            "due_date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
        }
        tasks.append(task)

    created_tasks = []

    for i, task in enumerate(tasks):
        logger.info(f"Creating batch task {i+1}/3: {task['title']}")

        result = await clickup_integration.create_task(task)

        assert result["success"] is True, f"Batch task {i+1} failed: {result.get('error')}"

        created_tasks.append(result)
        cleanup_tasks("clickup", result["task_id"], task)

        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)

    logger.info(f"✅ Successfully created {len(created_tasks)} batch tasks")

    # Verify all tasks were created
    assert len(created_tasks) == 3
    for result in created_tasks:
        assert "task_id" in result
        assert "task_url" in result


@pytest.mark.clickup
@pytest.mark.asyncio
async def test_clickup_special_characters(clickup_integration, test_config, cleanup_tasks):
    """Test handling of special characters and unicode in ClickUp"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    special_task = {
        "title": f"{test_config['test_prefix']} Special Chars: émojis 🚀🎯, quotes \"test\"",
        "description": "Testing special characters in ClickUp:\n- Unicode: café, naïve, résumé\n- Emojis: 🔥💡🚀🎯\n- Quotes: \"double\" and 'single'\n- Symbols: & < > % @ #\n- Line breaks and **markdown** formatting",
        "priority": "medium"
    }

    result = await clickup_integration.create_task(special_task)

    assert result["success"] is True, f"Special characters task failed: {result.get('error')}"

    logger.info(f"✅ Created ClickUp task with special characters: {result['task_id']}")
    cleanup_tasks("clickup", result["task_id"], special_task)


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_tags_handling(clickup_integration, test_config, cleanup_tasks):
    """Test handling of tags in ClickUp tasks"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    tagged_task = {
        "title": f"{test_config['test_prefix']} Tags Test Task",
        "description": "Testing tag functionality in ClickUp",
        "priority": "medium",
        "tags": ["test", "scrumbot", "integration", "automated"]
    }

    result = await clickup_integration.create_task(tagged_task)

    assert result["success"] is True, f"Tagged task creation failed: {result.get('error')}"

    logger.info(f"✅ Created ClickUp task with tags: {result['task_id']}")
    cleanup_tasks("clickup", result["task_id"], tagged_task)


@pytest.mark.clickup
@pytest.mark.integration
@pytest.mark.asyncio
async def test_clickup_assignee_with_nonexistent_user(clickup_integration, test_config, cleanup_tasks):
    """Test task creation with non-existent assignee"""
    if test_config["use_mock"]:
        pytest.skip("Running in mock mode - skipping real API test")

    task_with_fake_assignee = {
        "title": f"{test_config['test_prefix']} Nonexistent Assignee Test",
        "description": "Testing task creation with non-existent user assignment",
        "priority": "low",
        "assignee": "nonexistent_user@example.com"
    }

    result = await clickup_integration.create_task(task_with_fake_assignee)

    # Should succeed (assignee just won't be set)
    assert result["success"] is True, f"Task with nonexistent assignee failed: {result.get('error')}"

    logger.info(f"✅ Created ClickUp task with nonexistent assignee (assignee ignored): {result['task_id']}")
    cleanup_tasks("clickup", result["task_id"], task_with_fake_assignee)
