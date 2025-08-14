# MCP Integration API Contract

## Notion MCP Server

### Base URL
```
http://localhost:8081
```

### Create Task
```
POST /mcp/notion/create-task
Headers: {
  "Authorization": "Bearer notion_token",
  "Notion-Version": "2022-06-28"
}
Body: {
  "title": "Task title",
  "description": "Task description",
  "assignee": "John Doe",
  "due_date": "2025-01-15",
  "priority": "high|medium|low",
  "category": "action_item|follow_up|decision_required",
  "meeting_id": "meeting_123",
  "meeting_title": "Sprint Planning"
}
Response: {
  "success": true,
  "notion_page_id": "page_123",
  "notion_url": "https://notion.so/page_123"
}
```

## Slack MCP Server

### Base URL
```
http://localhost:8082
```

### Send Task Notification
```
POST /mcp/slack/send-task-notification
Body: {
  "task_title": "Task title",
  "task_description": "Task description",
  "assignee": "John Doe",
  "due_date": "2025-01-15",
  "priority": "high",
  "meeting_title": "Sprint Planning",
  "meeting_id": "meeting_123",
  "notion_url": "https://notion.so/page_123"
}
Response: {
  "success": true,
  "message_ts": "1234567890.123456",
  "channel": "C1234567890"
}
```

## Integration API

### Base URL
```
http://localhost:3003
```

### Process Complete Meeting
```
POST /process-meeting
Body: {
  "meeting_data": {
    "meeting_id": "meeting_123",
    "summary": {...},
    "tasks": {...}
  },
  "create_notion_tasks": true,
  "send_slack_notifications": true,
  "notion_auth": "Bearer token",
  "slack_channel": "#scrumbot-tasks"
}
Response: {
  "success": true,
  "notion_result": {...},
  "slack_result": {...}
}
```