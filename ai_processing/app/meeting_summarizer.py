import json
import asyncio
from typing import Dict, List
from datetime import datetime

class MeetingSummarizer:

    def __init__(self, ai_processor):

        self.ai_processor = ai_processor

    

    async def generate_comprehensive_summary(self, transcript: str, meeting_context: Dict = None) -> Dict:

        """Generate comprehensive meeting summary with multiple sections"""

        

        if not meeting_context:

            meeting_context = {}

        

        # Run multiple summarization tasks in parallel

        tasks = [

            self._generate_executive_summary(transcript, meeting_context),

            self._extract_key_decisions(transcript),

            self._identify_discussion_topics(transcript),

            self._extract_next_steps(transcript),

            self._identify_participants_and_roles(transcript)

        ]

        

        results = await asyncio.gather(*tasks)

        

        executive_summary, key_decisions, discussion_topics, next_steps, participants = results

        

        return {

            "meeting_metadata": {

                "title": meeting_context.get("title", "Meeting Summary"),

                "date": meeting_context.get("date", datetime.now().isoformat()),

                "duration": meeting_context.get("duration", "Unknown"),

                "platform": meeting_context.get("platform", "Unknown")

            },

            "executive_summary": executive_summary,

            "key_decisions": key_decisions,

            "discussion_topics": discussion_topics,

            "next_steps": next_steps,

            "participants": participants,

            "summary_generated_at": datetime.now().isoformat()

        }

    

    async def _generate_executive_summary(self, transcript: str, context: Dict) -> Dict:

        """Generate high-level executive summary"""

        system_prompt = """You are an executive assistant creating concise, high-level summaries for leadership.

        Focus on outcomes, decisions, and business impact. Keep it brief but comprehensive."""

        

        prompt = f"""

        Create an executive summary of this meeting:

        

        Meeting Context: {json.dumps(context, indent=2)}

        

        Transcript:

        {transcript}

        

        Provide a JSON response with:

        {{

            "overview": "2-3 sentence high-level summary",

            "key_outcomes": ["outcome 1", "outcome 2"],

            "business_impact": "How this affects business goals",

            "urgency_level": "low|medium|high",

            "follow_up_required": true/false

        }}

        """

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {

                "overview": response[:200] + "..." if len(response) > 200 else response,

                "key_outcomes": [],

                "business_impact": "Unable to determine",

                "urgency_level": "medium",

                "follow_up_required": True

            }

    

    async def _extract_key_decisions(self, transcript: str) -> Dict:

        """Extract key decisions made during the meeting"""

        system_prompt = """You are an expert at identifying decisions made in meetings.

        Look for definitive statements, agreements, approvals, and commitments."""

        

        prompt = f"""

        Extract all key decisions made in this meeting:

        

        Transcript:

        {transcript}

        

        Return JSON with decisions:

        {{

            "decisions": [

                {{

                    "decision": "What was decided",

                    "rationale": "Why this decision was made",

                    "impact": "Who/what this affects",

                    "timeline": "When this takes effect",

                    "confidence": 0.9

                }}

            ],

            "total_decisions": 3,

            "consensus_level": "unanimous|majority|split"

        }}

        """

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {

                "decisions": [],

                "total_decisions": 0,

                "consensus_level": "unknown"

            }

    

    async def _identify_discussion_topics(self, transcript: str) -> Dict:

        """Identify and categorize discussion topics"""

        system_prompt = """You are an expert at categorizing meeting discussions.

        Identify main topics, subtopics, and the depth of discussion for each."""

        

        prompt = f"""

        Identify and categorize all discussion topics in this meeting:

        

        Transcript:

        {transcript}

        

        Return JSON with topics:

        {{

            "topics": [

                {{

                    "topic": "Main topic name",

                    "category": "technical|business|process|planning|review",

                    "discussion_depth": "brief|moderate|extensive",

                    "resolution_status": "resolved|ongoing|deferred",

                    "key_points": ["point 1", "point 2"]

                }}

            ],

            "primary_focus": "What was the main focus",

            "topic_distribution": {{"technical": 40, "business": 60}}

        }}

        """

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {

                "topics": [],

                "primary_focus": "Unable to determine",

                "topic_distribution": {}

            }

    

    async def _extract_next_steps(self, transcript: str) -> Dict:

        """Extract next steps and follow-up actions"""

        system_prompt = """You are an expert at identifying follow-up actions and next steps from meetings.

        Look for commitments, assignments, and planned activities."""

        

        prompt = f"""

        Extract all next steps and follow-up actions from this meeting:

        

        Transcript:

        {transcript}

        

        Return JSON with next steps:

        {{

            "next_steps": [

                {{

                    "action": "What needs to be done",

                    "owner": "Who is responsible",

                    "deadline": "When it's due",

                    "priority": "high|medium|low",

                    "dependencies": ["what this depends on"]

                }}

            ],

            "next_meeting": {{

                "scheduled": true/false,

                "date": "date if mentioned",

                "purpose": "why meeting again"

            }},

            "total_actions": 5

        }}

        """

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {

                "next_steps": [],

                "next_meeting": {"scheduled": False, "date": "", "purpose": ""},

                "total_actions": 0

            }

    

    async def _identify_participants_and_roles(self, transcript: str) -> Dict:

        """Identify participants and their roles in the meeting"""

        system_prompt = """You are an expert at identifying meeting participants and their roles.

        Analyze who spoke, their apparent roles, and their level of participation."""

        

        prompt = f"""

        Identify participants and their roles in this meeting:

        

        Transcript:

        {transcript}

        

        Return JSON with participants:

        {{

            "participants": [

                {{

                    "name": "Participant name or role",

                    "role": "Their apparent role/title",

                    "participation_level": "high|medium|low",

                    "key_contributions": ["what they contributed"]

                }}

            ],

            "meeting_leader": "Who led the meeting",

            "total_participants": 4,

            "participation_balance": "balanced|dominated|mixed"

        }}

        """

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {

                "participants": [],

                "meeting_leader": "Unknown",

                "total_participants": 0,

                "participation_balance": "unknown"

            }
