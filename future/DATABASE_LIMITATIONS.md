# Database Limitations - AI Processing Integration

## Current Status

The AI processing integration bridge has been implemented with temporary limitations due to database schema constraints.

## Excluded Fields

The following fields are **temporarily excluded** from task creation to prevent database errors:

### `meeting_id`
- **Purpose**: Track which meeting generated the task
- **AI Processing**: Generates this field from meeting context
- **Integration System**: Code supports this field
- **Database**: **NOT SUPPORTED** - Schema needs update
- **Status**: Excluded in `integration_bridge.py`

### `due_date` 
- **Purpose**: Set task deadlines based on AI analysis
- **AI Processing**: Can extract due dates from meeting content
- **Integration System**: Code supports this field (with proper formatting)
- **Database**: **NOT SUPPORTED** - Schema needs update  
- **Status**: Excluded in `integration_bridge.py`

## Current Working Fields

These fields are fully supported and working:

- ✅ `title` (required) - Task title from AI extraction
- ✅ `description` (optional) - Task details from AI analysis
- ✅ `assignee` (optional) - Person assigned to task
- ✅ `priority` (optional) - Task priority (low/medium/high/urgent)

## Implementation Details

### Location of Exclusions

**File**: `ai_processing/app/integration_bridge.py`

**Method**: `_transform_ai_task_to_integration_format()`

**Code Section**:
```python
# TODO: Uncomment when database supports these fields
# meeting_id = ai_task.get("meeting_id")
# if meeting_id:
#     integration_task["meeting_id"] = meeting_id
#
# due_date = ai_task.get("due_date")  
# if due_date:
#     integration_task["due_date"] = due_date
```

### Integration System Compatibility

The integration system (`integration/app/`) already handles these fields properly:
- Uses `.get()` methods for optional field access
- Graceful handling when fields are missing
- No code changes needed in integration system

## Future Updates Required

### When Database Schema is Updated

1. **Update Database Schema**:
   - Add `meeting_id` column to tasks table
   - Add `due_date` column to tasks table

2. **Update AI Processing Integration**:
   - Uncomment the excluded fields in `integration_bridge.py`
   - Update the `create_task_everywhere()` call to include new fields

3. **Test End-to-End**:
   - Verify tasks are created with meeting context
   - Verify due dates are properly formatted and stored

### Code Changes Needed

**File**: `ai_processing/app/integration_bridge.py`

**In `_transform_ai_task_to_integration_format()`**:
```python
# Uncomment these lines:
meeting_id = ai_task.get("meeting_id")
if meeting_id:
    integration_task["meeting_id"] = meeting_id

due_date = ai_task.get("due_date")  
if due_date:
    integration_task["due_date"] = due_date
```

**In `create_tasks_from_ai_results()`**:
```python
# Update the tool call to include new fields:
result = await self.tools_registry.create_task_everywhere(
    title=integration_task["title"],
    description=integration_task["description"],
    assignee=integration_task["assignee"],
    priority=integration_task["priority"],
    meeting_id=integration_task.get("meeting_id"),  # Add this
    due_date=integration_task.get("due_date")       # Add this
)
```

## Testing Strategy

### Current Testing
- Integration bridge works with 4 core fields
- Tasks are created successfully in Notion, Slack, ClickUp
- Error handling works when fields are missing

### Future Testing
- Test with `meeting_id` field included
- Test with `due_date` field in various formats
- Verify database storage of new fields
- Test integration system handling of new fields

## Migration Path

1. **Phase 1** (Current): Core integration working without meeting_id/due_date
2. **Phase 2**: Update database schema to support new fields
3. **Phase 3**: Update AI processing to include new fields
4. **Phase 4**: End-to-end testing and validation

## Commit Reference

This limitation was implemented in commit: `[COMMIT_HASH]`

Search for "TODO: Add when database supports" in the codebase to find all locations that need updates when database schema is ready.