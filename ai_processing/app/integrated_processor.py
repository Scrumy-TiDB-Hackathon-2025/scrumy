import asyncio
from typing import Dict, List
from app.ai_processor import AIProcessor
from app.speaker_identifier import SpeakerIdentifier
from app.meeting_summarizer import MeetingSummarizer
from app.task_extractor import TaskExtractor
from datetime import datetime

class IntegratedAIProcessor:

    def __init__(self):

        self.ai_processor = AIProcessor()

        self.speaker_identifier = SpeakerIdentifier(self.ai_processor)

        self.meeting_summarizer = MeetingSummarizer(self.ai_processor)

        self.task_extractor = TaskExtractor(self.ai_processor)

    

    async def process_complete_meeting(self, transcript: str, meeting_context: Dict = None) -> Dict:

        """Process a complete meeting with all AI features"""

        

        if not meeting_context:

            meeting_context = {}

        

        try:

            # Run all processing in parallel for efficiency

            tasks = [

                self.speaker_identifier.identify_speakers_advanced(transcript),

                self.meeting_summarizer.generate_comprehensive_summary(transcript, meeting_context),

                self.task_extractor.extract_comprehensive_tasks(transcript, meeting_context)

            ]

            

            speakers_result, summary_result, tasks_result = await asyncio.gather(*tasks)

            

            return {

                "status": "success",

                "meeting_id": meeting_context.get("meeting_id", f"meeting_{hash(transcript) % 10000}"),

                "processing_results": {

                    "speakers": speakers_result,

                    "summary": summary_result,

                    "tasks": tasks_result

                },

                "metadata": {

                    "transcript_length": len(transcript),

                    "processing_time": "calculated_in_real_implementation",

                    "ai_model": self.ai_processor.model,

                    "processed_at": datetime.now().isoformat()

                }

            }

            

        except Exception as e:

            return {

                "status": "error",

                "error": str(e),

                "meeting_id": meeting_context.get("meeting_id", "unknown"),

                "processing_results": None

            }
