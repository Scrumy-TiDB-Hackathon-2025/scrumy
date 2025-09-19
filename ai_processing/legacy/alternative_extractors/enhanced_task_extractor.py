#!/usr/bin/env python3
"""
Enhanced Task Extractor - Outputs all database-supported fields
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
try:
    from .ai_processor import AIProcessor
except ImportError:
    from ai_processor import AIProcessor

class EnhancedTaskExtractor:
    """Task extractor that outputs all database-supported fields"""
    
    def __init__(self):
        self.ai_processor = AIProcessor()
    
    async def extract_comprehensive_tasks(self, transcript: str, meeting_id: str = None) -> Dict:
        """Extract tasks with all database fields populated"""
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_timestamp = datetime.now().isoformat()
        
        if not meeting_id:
            meeting_id = f"meeting_{int(datetime.now().timestamp())}"
        
        system_prompt = """You are an expert task extraction AI that outputs comprehensive task data for database storage.

        Extract tasks with ALL possible fields populated. Be thorough and accurate.
        
        FIELD REQUIREMENTS:
        - title: Max 500 chars, clear and actionable
        - assignee: Person's name or null if unassigned  
        - due_date: YYYY-MM-DD format only, or null
        - priority: 'low', 'medium', 'high', or 'urgent'
        - status: 'pending', 'in_progress', 'completed', or 'cancelled'
        - category: 'action_item', 'decision', 'follow_up', 'discussion', 'research'
        - business_impact: 'low', 'medium', 'high', or 'critical'
        - dependencies: Array of task titles or descriptions this depends on
        - mentioned_by: Who brought up or assigned this task
        - context: Surrounding discussion context (2-3 sentences)
        - explicit_level: 'direct' (clearly stated), 'implied' (suggested), 'inferred' (derived)
        - source_transcript_segment: Exact quote from transcript
        - ai_confidence_score: 0.0-1.0 confidence in extraction accuracy
        - extraction_method: 'explicit', 'implicit', 'dependency_analysis'"""
        
        prompt = f"""
        Extract comprehensive tasks from this meeting transcript:
        
        Meeting ID: {meeting_id}
        Current Date: {current_date}
        Extraction Time: {current_timestamp}
        
        Transcript:
        {transcript}
        
        Look for:
        - Direct assignments: "John will do X by Friday"
        - Action items: "We need to complete Y"
        - Decisions that require follow-up: "Let's go with option A, someone needs to implement it"
        - Implicit tasks: "The server is slow" → implies "Investigate server performance"
        - Dependencies: "After X is done, we'll do Y"
        
        Return JSON with ALL fields populated:
        {{
            "tasks": [
                {{
                    "ai_task_id": "task_1",
                    "title": "Update user documentation",
                    "description": "Update the user documentation to reflect new API changes and features discussed in the meeting",
                    "assignee": "John Smith",
                    "due_date": "2025-09-06",
                    "priority": "medium",
                    "status": "pending",
                    "category": "action_item",
                    "business_impact": "medium",
                    "dependencies": ["Complete API changes", "Review new features"],
                    "mentioned_by": "Sarah Johnson",
                    "context": "Discussion about user experience and documentation gaps after recent API updates",
                    "explicit_level": "direct",
                    "source_transcript_segment": "Sarah: John, can you update the documentation by Friday to include the new API endpoints?",
                    "ai_confidence_score": 0.95,
                    "extraction_method": "explicit"
                }}
            ],
            "extraction_metadata": {{
                "meeting_id": "{meeting_id}",
                "total_tasks_found": 1,
                "explicit_tasks": 1,
                "implicit_tasks": 0,
                "dependency_relationships": 2,
                "extraction_duration_ms": 1500,
                "ai_model_used": "llama3.1",
                "confidence_threshold": 0.7,
                "extracted_at": "{current_timestamp}"
            }}
        }}
        
        VALIDATION RULES:
        - Every task must have title, ai_task_id, extraction_method
        - Use null for missing optional fields, don't omit them
        - due_date must be YYYY-MM-DD or null
        - Convert relative dates: "tomorrow" → {datetime.now().replace(day=datetime.now().day+1).strftime('%Y-%m-%d')}
        - Convert weekdays: "Friday" → next Friday's date
        - Confidence score based on clarity of task statement
        - Dependencies as array of strings (task titles or descriptions)
        """
        
        try:
            response = await self.ai_processor.call_ollama(prompt, system_prompt)
            
            if not response or not response.strip():
                return self._empty_result(meeting_id)
            
            # Parse JSON response
            result = json.loads(response.strip())
            
            # Add meeting_id to each task and validate
            if 'tasks' in result:
                for task in result['tasks']:
                    task['meeting_id'] = meeting_id
                    task['ai_extracted_at'] = current_timestamp
                    
                    # Ensure all required fields exist
                    self._ensure_required_fields(task)
            
            return {
                "status": "success",
                "data": result
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Invalid JSON response: {str(e)}",
                "data": self._empty_result(meeting_id)
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Task extraction failed: {str(e)}",
                "data": self._empty_result(meeting_id)
            }
    
    def _ensure_required_fields(self, task: Dict) -> None:
        """Ensure all database fields exist with proper defaults"""
        
        # Required fields with defaults
        defaults = {
            'priority': 'medium',
            'status': 'pending', 
            'category': 'action_item',
            'business_impact': 'medium',
            'explicit_level': 'direct',
            'extraction_method': 'explicit',
            'ai_confidence_score': 0.8,
            'dependencies': [],
            'context': '',
            'source_transcript_segment': ''
        }
        
        for field, default_value in defaults.items():
            if field not in task or task[field] is None:
                task[field] = default_value
        
        # Validate enums
        if task.get('priority') not in ['low', 'medium', 'high', 'urgent']:
            task['priority'] = 'medium'
        
        if task.get('status') not in ['pending', 'in_progress', 'completed', 'cancelled']:
            task['status'] = 'pending'
        
        if task.get('category') not in ['action_item', 'decision', 'follow_up', 'discussion', 'research']:
            task['category'] = 'action_item'
        
        if task.get('business_impact') not in ['low', 'medium', 'high', 'critical']:
            task['business_impact'] = 'medium'
        
        if task.get('explicit_level') not in ['direct', 'implied', 'inferred']:
            task['explicit_level'] = 'direct'
    
    def _empty_result(self, meeting_id: str) -> Dict:
        """Return empty result structure"""
        return {
            'tasks': [],
            'extraction_metadata': {
                'meeting_id': meeting_id,
                'total_tasks_found': 0,
                'explicit_tasks': 0,
                'implicit_tasks': 0,
                'dependency_relationships': 0,
                'extracted_at': datetime.now().isoformat()
            }
        }
    
    def generate_sql_inserts(self, tasks: List[Dict]) -> List[tuple]:
        """Generate SQL INSERT statements for all database fields"""
        
        sql_statements = []
        
        # All possible database columns
        all_columns = [
            'meeting_id', 'title', 'description', 'assignee', 'due_date',
            'priority', 'status', 'category', 'business_impact', 'dependencies',
            'mentioned_by', 'context', 'explicit_level', 'ai_task_id',
            'ai_extracted_at', 'ai_confidence_score', 'source_transcript_segment',
            'extraction_method'
        ]
        
        for task in tasks:
            columns = []
            values = []
            placeholders = []
            
            for column in all_columns:
                if column in task and task[column] is not None:
                    columns.append(column)
                    
                    # Handle JSON fields
                    if column == 'dependencies' and isinstance(task[column], list):
                        values.append(json.dumps(task[column]))
                    else:
                        values.append(task[column])
                    
                    placeholders.append('%s')
            
            if columns:
                columns_str = ', '.join(columns)
                placeholders_str = ', '.join(placeholders)
                
                sql = f"INSERT INTO tasks ({columns_str}) VALUES ({placeholders_str})"
                sql_statements.append((sql, values))
        
        return sql_statements

# Usage example and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_enhanced_extraction():
        extractor = EnhancedTaskExtractor()
        
        test_transcript = """
        Sarah: Good morning everyone. Let's review our sprint goals.
        John: I can update the documentation by Friday. The API changes are ready.
        Sarah: Great! Mike, can you deploy to staging by Thursday? It's critical for the demo.
        Mike: Yes, I'll handle the staging deployment. Should be straightforward.
        Lisa: After staging is up, I'll run the full test suite. Might take a day or two.
        Sarah: Perfect. Also, we need someone to investigate the slow query issue.
        John: I noticed that too. I can look into the database performance after the docs.
        Sarah: Let's make that high priority. The customer is complaining.
        """
        
        meeting_id = "sprint_planning_001"
        
        print("🚀 TESTING ENHANCED TASK EXTRACTION")
        print("=" * 60)
        
        result = await extractor.extract_comprehensive_tasks(test_transcript, meeting_id)
        
        if result['status'] == 'success':
            data = result['data']
            tasks = data.get('tasks', [])
            metadata = data.get('extraction_metadata', {})
            
            print(f"✅ Extraction successful!")
            print(f"📊 Metadata:")
            print(f"   Meeting ID: {metadata.get('meeting_id')}")
            print(f"   Total tasks: {metadata.get('total_tasks_found')}")
            print(f"   Explicit tasks: {metadata.get('explicit_tasks')}")
            print(f"   Dependencies: {metadata.get('dependency_relationships')}")
            
            print(f"\n📋 COMPREHENSIVE TASKS:")
            for i, task in enumerate(tasks, 1):
                print(f"\n{i}. {task.get('title')}")
                print(f"   📝 Description: {task.get('description', 'None')}")
                print(f"   👤 Assignee: {task.get('assignee', 'None')}")
                print(f"   📅 Due Date: {task.get('due_date', 'None')}")
                print(f"   🔥 Priority: {task.get('priority')} | Impact: {task.get('business_impact')}")
                print(f"   📂 Category: {task.get('category')} | Status: {task.get('status')}")
                print(f"   🔗 Dependencies: {task.get('dependencies', [])}")
                print(f"   💬 Mentioned by: {task.get('mentioned_by', 'None')}")
                print(f"   🎯 Confidence: {task.get('ai_confidence_score', 0)}")
                print(f"   📍 Method: {task.get('extraction_method')} | Level: {task.get('explicit_level')}")
            
            # Generate SQL
            sql_statements = extractor.generate_sql_inserts(tasks)
            print(f"\n💾 SQL INSERT STATEMENTS:")
            for i, (sql, values) in enumerate(sql_statements, 1):
                print(f"\n{i}. {sql}")
                print(f"   Values: {values[:3]}..." if len(values) > 3 else f"   Values: {values}")
        
        else:
            print(f"❌ Extraction failed: {result['error']}")
    
    asyncio.run(test_enhanced_extraction())