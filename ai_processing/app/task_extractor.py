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

        

        # Run multiple extraction strategies

        tasks = [

            self._extract_explicit_tasks(transcript),

            self._extract_implicit_tasks(transcript),

            self._analyze_task_dependencies(transcript),

            self._prioritize_tasks(transcript)

        ]

        

        results = await asyncio.gather(*tasks)

        explicit_tasks, implicit_tasks, dependencies, priorities = results

        

        # Merge and deduplicate tasks

        all_tasks = self._merge_tasks(explicit_tasks, implicit_tasks)

        

        # Apply dependencies and priorities

        final_tasks = self._apply_task_metadata(all_tasks, dependencies, priorities)

        

        return {

            "tasks": final_tasks,

            "task_summary": {

                "total_tasks": len(final_tasks),

                "high_priority": len([t for t in final_tasks if t.get("priority") == "high"]),

                "with_deadlines": len([t for t in final_tasks if t.get("due_date")]),

                "assigned": len([t for t in final_tasks if t.get("assignee") != "Unassigned"])

            },

            "extraction_metadata": {

                "explicit_tasks_found": len(explicit_tasks.get("tasks", [])),

                "implicit_tasks_found": len(implicit_tasks.get("tasks", [])),

                "extracted_at": datetime.now().isoformat()

            }

        }

    

    async def _extract_explicit_tasks(self, transcript: str) -> Dict:

        """Extract explicitly mentioned tasks and action items"""

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

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {"tasks": []}

    

    async def _extract_implicit_tasks(self, transcript: str) -> Dict:

        """Extract implicit tasks that weren't directly stated but are implied"""

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

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {"tasks": []}

    

    async def _analyze_task_dependencies(self, transcript: str) -> Dict:

        """Analyze dependencies between tasks"""

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

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {"dependencies": [], "critical_path": [], "parallel_tracks": []}

    

    async def _prioritize_tasks(self, transcript: str) -> Dict:

        """Analyze task priorities based on discussion"""

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

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {"task_priorities": []}

    

    def _merge_tasks(self, explicit_tasks: Dict, implicit_tasks: Dict) -> List[Dict]:

        """Merge explicit and implicit tasks, removing duplicates"""

        all_tasks = []

        

        # Add explicit tasks

        for task in explicit_tasks.get("tasks", []):

            task["source"] = "explicit"

            all_tasks.append(task)

        

        # Add implicit tasks, checking for duplicates

        for implicit_task in implicit_tasks.get("tasks", []):

            implicit_task["source"] = "implicit"

            

            # Simple duplicate detection based on title similarity

            is_duplicate = False

            for existing_task in all_tasks:

                if self._tasks_similar(implicit_task["title"], existing_task["title"]):

                    is_duplicate = True

                    break

            

            if not is_duplicate:

                all_tasks.append(implicit_task)

        

        return all_tasks

    

    def _tasks_similar(self, title1: str, title2: str, threshold: float = 0.7) -> bool:

        """Simple similarity check for task titles"""

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

    

    def _apply_task_metadata(self, tasks: List[Dict], dependencies: Dict, priorities: Dict) -> List[Dict]:

        """Apply dependency and priority metadata to tasks"""

        

        # Create priority lookup

        priority_lookup = {}

        for priority_info in priorities.get("task_priorities", []):

            priority_lookup[priority_info["task_reference"]] = priority_info

        

        # Apply metadata to each task

        for task in tasks:

            task_title = task.get("title", "")

            

            # Apply priority if found

            for ref, priority_info in priority_lookup.items():

                if ref.lower() in task_title.lower() or task_title.lower() in ref.lower():

                    task["priority"] = priority_info["priority"]

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

            for dep in dependencies.get("dependencies", []):

                if dep["task"].lower() in task_title.lower():

                    task["dependencies"] = dep["depends_on"]

                    task["dependency_type"] = dep["dependency_type"]

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

                task["id"] = f"task_{hash(task_title) % 10000}"

        

        return tasks
