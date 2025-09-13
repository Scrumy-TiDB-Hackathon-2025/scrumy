import json
from typing import Dict, List
from datetime import datetime
import re
import asyncio
import logging

logger = logging.getLogger(__name__)

class TaskExtractor:

    def __init__(self, ai_processor):

        self.ai_processor = ai_processor



    async def extract_comprehensive_tasks(self, transcript: str, meeting_context: Dict = None) -> Dict:
        """
        UPDATED: Use unified single API call instead of multiple strategies
        """

        if not transcript or not transcript.strip():
            return self._get_empty_result("No transcript provided")

        # Use unified extraction method
        logger.info("Starting unified task extraction (single API call)")

        try:
            result = await self.extract_tasks_unified(transcript, meeting_context)

            logger.info(f"Unified extraction completed: {len(result.get('tasks', []))} tasks found")
            return result

        except Exception as e:
            logger.error(f"Unified extraction failed: {e}")
            return self._get_empty_result(error=str(e))

    async def extract_tasks_unified(self, transcript: str, meeting_context: Dict = None) -> Dict:
        """
        UNIFIED task extraction using single Groq API call
        Replaces 4 separate API calls with 1 comprehensive call
        """

        if not transcript or not transcript.strip():
            return self._get_empty_result()

        # Build comprehensive system prompt
        system_prompt = """You are an expert at analyzing meeting transcripts and extracting actionable tasks.

        Your analysis must include ALL of the following:
        1. EXPLICIT TASKS - Direct action items clearly mentioned
        2. IMPLICIT TASKS - Tasks that are implied but not directly stated
        3. TASK DEPENDENCIES - Relationships and dependencies between tasks
        4. TASK PRIORITIES - Urgency and importance levels

        Respond with valid JSON only, no additional text."""

        # Build comprehensive user prompt with grammar focus
        user_prompt = f"""
        Analyze this meeting transcript and extract clear, well-written tasks:

        TRANSCRIPT:
        {transcript}

        MEETING CONTEXT:
        {json.dumps(meeting_context or {}, indent=2)}

        CRITICAL: The transcript may contain speech recognition errors. You MUST:
        - Correct obvious grammar and spelling mistakes
        - Create clear, professional task titles
        - Fix garbled words using context clues
        - Write tasks as proper action items

        EXAMPLES OF CORRECTIONS:
        - "Use dedication module by Friday" → "Complete user authentication module by Friday"
        - "Right unites for P process" → "Write unit tests for payment processing"
        - "Create user resolution from I signed" → "Create user registration form"
        - "Finalize API paper documentation" → "Finalize API documentation"

        ANALYSIS REQUIREMENTS:

        1. EXPLICIT TASKS - Find direct action items and CORRECT the language:
           - Fix speech recognition errors
           - Create clear, actionable titles
           - Ensure proper grammar and spelling

        2. IMPLICIT TASKS - Identify implied tasks with CLEAR descriptions:
           - Problems mentioned without solutions
           - Requirements that need follow-up
           - Decisions that require implementation

        3. TASK PRIORITIES - Determine urgency:
           - High: Blocking issues, urgent deadlines
           - Medium: Important but not urgent
           - Low: Nice-to-have improvements

        Return comprehensive JSON:
        {{
            "tasks": [
                {{
                    "id": "task_1",
                    "title": "Clear, grammatically correct task title (fix any speech errors)",
                    "description": "Detailed description with proper grammar",
                    "assignee": "Person assigned or 'Unassigned'",
                    "due_date": "YYYY-MM-DD or null",
                    "priority": "high|medium|low",
                    "category": "explicit|implicit",
                    "dependencies": ["task_2", "task_3"],
                    "context": "Relevant transcript context (corrected for grammar)",
                    "confidence": 0.9
                }}
            ],
            "task_summary": {{
                "total_tasks": 0,
                "explicit_tasks": 0,
                "implicit_tasks": 0,
                "high_priority": 0,
                "with_deadlines": 0,
                "with_dependencies": 0
            }},
            "dependencies": [
                {{
                    "task": "task_1",
                    "depends_on": ["task_2"],
                    "dependency_type": "blocking|sequential|parallel"
                }}
            ],
            "extraction_metadata": {{
                "model_used": "unified_extraction",
                "confidence_score": 0.85,
                "processing_method": "single_api_call",
                "extracted_at": "{datetime.now().isoformat()}"
            }}
        }}
        """

        try:
            # Single comprehensive API call
            response = await self.ai_processor.call_ollama(user_prompt, system_prompt)

            if not response or not response.strip():
                return self._get_empty_result()

            # Parse and validate response
            result = self._parse_unified_response(response)

            # Apply post-processing
            final_tasks = self._post_process_unified_tasks(result, meeting_context)

            return {
                "tasks": final_tasks,
                "task_summary": result.get("task_summary", {}),
                "extraction_metadata": result.get("extraction_metadata", {})
            }

        except Exception as e:
            logger.error(f"Unified task extraction failed: {e}")
            return self._get_empty_result(error=str(e))

    def _parse_unified_response(self, response: str) -> Dict:
        """Parse and validate unified API response"""
        try:
            # Extract JSON from response
            json_str = self._extract_json_from_response(response)
            if not json_str:
                return {}

            result = json.loads(json_str)

            # Validate structure
            if not isinstance(result, dict) or "tasks" not in result:
                return {}

            # Validate tasks
            validated_tasks = []
            for task in result.get("tasks", []):
                if self._validate_task_structure(task):
                    validated_tasks.append(task)

            result["tasks"] = validated_tasks
            return result

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse unified response: {e}")
            return {}

    def _validate_task_structure(self, task: Dict) -> bool:
        """Validate individual task structure"""
        required_fields = ["id", "title", "description", "priority"]
        return (
            isinstance(task, dict) and
            all(field in task for field in required_fields) and
            task.get("title", "").strip() != ""
        )

    def _post_process_unified_tasks(self, result: Dict, meeting_context: Dict = None) -> List[Dict]:
        """Post-process unified extraction results"""
        tasks = result.get("tasks", [])

        # Apply meeting context
        if meeting_context:
            for task in tasks:
                task["meeting_id"] = meeting_context.get("meeting_id", "unknown")
                task["meeting_title"] = meeting_context.get("title", "Meeting")

        # Apply dependency logic
        dependencies = result.get("dependencies", [])
        for task in tasks:
            task["dependencies"] = self._resolve_dependencies(task, dependencies)

        return tasks

    def _resolve_dependencies(self, task: Dict, dependencies: List[Dict]) -> List[str]:
        """Resolve task dependencies"""
        task_dependencies = []
        for dep in dependencies:
            if dep.get("task") == task.get("id"):
                task_dependencies.extend(dep.get("depends_on", []))
        return task_dependencies

    def _get_empty_result(self, error: str = None) -> Dict:
        """Return empty result structure"""
        return {
            "tasks": [],
            "task_summary": {
                "total_tasks": 0,
                "explicit_tasks": 0,
                "implicit_tasks": 0,
                "high_priority": 0,
                "with_deadlines": 0,
                "with_dependencies": 0
            },
            "extraction_metadata": {
                "error": error,
                "extracted_at": datetime.now().isoformat(),
                "processing_method": "unified_single_call"
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

            # Extract JSON from response (AI might include extra text)
            json_str = self._extract_json_from_response(response)
            if not json_str:
                return {"tasks": []}

            result = json.loads(json_str)

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

            # Extract JSON from response (AI might include extra text)
            json_str = self._extract_json_from_response(response)
            if not json_str:
                return {"tasks": []}

            result = json.loads(json_str)

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

            # Extract JSON from response (AI might include extra text)
            json_str = self._extract_json_from_response(response)
            if not json_str:
                return {"dependencies": [], "critical_path": [], "parallel_tracks": []}

            result = json.loads(json_str)

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

            # Extract JSON from response (AI might include extra text)
            json_str = self._extract_json_from_response(response)
            if not json_str:
                return {"task_priorities": []}

            result = json.loads(json_str)

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



    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from AI response that might contain extra text"""
        if not response:
            return ""

        # Look for JSON object starting with { and ending with }
        start_idx = response.find('{')
        if start_idx == -1:
            return ""

        # Find the matching closing brace
        brace_count = 0
        end_idx = -1

        for i in range(start_idx, len(response)):
            if response[i] == '{':
                brace_count += 1
            elif response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break

        if end_idx == -1:
            return ""

        return response[start_idx:end_idx + 1]

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
