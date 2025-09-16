import asyncio
from typing import Dict, List
from app.ai_processor import AIProcessor
from app.speaker_identifier import SpeakerIdentifier
from app.meeting_summarizer import MeetingSummarizer
from app.task_extractor import TaskExtractor
from app.integration_bridge import create_integration_bridge, DEFAULT_INTEGRATION_CONFIG
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IntegratedAIProcessor:

    def __init__(self, integration_config: Dict = None):

        self.ai_processor = AIProcessor()

        self.speaker_identifier = SpeakerIdentifier(self.ai_processor)

        self.meeting_summarizer = MeetingSummarizer(self.ai_processor)

        self.task_extractor = TaskExtractor(self.ai_processor)
        
        # Initialize integration bridge
        config = integration_config or DEFAULT_INTEGRATION_CONFIG
        self.integration_bridge = create_integration_bridge(config)
        
        logger.info(f"IntegratedAIProcessor initialized with integration {'enabled' if self.integration_bridge.enabled else 'disabled'}")

    

    async def process_complete_meeting(self, transcript: str, meeting_context: Dict = None) -> Dict:

        """Process a complete meeting with all AI features and create tasks via integrations"""

        

        if not meeting_context:

            meeting_context = {}

        

        try:

            # Run all AI processing in parallel for efficiency

            tasks = [

                self.speaker_identifier.identify_speakers_advanced(transcript),

                self.meeting_summarizer.generate_comprehensive_summary(transcript, meeting_context),

                self.task_extractor.extract_comprehensive_tasks(transcript, meeting_context)

            ]

            

            speakers_result, summary_result, tasks_result = await asyncio.gather(*tasks)

            

            # Process integrations if tasks were extracted
            integration_results = None
            if tasks_result and isinstance(tasks_result, dict) and tasks_result.get("tasks"):
                logger.info(f"Processing {len(tasks_result['tasks'])} tasks for integration")
                integration_results = await self.integration_bridge.create_tasks_from_ai_results(
                    ai_tasks=tasks_result["tasks"],
                    meeting_context=meeting_context
                )
            else:
                logger.info("No tasks extracted, skipping integration")
                integration_results = {
                    "integration_enabled": self.integration_bridge.enabled,
                    "tasks_processed": 0,
                    "tasks_created": 0,
                    "reason": "No tasks extracted from meeting"
                }

            

            # Build comprehensive response
            response = {

                "status": "success",

                "meeting_id": meeting_context.get("meeting_id", f"meeting_{hash(transcript) % 10000}"),

                "processing_results": {

                    "speakers": speakers_result,

                    "summary": summary_result,

                    "tasks": tasks_result

                },

                "integration_results": integration_results,

                "metadata": {

                    "transcript_length": len(transcript),

                    "processing_time": "calculated_in_real_implementation",

                    "ai_model": self.ai_processor.model,

                    "processed_at": datetime.now().isoformat(),

                    "integration_enabled": self.integration_bridge.enabled

                }

            }
            
            # Send meeting summary notification if enabled
            if integration_results and integration_results.get("tasks_created", 0) > 0:
                summary_text = summary_result.get("executive_summary", "") if isinstance(summary_result, dict) else str(summary_result)
                await self.integration_bridge.send_meeting_summary_notification(
                    meeting_summary=summary_text,
                    tasks_created=integration_results["tasks_created"],
                    meeting_context=meeting_context
                )
            
            return response

            

        except Exception as e:
            logger.error(f"Error in process_complete_meeting: {e}")
            return {

                "status": "error",

                "error": str(e),

                "meeting_id": meeting_context.get("meeting_id", "unknown"),

                "processing_results": None,
                
                "integration_results": {
                    "integration_enabled": False,
                    "error": "Processing failed before integration"
                }

            }
