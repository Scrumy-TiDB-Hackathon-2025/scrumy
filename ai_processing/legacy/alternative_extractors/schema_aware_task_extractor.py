#!/usr/bin/env python3
"""
Schema-Aware Task Extractor - Extracts tasks in database-compatible format
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from .ai_processor import AIProcessor

class SchemaAwareTaskExtractor:
    """Task extractor that outputs database-compatible format directly"""
    
    def __init__(self):
        self.ai_processor = AIProcessor()
        
        # Database schema definition for AI prompt
        self.db_schema = {
            "required_fields": {
                "meeting_id": "VARCHAR(255) - Will be provided by system",
                "title": "VARCHAR(500) - Clear, actionable task title",
                "description": "TEXT - Detailed description"
            },
            "optional_fields": {
                "assignee": "VARCHAR(255) - Person assigned or null",
                "due_date": "DATE - ISO format YYYY-MM-DD or null",
                "priority": "ENUM('low', 'medium', 'high') - Default: medium",
                "status": "ENUM('pending', 'in_progress', 'completed', 'cancelled') - Default: pending"
            },
            "date_conversion_rules": {
                "today": "Use current date",
                "tomorrow": "Add 1 day to current date", 
                "friday/monday/etc": "Next occurrence of that weekday",
                "next week": "End of next week (Friday)",
                "end of month": "Last day of current month",
                "in X days": "Add X days to current date",
                "MM/DD/YYYY or YYYY-MM-DD": "Convert to YYYY-MM-DD format"
            }
        }
    
    async def extract_database_ready_tasks(self, transcript: str, meeting_id: str) -> Dict:
        """Extract tasks in database-compatible format"""
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        system_prompt = f"""You are a database-aware task extraction expert. 
        
        Extract tasks that are DIRECTLY compatible with this database schema:
        
        REQUIRED FIELDS:
        - title: VARCHAR(500) - Clear, actionable task title
        - description: TEXT - Detailed description of what needs to be done
        
        OPTIONAL FIELDS:
        - assignee: VARCHAR(255) - Person assigned (or null if unassigned)
        - due_date: DATE - ISO format YYYY-MM-DD only (or null if no deadline)
        - priority: 'low', 'medium', or 'high' (default: 'medium')
        - status: 'pending', 'in_progress', 'completed', or 'cancelled' (default: 'pending')
        
        DATE CONVERSION RULES (today is {current_date}):
        - "today" → {current_date}
        - "tomorrow" → {datetime.now().replace(day=datetime.now().day+1).strftime('%Y-%m-%d')}
        - "friday", "monday", etc → Next occurrence in YYYY-MM-DD format
        - "next week" → End of next week (Friday) in YYYY-MM-DD format
        - "in 3 days" → Add 3 days to today in YYYY-MM-DD format
        - If date is unclear or invalid → null
        
        CRITICAL: Output ONLY valid database values. No natural language dates!"""
        
        prompt = f"""
        Extract database-ready tasks from this meeting transcript:
        
        Transcript:
        {transcript}
        
        Meeting ID: {meeting_id}
        Current Date: {current_date}
        
        Look for:
        - Direct assignments: "John will do X"
        - Action items: "We need to complete Y" 
        - Commitments: "I'll handle Z by Friday"
        - Follow-ups: "Let's review this next week"
        
        Return JSON in this EXACT format (database-compatible):
        {{
            "tasks": [
                {{
                    "title": "Update documentation",
                    "description": "Update the user documentation with new features",
                    "assignee": "John Smith",
                    "due_date": "2025-09-06",
                    "priority": "medium",
                    "status": "pending"
                }},
                {{
                    "title": "Review code changes", 
                    "description": "Review the pull request for authentication module",
                    "assignee": null,
                    "due_date": null,
                    "priority": "high",
                    "status": "pending"
                }}
            ],
            "extraction_metadata": {{
                "total_tasks_found": 2,
                "tasks_with_deadlines": 1,
                "tasks_with_assignees": 1,
                "extracted_at": "{datetime.now().isoformat()}"
            }}
        }}
        
        VALIDATION RULES:
        - title: Max 500 characters, required
        - assignee: Max 255 characters or null
        - due_date: YYYY-MM-DD format only or null
        - priority: Must be 'low', 'medium', or 'high'
        - status: Must be 'pending', 'in_progress', 'completed', or 'cancelled'
        
        If a task doesn't meet these requirements, skip it or fix it to comply.
        """
        
        try:
            response = await self.ai_processor.call_ollama(prompt, system_prompt)
            
            if not response or not response.strip():
                return self._empty_result()
            
            # Parse and validate response
            result = json.loads(response.strip())
            
            # Add meeting_id to each task
            if 'tasks' in result:
                for task in result['tasks']:
                    task['meeting_id'] = meeting_id
            
            # Validate against schema
            validated_result = self._validate_tasks(result)
            
            return {
                "status": "success",
                "data": validated_result
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error", 
                "error": f"Invalid JSON response: {str(e)}",
                "data": self._empty_result()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Task extraction failed: {str(e)}",
                "data": self._empty_result()
            }
    
    def _validate_tasks(self, result: Dict) -> Dict:
        """Validate tasks against database schema"""
        
        if 'tasks' not in result:
            return self._empty_result()
        
        valid_tasks = []
        invalid_tasks = []
        
        for task in result['tasks']:
            validation_errors = []
            
            # Validate required fields
            if not task.get('title'):
                validation_errors.append("Missing required field: title")
            elif len(task['title']) > 500:
                validation_errors.append("Title exceeds 500 characters")
            
            # Validate optional fields
            if task.get('assignee') and len(task['assignee']) > 255:
                validation_errors.append("Assignee exceeds 255 characters")
            
            if task.get('priority') and task['priority'] not in ['low', 'medium', 'high']:
                validation_errors.append(f"Invalid priority: {task['priority']}")
            
            if task.get('status') and task['status'] not in ['pending', 'in_progress', 'completed', 'cancelled']:
                validation_errors.append(f"Invalid status: {task['status']}")
            
            # Validate date format
            if task.get('due_date'):
                try:
                    datetime.strptime(task['due_date'], '%Y-%m-%d')
                except ValueError:
                    validation_errors.append(f"Invalid date format: {task['due_date']}")
            
            # Set defaults for missing optional fields
            if 'priority' not in task or not task['priority']:
                task['priority'] = 'medium'
            
            if 'status' not in task or not task['status']:
                task['status'] = 'pending'
            
            if validation_errors:
                invalid_tasks.append({
                    'task': task,
                    'errors': validation_errors
                })
            else:
                valid_tasks.append(task)
        
        return {
            'tasks': valid_tasks,
            'invalid_tasks': invalid_tasks,
            'task_summary': {
                'total_tasks': len(result['tasks']),
                'valid_tasks': len(valid_tasks),
                'invalid_tasks': len(invalid_tasks),
                'tasks_with_deadlines': len([t for t in valid_tasks if t.get('due_date')]),
                'tasks_with_assignees': len([t for t in valid_tasks if t.get('assignee')])
            },
            'extraction_metadata': result.get('extraction_metadata', {})
        }
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'tasks': [],
            'invalid_tasks': [],
            'task_summary': {
                'total_tasks': 0,
                'valid_tasks': 0,
                'invalid_tasks': 0,
                'tasks_with_deadlines': 0,
                'tasks_with_assignees': 0
            },
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat()
            }
        }
    
    def generate_sql_inserts(self, tasks: List[Dict]) -> List[tuple]:
        """Generate SQL INSERT statements for validated tasks"""
        
        sql_statements = []
        
        for task in tasks:
            # Build column names and values
            columns = []
            values = []
            placeholders = []
            
            for key, value in task.items():
                if value is not None:
                    columns.append(key)
                    values.append(value)
                    placeholders.append('%s')
            
            if columns:
                columns_str = ', '.join(columns)
                placeholders_str = ', '.join(placeholders)
                
                sql = f"INSERT INTO tasks ({columns_str}) VALUES ({placeholders_str})"
                sql_statements.append((sql, values))
        
        return sql_statements

# Usage example
if __name__ == "__main__":
    import asyncio
    
    async def test_schema_aware_extraction():
        extractor = SchemaAwareTaskExtractor()
        
        test_transcript = """
        Sarah: John, can you update the documentation by Friday?
        John: Yes, I'll handle the documentation update.
        Sarah: Mike, we need the staging server deployed by Thursday.
        Mike: I'll deploy staging by Thursday.
        Lisa: After deployment, I'll test the new features.
        """
        
        meeting_id = "meeting_schema_test_001"
        
        print("🎯 TESTING SCHEMA-AWARE TASK EXTRACTION")
        print("=" * 50)
        
        result = await extractor.extract_database_ready_tasks(test_transcript, meeting_id)
        
        if result['status'] == 'success':
            data = result['data']
            
            print(f"✅ Extraction successful!")
            print(f"📊 Summary:")
            print(f"   Total tasks: {data['task_summary']['total_tasks']}")
            print(f"   Valid tasks: {data['task_summary']['valid_tasks']}")
            print(f"   Invalid tasks: {data['task_summary']['invalid_tasks']}")
            
            print(f"\n💾 DATABASE-READY TASKS:")
            for i, task in enumerate(data['tasks'], 1):
                print(f"{i}. {task['title']}")
                print(f"   Assignee: {task.get('assignee', 'None')}")
                print(f"   Due Date: {task.get('due_date', 'None')}")
                print(f"   Priority: {task['priority']}")
                print(f"   Meeting ID: {task['meeting_id']}")
            
            # Generate SQL
            sql_statements = extractor.generate_sql_inserts(data['tasks'])
            print(f"\n💾 SQL STATEMENTS:")
            for i, (sql, values) in enumerate(sql_statements, 1):
                print(f"{i}. {sql}")
                print(f"   Values: {values}")
        
        else:
            print(f"❌ Extraction failed: {result['error']}")
    
    asyncio.run(test_schema_aware_extraction())