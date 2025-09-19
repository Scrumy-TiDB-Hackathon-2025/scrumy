# Assignee Management Documentation

## Overview
This document describes how to manage and augment assignee values in the Notion database as new users are mentioned in meetings.

## Current Implementation
- **Property Type**: Select field in Notion database
- **Current Options**: "ScrumAi" (auto-created as needed)
- **Behavior**: Automatically creates new assignee options when needed
- **Auto-Assignment**: System tasks default to "ScrumAi"
- **Source**: Names extracted from meeting transcriptions and task assignments

## Assignee Augmentation Strategy

### When New Users Are Named
The system now automatically handles new assignees through API calls:

### Automatic Augmentation Process ✅ IMPLEMENTED
1. **Auto-Detection**: When a task is assigned to a new person
2. **Auto-Creation**: System automatically adds the assignee to Notion database
3. **Retry Logic**: If task creation fails due to missing assignee, system:
   - Adds the assignee option to database
   - Retries task creation automatically
4. **Default Assignment**: System-generated tasks default to "ScrumAi"
5. **Caching**: System remembers known assignees to avoid duplicate API calls

### Future Enhancement Options

#### Option 1: Maintain Current Select Property ✅ CURRENT STATE
- Already converted to Select property type
- Current options: "ScrumAi"
- Benefits: Consistency, validation, autocomplete
- Requirement: Must add new options manually as team members are mentioned

#### Option 2: Person Property Integration
- Convert to Notion's Person property type
- Link to actual Notion workspace users
- Benefits: True user linking, avatars, notifications
- Requirements: Users must be in the Notion workspace

#### Option 3: Hybrid Approach
- Keep Text field for flexibility
- Maintain a separate "Known Users" reference
- Implement name normalization/suggestion logic
- Benefits: Flexibility + consistency guidance

### Implementation Notes

#### Auto-Creation Implementation:
```python
# System automatically handles new assignees
async def create_task(self, task: Dict) -> Dict:
    # Default to ScrumAi for system tasks
    if not task.get("assignee"):
        task["assignee"] = "ScrumAi"
    
    # Pre-emptively add assignee option to database
    await self._add_assignee_option(task["assignee"])
    
    # Create task - will retry once if assignee option missing
    result = await self._create_notion_page(task)
    
    # Automatic retry logic built into integration
    return result
```

#### For Person Property:
```python
# Attempt user lookup first
notion_user = resolve_notion_user(assignee_name)
if notion_user:
    properties["Assignee"] = {
        "people": [{"id": notion_user["id"]}]
    }
else:
    # Fallback to text or log for manual resolution
    logger.warning(f"Could not resolve user: {assignee_name}")
```

### Recommended Approach ✅ IMPLEMENTED
1. **Auto-Creation**: System automatically creates assignee options as needed ✅
2. **Default Assignment**: System tasks assigned to "ScrumAi" by default ✅
3. **User Tasks**: Meeting-derived tasks assigned to mentioned users ✅
4. **Retry Logic**: Automatic retry with assignee creation on failure ✅
5. **Caching**: Performance optimization to avoid duplicate API calls ✅
6. **Long-term**: Evaluate conversion to Person property when team is stable

### Maintenance Tasks
- [x] Convert to Select property ✅ DONE
- [x] Implement auto-creation of assignee options ✅ DONE
- [x] Add default "ScrumAi" assignment for system tasks ✅ DONE
- [x] Add retry logic for missing assignee options ✅ DONE
- [ ] Monitor assignee creation logs for name standardization
- [ ] Evaluate Person property integration for workspace users

### Current Database State
- **Property Type**: Select
- **Auto-Management**: Assignee options created automatically as needed ✅
- **Default Option**: "ScrumAi" (for system tasks)
- **Behavior**: No manual intervention required for new assignees

## Related Files
- `app/integrations.py` - Current assignee handling implementation
- `app/notion_tools.py` - Task creation with assignee field