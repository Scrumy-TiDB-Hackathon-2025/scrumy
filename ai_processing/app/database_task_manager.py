#!/usr/bin/env python3
"""
Database Task Manager - Handles comprehensive task storage and filtered integration
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

class DatabaseTaskManager:
    """Manages task storage in database and filtered output for integrations"""
    
    def __init__(self):
        # Define what fields each integration platform supports
        self.integration_supported_fields = {
            "notion": ["title", "description", "assignee", "priority", "status"],
            "clickup": ["title", "description", "assignee", "priority", "due_date"],
            "slack": ["title", "description", "assignee"],
            "database": "all"  # Database supports all fields
        }
    
    def store_comprehensive_tasks(self, ai_tasks: List[Dict], meeting_id: str) -> Dict:
        """
        Store all AI-extracted fields in database
        Returns: Database storage result with all fields preserved
        """
        
        stored_tasks = []
        
        for task in ai_tasks:
            # Ensure meeting_id is set
            task['meeting_id'] = meeting_id
            
            # Add database timestamps
            if 'ai_extracted_at' not in task:
                task['ai_extracted_at'] = datetime.now().isoformat()
            
            # Validate and store comprehensive task
            db_task = self._prepare_for_database(task)
            stored_tasks.append(db_task)
        
        return {
            "status": "success",
            "stored_tasks": stored_tasks,
            "total_stored": len(stored_tasks),
            "storage_metadata": {
                "meeting_id": meeting_id,
                "stored_at": datetime.now().isoformat(),
                "fields_preserved": len(stored_tasks[0].keys()) if stored_tasks else 0
            }
        }
    
    def get_integration_tasks(self, stored_tasks: List[Dict], platform: str = "integration") -> List[Dict]:
        """
        Filter stored tasks to only fields supported by integration platforms
        
        Args:
            stored_tasks: Full tasks from database
            platform: Target platform ("notion", "clickup", "slack", or "integration" for general)
        
        Returns:
            Filtered tasks with only supported fields
        """
        
        # Define supported fields for general integration (current working set)
        if platform == "integration":
            supported_fields = ["title", "description", "assignee", "priority"]
        else:
            supported_fields = self.integration_supported_fields.get(platform, ["title", "description"])
        
        # Store integration fields for reference
        if platform == "integration":
            self.integration_supported_fields["integration"] = supported_fields
        
        filtered_tasks = []
        
        for task in stored_tasks:
            filtered_task = {}
            
            for field in supported_fields:
                if field in task and task[field] is not None:
                    filtered_task[field] = task[field]
            
            # Ensure required fields exist
            if "title" in filtered_task:  # Only include if has required title
                filtered_tasks.append(filtered_task)
        
        return filtered_tasks
    
    def _prepare_for_database(self, task: Dict) -> Dict:
        """Prepare task for database storage with all fields"""
        
        # Ensure all database fields exist with proper defaults
        db_task = {
            # Core identification
            "ai_task_id": task.get("ai_task_id", f"task_{int(datetime.now().timestamp())}"),
            "meeting_id": task.get("meeting_id"),
            
            # Basic task info
            "title": task.get("title", "").strip(),
            "description": task.get("description", "").strip(),
            "assignee": task.get("assignee"),
            
            # Scheduling
            "due_date": task.get("due_date"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            
            # Classification
            "priority": self._validate_enum(task.get("priority"), ["low", "medium", "high", "urgent"], "medium"),
            "status": self._validate_enum(task.get("status"), ["pending", "in_progress", "completed", "cancelled"], "pending"),
            "category": task.get("category", "action_item"),
            "business_impact": self._validate_enum(task.get("business_impact"), ["low", "medium", "high", "critical"], "medium"),
            
            # Relationships and context
            "dependencies": task.get("dependencies", []),
            "mentioned_by": task.get("mentioned_by"),
            "context": task.get("context", ""),
            "explicit_level": self._validate_enum(task.get("explicit_level"), ["direct", "implied", "inferred"], "direct"),
            
            # AI metadata
            "ai_extracted_at": task.get("ai_extracted_at", datetime.now().isoformat()),
            "ai_confidence_score": task.get("ai_confidence_score", 0.8),
            "source_transcript_segment": task.get("source_transcript_segment", ""),
            "extraction_method": task.get("extraction_method", "explicit")
        }
        
        # Remove None values for cleaner storage
        return {k: v for k, v in db_task.items() if v is not None}
    
    def _validate_enum(self, value: str, valid_values: List[str], default: str) -> str:
        """Validate enum value against allowed values"""
        if value and value.lower() in valid_values:
            return value.lower()
        return default
    
    def generate_database_sql(self, tasks: List[Dict]) -> List[tuple]:
        """Generate SQL INSERT statements for comprehensive database storage"""
        
        sql_statements = []
        
        for task in tasks:
            columns = []
            values = []
            placeholders = []
            
            for key, value in task.items():
                if value is not None:
                    columns.append(key)
                    
                    # Handle JSON fields (dependencies)
                    if key == "dependencies" and isinstance(value, list):
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
                    
                    placeholders.append('%s')
            
            if columns:
                columns_str = ', '.join(columns)
                placeholders_str = ', '.join(placeholders)
                
                sql = f"INSERT INTO tasks ({columns_str}) VALUES ({placeholders_str})"
                sql_statements.append((sql, values))
        
        return sql_statements
    
    def show_field_mapping(self, stored_tasks: List[Dict]) -> Dict:
        """Show what fields are available vs what integrations support"""
        
        if not stored_tasks:
            return {"available_fields": [], "integration_mappings": {}}
        
        available_fields = list(stored_tasks[0].keys())
        
        integration_mappings = {}
        for platform, supported in self.integration_supported_fields.items():
            if platform == "database":
                continue
                
            if supported == "all":
                integration_mappings[platform] = available_fields
            else:
                integration_mappings[platform] = {
                    "supported": [f for f in supported if f in available_fields],
                    "unsupported": [f for f in available_fields if f not in supported]
                }
        
        return {
            "available_fields": available_fields,
            "integration_mappings": integration_mappings,
            "field_count": {
                "total_available": len(available_fields),
                "integration_supported": len(self.integration_supported_fields.get("integration", [])),
                "preservation_ratio": f"{len(self.integration_supported_fields.get('integration', []))}/{len(available_fields)}"
            }
        }

# Usage example
if __name__ == "__main__":
    
    def test_database_task_manager():
        manager = DatabaseTaskManager()
        
        # Sample comprehensive AI-extracted tasks
        ai_tasks = [
            {
                "ai_task_id": "task_1",
                "title": "Update documentation",
                "description": "Update user documentation with new API endpoints",
                "assignee": "John Smith",
                "due_date": "2025-09-06",
                "priority": "medium",
                "status": "pending",
                "category": "action_item",
                "business_impact": "medium",
                "dependencies": ["Complete API changes"],
                "mentioned_by": "Sarah Johnson",
                "context": "Discussion about API documentation gaps",
                "explicit_level": "direct",
                "ai_confidence_score": 0.95,
                "source_transcript_segment": "Sarah: John, update the docs by Friday",
                "extraction_method": "explicit"
            },
            {
                "ai_task_id": "task_2", 
                "title": "Deploy staging server",
                "description": "Deploy application to staging environment",
                "assignee": "Mike Wilson",
                "due_date": "2025-09-05",
                "priority": "high",
                "status": "pending",
                "category": "action_item",
                "business_impact": "high",
                "dependencies": [],
                "mentioned_by": "Sarah Johnson",
                "context": "Critical for demo preparation",
                "explicit_level": "direct",
                "ai_confidence_score": 0.88,
                "source_transcript_segment": "Sarah: Mike, deploy staging by Thursday",
                "extraction_method": "explicit"
            }
        ]
        
        meeting_id = "sprint_planning_001"
        
        print("🎯 DATABASE TASK MANAGER TEST")
        print("=" * 50)
        
        # Step 1: Store comprehensive tasks in database
        storage_result = manager.store_comprehensive_tasks(ai_tasks, meeting_id)
        stored_tasks = storage_result["stored_tasks"]
        
        print(f"✅ Database Storage:")
        print(f"   Tasks stored: {storage_result['total_stored']}")
        print(f"   Fields preserved: {storage_result['storage_metadata']['fields_preserved']}")
        print(f"   Meeting ID: {storage_result['storage_metadata']['meeting_id']}")
        
        # Step 2: Get filtered tasks for integration
        integration_tasks = manager.get_integration_tasks(stored_tasks, "integration")
        
        print(f"\n🔄 Integration Filtering:")
        print(f"   Original fields: {len(stored_tasks[0].keys()) if stored_tasks else 0}")
        print(f"   Integration fields: {len(integration_tasks[0].keys()) if integration_tasks else 0}")
        
        print(f"\n📋 STORED TASKS (Database - All Fields):")
        for i, task in enumerate(stored_tasks, 1):
            print(f"{i}. {task['title']}")
            print(f"   📝 Description: {task.get('description', 'None')}")
            print(f"   👤 Assignee: {task.get('assignee', 'None')}")
            print(f"   📅 Due Date: {task.get('due_date', 'None')}")
            print(f"   🔥 Priority: {task['priority']} | Impact: {task['business_impact']}")
            print(f"   📂 Category: {task['category']} | Status: {task['status']}")
            print(f"   🔗 Dependencies: {task.get('dependencies', [])}")
            print(f"   💬 Mentioned by: {task.get('mentioned_by', 'None')}")
            print(f"   🎯 Confidence: {task.get('ai_confidence_score', 0)}")
        
        print(f"\n📤 INTEGRATION TASKS (Filtered for Notion/ClickUp):")
        for i, task in enumerate(integration_tasks, 1):
            print(f"{i}. {task['title']}")
            print(f"   📝 Description: {task.get('description', 'None')}")
            print(f"   👤 Assignee: {task.get('assignee', 'None')}")
            print(f"   🔥 Priority: {task.get('priority', 'None')}")
        
        # Step 3: Show field mapping
        field_mapping = manager.show_field_mapping(stored_tasks)
        
        print(f"\n🗺️  FIELD MAPPING ANALYSIS:")
        print(f"   Available fields: {len(field_mapping['available_fields'])}")
        print(f"   Integration supported: {len(manager.integration_supported_fields['integration'])}")
        print(f"   Preservation ratio: {field_mapping['field_count']['preservation_ratio']}")
        
        print(f"\n📊 PLATFORM SUPPORT:")
        for platform, mapping in field_mapping['integration_mappings'].items():
            if isinstance(mapping, dict):
                print(f"   {platform}: {len(mapping['supported'])} supported, {len(mapping['unsupported'])} lost")
            else:
                print(f"   {platform}: {len(mapping)} fields")
        
        # Step 4: Generate SQL
        sql_statements = manager.generate_database_sql(stored_tasks)
        print(f"\n💾 DATABASE SQL (Sample):")
        if sql_statements:
            sql, values = sql_statements[0]
            print(f"   {sql}")
            print(f"   Values: {values[:5]}... (showing first 5)")
        
        print(f"\n🎉 ARCHITECTURE SUMMARY:")
        print("✅ AI extracts comprehensive task data")
        print("✅ Database stores ALL fields (no data loss)")
        print("✅ Integration filters to supported fields only")
        print("✅ Notion/ClickUp APIs receive compatible data")
        print("✅ Rich analytics available from database")
    
    test_database_task_manager()