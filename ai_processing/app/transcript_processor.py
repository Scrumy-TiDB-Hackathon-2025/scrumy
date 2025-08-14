from pydantic import BaseModel
from typing import List, Tuple
import logging
import json

logger = logging.getLogger(__name__)

class Block(BaseModel):
    """Represents a block of content in a section"""
    id: str
    type: str
    content: str
    color: str

class Section(BaseModel):
    """Represents a section in the meeting summary"""
    title: str
    blocks: List[Block]

class SummaryResponse(BaseModel):
    """Represents the meeting summary response"""
    MeetingName: str
    SectionSummary: Section
    CriticalDeadlines: Section
    KeyItemsDecisions: Section
    ImmediateActionItems: Section
    NextSteps: Section
    OtherImportantPoints: Section
    ClosingRemarks: Section

class TranscriptProcessor:
    """Simplified transcript processor for testing"""
    
    def __init__(self):
        logger.info("TranscriptProcessor initialized (simplified version)")
    
    async def process_transcript(self, text: str, model: str, model_name: str, chunk_size: int = 5000, overlap: int = 1000) -> Tuple[int, List[str]]:
        """Mock processing that returns fake structured data"""
        logger.info(f"Processing transcript (length {len(text)}) - MOCK VERSION")
        
        # Create mock structured response
        mock_summary = SummaryResponse(
            MeetingName="Test Meeting",
            SectionSummary=Section(title="Section Summary", blocks=[]),
            CriticalDeadlines=Section(title="Critical Deadlines", blocks=[]),
            KeyItemsDecisions=Section(title="Key Items & Decisions", blocks=[]),
            ImmediateActionItems=Section(title="Immediate Action Items", blocks=[]),
            NextSteps=Section(title="Next Steps", blocks=[]),
            OtherImportantPoints=Section(title="Other Important Points", blocks=[]),
            ClosingRemarks=Section(title="Closing Remarks", blocks=[])
        )
        
        # Convert to JSON string
        json_result = mock_summary.model_dump_json()
        
        return 1, [json_result]
    
    def cleanup(self):
        pass
