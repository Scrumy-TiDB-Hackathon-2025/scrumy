import json
from typing import Dict, List
from datetime import datetime, timedelta
import re
import asyncio

class TaskExtractor:

    def __init__(self, ai_processor):

        self.ai_processor = ai_processor



    async def extract_comprehensive_tasks(self, transcript: str, meeting_context: Dict = None) -> Dict:

        """Extract tasks with comprehensive analysis"""



        # Handle null/empty input
        if not transcript or not transcript.strip():
            return {
                "tasks": [],
                "task_summary": {
                    "total_tasks": 0,
                    "high_priority": 0,
                    "with_deadlines": 0,
                    "assigned": 0
                },
                "extraction_metadata": {
                    "explicit_tasks_found": 0,
                    "implicit_tasks_found": 0,
                    "extracted_at": datetime.now().isoformat(),
                    "error": "No transcript provided for task extraction"
                }
            }

        try:
            # Run multiple extraction strategies

            tasks = [

                self._extract_explicit_tasks(transcript),

                self._extract_implicit_tasks(transcript),

                self._analyze_task_dependencies(transcript),

                self._prioritize_tasks(transcript)

            ]



            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle potential exceptions from individual strategies
            explicit_tasks = results[0] if not isinstance(results[0], Exception) else {"tasks": []}
            implicit_tasks = results[1] if not isinstance(results[1], Exception) else {"tasks": []}
            dependencies = results[2] if not isinstance(results[2], Exception) else {"dependencies": [], "critical_path": [], "parallel_tracks": []}
            priorities = results[3] if not isinstance(results[3], Exception) else {"task_priorities": []}



            # Merge and deduplicate tasks

            all_tasks = self._merge_tasks(explicit_tasks, implicit_tasks)



            # Apply dependencies and priorities

            final_tasks = self._apply_task_metadata(all_tasks, dependencies, priorities)



            return {

                "tasks": final_tasks,

                "task_summary": {

                    "total_tasks": len(final_tasks),

                    "high_priority": len([t for t in final_tasks if t and t.get("priority") == "high"]),

                    "with_deadlines": len([t for t in final_tasks if t and t.get("due_date")]),

                    "assigned": len([t for t in final_tasks if t and t.get("assignee") != "Unassigned"])

                },

                "extraction_metadata": {

                    "explicit_tasks_found": len(explicit_tasks.get("tasks", [])),

                    "implicit_tasks_found": len(implicit_tasks.get("tasks", [])),

                    "extracted_at": datetime.now().isoformat()

                }

            }
        except Exception as e:
            return {
                "tasks": [],
                "task_summary": {
                    "total_tasks": 0,
                    "high_priority": 0,
                    "with_deadlines": 0,
                    "assigned": 0
                },
                "extraction_metadata": {
                    "explicit_tasks_found": 0,
                    "implicit_tasks_found": 0,
                    "extracted_at": datetime.now().isoformat(),
                    "error": f"Task extraction failed: {str(e)}"
                }
            }



    async def _extract_explicit_tasks(self, transcript: str) -> Dict:

        """Extract explicitly mentioned tasks and action items"""

        if not transcript or not transcript.strip():
            return {"tasks": []}

        system_prompt = """You are an expert at identifying explicit action items and tasks from meeting discussions.

        Look for clear commitments, assignments, and action items that were directly stated."""



        prompt = f"""

        Extract all explicitly mentioned tasks and action items from this meeting:



        Transcript:

        {transcript}



        Look for phrases like:

        - "I'll do X"

        - "Can you handle Y"

        - "We need to complete Z"

        - "Action item: ..."

        - "Follow up on ..."



        Return JSON with explicit tasks:

        {{

            "tasks": [

                {{

                    "id": "task_1",

                    "title": "Clear, actionable task title",

                    "description": "Detailed description of what needs to be done",

                    "assignee": "Person assigned or 'Unassigned'",

                    "mentioned_by": "Who brought up this task",

                    "due_date": "Deadline if mentioned or null",

                    "context": "Surrounding discussion context",

                    "explicit_level": "direct|implied|inferred"

                }}

            ]

        }}

        """



        try:
            response = await self.ai_processor.call_ollama(prompt, system_prompt)

            if not response or not response.strip():
                return {"tasks": []}

            result = json.loads(response)

            # Validate result structure
            if not isinstance(result, dict):
                return {"tasks": []}

            if "tasks" not in result:
                result["tasks"] = []

            # Validate task structure
            validated_tasks = []
            for task in result.get("tasks", []):
                if isinstance(task, dict) and task.get("title"):
                    validated_tasks.append(task)

            result["tasks"] = validated_tasks
            return result

        except (json.JSONDecodeError, Exception):

            return {"tasks": []}



    async def _extract_implicit_tasks(self, transcript: str) -> Dict:

        """Extract implicit tasks that weren't directly stated but are implied"""

        if not transcript or not transcript.strip():
            return {"tasks": []}

        system_prompt = """You are an expert at identifying implicit tasks and follow-up actions.

        Look for problems mentioned, decisions made, or discussions that imply work needs to be done."""



        prompt = f"""

        Extract implicit tasks and follow-up actions from this meeting:



        Transcript:

        {transcript}



        Look for:

        - Problems that need solutions

        - Decisions that require implementation

        - Questions that need research

        - Issues that need follow-up

        - Processes that need improvement



        Return JSON with implicit tasks:

        {{

            "tasks": [

                {{

                    "id": "implicit_task_1",

                    "title": "Inferred task title",

                    "description": "What needs to be done based on discussion",

                    "rationale": "Why this task is needed",

                    "urgency": "high|medium|low",

                    "category": "research|implementation|follow_up|decision_required"

                }}

            ]

        }}

        """



        try:
            response = await self.ai_processor.call_ollama(prompt, system_prompt)

            if not response or not response.strip():
                return {"tasks": []}

            result = json.loads(response)

            # Validate result structure
            if not isinstance(result, dict):
                return {"tasks": []}

            if "tasks" not in result:
                result["tasks"] = []

            # Validate task structure
            validated_tasks = []
            for task in result.get("tasks", []):
                if isinstance(task, dict) and task.get("title"):
                    validated_tasks.append(task)

            result["tasks"] = validated_tasks
            return result

        except (json.JSONDecodeError, Exception):

            return {"tasks": []}



    async def _analyze_task_dependencies(self, transcript: str) -> Dict:

        """Analyze dependencies between tasks"""

        if not transcript or not transcript.strip():
            return {"dependencies": [], "critical_path": [], "parallel_tracks": []}

        system_prompt = """You are an expert at identifying task dependencies and relationships.

        Analyze the discussion to understand which tasks depend on others."""



        prompt = f"""

        Analyze task dependencies in this meeting discussion:



        Transcript:

        {transcript}



        Identify:

        - Which tasks must be completed before others can start

        - Which tasks can be done in parallel

        - Which tasks are blocking others



        Return JSON with dependencies:

        {{

            "dependencies": [

                {{

                    "task": "Task that depends on something",

                    "depends_on": ["prerequisite task 1", "prerequisite task 2"],

                    "dependency_type": "blocking|soft|parallel"

                }}

            ],

            "critical_path": ["task1", "task2", "task3"],

            "parallel_tracks": [["task_a", "task_b"], ["task_c", "task_d"]]

        }}

        """



        try:
            response = await self.ai_processor.call_ollama(prompt, system_prompt)

            if not response or not response.strip():
                return {"dependencies": [], "critical_path": [], "parallel_tracks": []}

            result = json.loads(response)

            # Validate result structure and provide defaults
            if not isinstance(result, dict):
                return {"dependencies": [], "critical_path": [], "parallel_tracks": []}

            # Ensure all required fields exist
            result.setdefault("dependencies", [])
            result.setdefault("critical_path", [])
            result.setdefault("parallel_tracks", [])

            return result

        except (json.JSONDecodeError, Exception):

            return {"dependencies": [], "critical_path": [], "parallel_tracks": []}



    async def _prioritize_tasks(self, transcript: str) -> Dict:

        """Analyze task priorities based on discussion"""

        if not transcript or not transcript.strip():
            return {"task_priorities": []}

        system_prompt = """You are an expert at determining task priorities based on meeting discussions.

        Analyze urgency, importance, and business impact mentioned in the discussion."""



        prompt = f"""

        Determine task priorities based on this meeting discussion:



        Transcript:

        {transcript}



        Consider:

        - Urgency expressed by participants

        - Business impact mentioned

        - Deadlines discussed

        - Stakeholder concerns



        Return JSON with priorities:

        {{

            "task_priorities": [

                {{

                    "task_reference": "Task description or key phrase",

                    "priority": "high|medium|low",

                    "urgency_score": 0.8,

                    "importance_score": 0.9,

                    "business_impact": "high|medium|low",

                    "reasoning": "Why this priority was assigned"

                }}

            ]

        }}

        """



        try:
            response = await self.ai_processor.call_ollama(prompt, system_prompt)

            if not response or not response.strip():
                return {"task_priorities": []}

            result = json.loads(response)

            # Validate result structure
            if not isinstance(result, dict):
                return {"task_priorities": []}

            if "task_priorities" not in result:
                result["task_priorities"] = []

            return result

        except (json.JSONDecodeError, Exception):

            return {"task_priorities": []}



    def _merge_tasks(self, explicit_tasks: Dict, implicit_tasks: Dict) -> List[Dict]:

        """Merge explicit and implicit tasks, removing duplicates"""

        all_tasks = []

        # Handle null inputs
        if not isinstance(explicit_tasks, dict):
            explicit_tasks = {"tasks": []}
        if not isinstance(implicit_tasks, dict):
            implicit_tasks = {"tasks": []}



        # Add explicit tasks

        for task in explicit_tasks.get("tasks", []):
            if task and isinstance(task, dict):
                task["source"] = "explicit"

                all_tasks.append(task)



        # Add implicit tasks, checking for duplicates

        for implicit_task in implicit_tasks.get("tasks", []):
            if not implicit_task or not isinstance(implicit_task, dict):
                continue

            implicit_task["source"] = "implicit"



            # Simple duplicate detection based on title similarity

            is_duplicate = False

            task_title = implicit_task.get("title", "")
            if not task_title:
                continue

            for existing_task in all_tasks:
                existing_title = existing_task.get("title", "") if existing_task else ""
                if existing_title and self._tasks_similar(task_title, existing_title):

                    is_duplicate = True

                    break



            if not is_duplicate:

                all_tasks.append(implicit_task)



        return all_tasks



    def _tasks_similar(self, title1: str, title2: str, threshold: float = 0.7) -> bool:

        """Simple similarity check for task titles"""

        # Handle null/empty inputs
        if not title1 or not title2:
            return False

        try:
            # Convert to lowercase and split into words

            words1 = set(title1.lower().split())

            words2 = set(title2.lower().split())



            # Calculate Jaccard similarity

            intersection = len(words1.intersection(words2))

            union = len(words1.union(words2))



            if union == 0:

                return False



            similarity = intersection / union

            return similarity >= threshold
        except (AttributeError, TypeError):
            return False



    def _apply_task_metadata(self, tasks: List[Dict], dependencies: Dict, priorities: Dict) -> List[Dict]:

        """Apply dependency and priority metadata to tasks"""



        # Handle null inputs
        if not tasks or not isinstance(tasks, list):
            return []

        if not isinstance(dependencies, dict):
            dependencies = {"dependencies": [], "critical_path": [], "parallel_tracks": []}

        if not isinstance(priorities, dict):
            priorities = {"task_priorities": []}

        # Create priority lookup

        priority_lookup = {}

        for priority_info in priorities.get("task_priorities", []):
            if isinstance(priority_info, dict) and priority_info.get("task_reference"):
                priority_lookup[priority_info["task_reference"]] = priority_info



        # Apply metadata to each task
        validated_tasks = []

        for task in tasks:
            if not task or not isinstance(task, dict):
                continue

            task_title = task.get("title", "")
            if not task_title:
                continue



            # Apply priority if found

            for ref, priority_info in priority_lookup.items():
                if ref and task_title and (ref.lower() in task_title.lower() or task_title.lower() in ref.lower()):

                    task["priority"] = priority_info.get("priority", "medium")

                    task["urgency_score"] = priority_info.get("urgency_score", 0.5)

                    task["importance_score"] = priority_info.get("importance_score", 0.5)

                    task["business_impact"] = priority_info.get("business_impact", "medium")

                    break



            # Set defaults if not found

            if "priority" not in task:

                task["priority"] = "medium"

                task["urgency_score"] = 0.5

                task["importance_score"] = 0.5

                task["business_impact"] = "medium"



            # Apply dependencies

            task["dependencies"] = []
            task["dependency_type"] = "none"

            for dep in dependencies.get("dependencies", []):
                if isinstance(dep, dict) and dep.get("task") and task_title:
                    if dep["task"].lower() in task_title.lower():

                        task["dependencies"] = dep.get("depends_on", [])

                        task["dependency_type"] = dep.get("dependency_type", "none")

                        break



            # Add standard fields if missing

            if "assignee" not in task:

                task["assignee"] = "Unassigned"

            if "due_date" not in task:

                task["due_date"] = None

            if "status" not in task:

                task["status"] = "pending"



            # Generate unique ID if not present

            if "id" not in task:
                try:
                    task["id"] = f"task_{abs(hash(task_title)) % 10000}"
                except:
                    task["id"] = f"task_{len(validated_tasks) + 1}"

            validated_tasks.append(task)



        return validated_tasks
