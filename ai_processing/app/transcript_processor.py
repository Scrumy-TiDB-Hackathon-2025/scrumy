from pydantic import BaseModel
from typing import List, Tuple, Literal, Optional, Dict
import logging
import os
from dotenv import load_dotenv
from app.db import DatabaseManager
from app.database_interface import DatabaseFactory
import asyncio
import json
import openai
import groq
from ollama import AsyncClient
import httpx

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file

# Change this line
db = DatabaseFactory.create_database(db_type='tidb')

class Block(BaseModel):
    """Represents a block of content in a section.

    Block types must align with frontend rendering capabilities:
    - 'text': Plain text content
    - 'bullet': Bulleted list item
    - 'heading1': Large section heading
    - 'heading2': Medium section heading

    Colors currently supported:
    - 'gray': Gray text color
    - '' or any other value: Default text color
    """
    id: str
    type: Literal['bullet', 'heading1', 'heading2', 'text']
    content: str
    color: str  # Frontend currently only uses 'gray' or default

class Section(BaseModel):
    """Represents a section in the meeting summary"""
    title: str
    blocks: List[Block]

class MeetingNotes(BaseModel):
    """Represents the meeting notes"""
    meeting_name: str
    sections: List[Section]

class People(BaseModel):
    """Represents the people in the meeting. Always have this part in the output. Title - Person Name (Role, Details)"""
    title: str
    blocks: List[Block]

class SummaryResponse(BaseModel):
    """Represents the meeting summary response based on a section of the transcript"""
    MeetingName : str
    People : People
    SessionSummary : Section
    CriticalDeadlines: Section
    KeyItemsDecisions: Section
    ImmediateActionItems: Section
    NextSteps: Section
    MeetingNotes: MeetingNotes

# --- Main Class Used by main.py ---

class TranscriptProcessor:
    """Handles the processing of meeting transcripts using AI models."""
    def __init__(self):
        """Initialize the transcript processor."""
        logger.info("TranscriptProcessor initialized.")
        # Change this line
        self.db = DatabaseFactory.create_database(db_type='tidb')
        self.active_clients = []  # Track active client sessions

    async def process_transcript(self, text: str, model: str, model_name: str, chunk_size: int = 5000, overlap: int = 1000, custom_prompt: str = "", participants: Optional[List[Dict]] = None) -> Tuple[int, List[str]]:
        """
        Process transcript text into chunks and generate structured summaries for each chunk using an AI model.

        Args:
            text: The transcript text.
            model: The AI model provider ('claude', 'ollama', 'groq', 'openai').
            model_name: The specific model name.
            chunk_size: The size of each text chunk.
            overlap: The overlap between consecutive chunks.
            custom_prompt: A custom prompt to use for the AI model.

        Returns:
            A tuple containing:
            - The number of chunks processed.
            - A list of JSON strings, where each string is the summary of a chunk.
        """

        logger.info(f"Processing transcript (length {len(text)}) with model provider={model}, model_name={model_name}, chunk_size={chunk_size}, overlap={overlap}, participants={len(participants or [])}")

        all_json_data = []

        try:
            # Adjust chunk size for different models
            if model == "ollama":
                if model_name.lower().startswith("phi4") or model_name.lower().startswith("llama"):
                    chunk_size = 10000
                    overlap = 1000
                else:
                    chunk_size = 30000
                    overlap = 1000

            # Split transcript into chunks
            step = chunk_size - overlap
            if step <= 0:
                logger.warning(f"Overlap ({overlap}) >= chunk_size ({chunk_size}). Adjusting overlap.")
                overlap = max(0, chunk_size - 100)
                step = chunk_size - overlap

            chunks = [text[i:i+chunk_size] for i in range(0, len(text), step)]
            num_chunks = len(chunks)
            logger.info(f"Split transcript into {num_chunks} chunks.")

            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{num_chunks}...")
                try:
                    # Create the prompt with participant context
                    prompt = self._create_prompt(chunk, custom_prompt, participants)

                    # Process based on model provider
                    if model == "claude":
                        response_text = await self._process_claude(model_name, prompt)
                    elif model == "openai":
                        response_text = await self._process_openai(model_name, prompt)
                    elif model == "groq":
                        response_text = await self._process_groq(model_name, prompt)
                    elif model == "ollama":
                        response_text = await self._process_ollama(model_name, prompt)
                    else:
                        logger.error(f"Unsupported model provider: {model}")
                        continue

                    # Parse and validate the response
                    try:
                        # Try to parse as JSON first
                        json_data = json.loads(response_text)
                        # Validate the structure by creating a SummaryResponse
                        summary = SummaryResponse.model_validate(json_data)
                        chunk_summary_json = summary.model_dump_json()
                        all_json_data.append(chunk_summary_json)
                        logger.info(f"Successfully generated summary for chunk {i+1}.")
                    except (json.JSONDecodeError, Exception) as e:
                        logger.error(f"Failed to parse response as JSON for chunk {i+1}: {e}")
                        # Create a fallback summary
                        fallback_summary = self._create_fallback_summary(response_text, participants)
                        all_json_data.append(fallback_summary.model_dump_json())

                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i+1}: {chunk_error}", exc_info=True)

            logger.info(f"Finished processing all {num_chunks} chunks.")
            return num_chunks, all_json_data

        except Exception as e:
            logger.error(f"Error during transcript processing: {str(e)}", exc_info=True)
            raise

    def _create_prompt(self, chunk: str, custom_prompt: str, participants: Optional[List[Dict]] = None) -> str:
        """Create the prompt for AI processing with participant context."""
        participant_context = ""
        if participants:
            participant_names = [p.get('name', 'Unknown') for p in participants]
            participant_info = []
            for p in participants:
                role = "Host" if p.get('is_host', False) else "Participant"
                participant_info.append(f"- {p.get('name', 'Unknown')} ({role})")
            participant_context = f"""
MEETING PARTICIPANTS (detected by system):
{chr(10).join(participant_info)}
Total participants: {len(participants)}

Use these participant names when identifying speakers in the transcript. If you see these names mentioned or speaking, use the exact names from this list.
"""

        return f"""Given the following meeting transcript chunk, extract the relevant information according to the required JSON structure. If a specific section (like Critical Deadlines) has no relevant information in this chunk, return an empty list for its 'blocks'. Ensure the output is only valid JSON data.

{participant_context}

IMPORTANT: Block types must be one of: 'text', 'bullet', 'heading1', 'heading2'
- Use 'text' for regular paragraphs
- Use 'bullet' for list items
- Use 'heading1' for major headings
- Use 'heading2' for subheadings

For the color field, use 'gray' for less important content or '' (empty string) for default.

Required JSON structure:
{{
  "MeetingName": "string",
  "People": {{
    "title": "People",
    "blocks": [{{ "id": "unique_id", "type": "text|bullet|heading1|heading2", "content": "content", "color": "gray|" }}]
  }},
  "SessionSummary": {{
    "title": "Session Summary",
    "blocks": [{{ "id": "unique_id", "type": "text|bullet|heading1|heading2", "content": "content", "color": "gray|" }}]
  }},
  "CriticalDeadlines": {{
    "title": "Critical Deadlines",
    "blocks": [{{ "id": "unique_id", "type": "text|bullet|heading1|heading2", "content": "content", "color": "gray|" }}]
  }},
  "KeyItemsDecisions": {{
    "title": "Key Items & Decisions",
    "blocks": [{{ "id": "unique_id", "type": "text|bullet|heading1|heading2", "content": "content", "color": "gray|" }}]
  }},
  "ImmediateActionItems": {{
    "title": "Immediate Action Items",
    "blocks": [{{ "id": "unique_id", "type": "text|bullet|heading1|heading2", "content": "content", "color": "gray|" }}]
  }},
  "NextSteps": {{
    "title": "Next Steps",
    "blocks": [{{ "id": "unique_id", "type": "text|bullet|heading1|heading2", "content": "content", "color": "gray|" }}]
  }},
  "MeetingNotes": {{
    "meeting_name": "string",
    "sections": [{{ "title": "section_title", "blocks": [{{ "id": "unique_id", "type": "text|bullet|heading1|heading2", "content": "content", "color": "gray|" }}] }}]
  }}
}}

Transcript Chunk:
---
{chunk}
---

Please capture all relevant action items. Transcription can have spelling mistakes, correct them if required. Context is important.

While generating the summary, please add the following context:
---
{custom_prompt}
---

Respond ONLY with valid JSON data, no additional text or formatting."""

    async def _process_claude(self, model_name: str, prompt: str) -> str:
        """Process using Claude/Anthropic API."""
        api_key = await self.db.get_api_key("claude")
        if not api_key:
            raise ValueError("Claude API key not found")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model_name,
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]

    async def _process_openai(self, model_name: str, prompt: str) -> str:
        """Process using OpenAI API."""
        api_key = await self.db.get_api_key("openai")
        if not api_key:
            raise ValueError("OpenAI API key not found")

        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1
        )
        return response.choices[0].message.content

    async def _process_groq(self, model_name: str, prompt: str) -> str:
        """Process using Groq API."""
        api_key = await self.db.get_api_key("groq")
        if not api_key:
            raise ValueError("Groq API key not found")

        client = groq.AsyncGroq(api_key=api_key)
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1
        )
        return response.choices[0].message.content

    async def _process_ollama(self, model_name: str, prompt: str) -> str:
        """Process using Ollama."""
        ollama_host = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
        client = AsyncClient(host=ollama_host)
        self.active_clients.append(client)

        try:
            response = await client.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                format="json"
            )
            return response['message']['content']
        finally:
            if client in self.active_clients:
                self.active_clients.remove(client)

    def _create_fallback_summary(self, text: str, participants: Optional[List[Dict]] = None) -> SummaryResponse:
        """Create a fallback summary when JSON parsing fails."""
        # Create participant blocks from real participant data if available
        participant_blocks = []
        if participants:
            for p in participants:
                role = "Host" if p.get('is_host', False) else "Participant"
                participant_blocks.append(
                    Block(id=f"p_{p.get('id', 'unknown')}",
                          type="bullet",
                          content=f"{p.get('name', 'Unknown')} ({role})",
                          color="")
                )
        else:
            participant_blocks = [Block(id="p1", type="text", content="Unable to extract participant information", color="gray")]

        return SummaryResponse(
            MeetingName="Meeting Summary",
            People=People(
                title="People",
                blocks=participant_blocks
            ),
            SessionSummary=Section(
                title="Session Summary",
                blocks=[Block(id="s1", type="text", content=text[:500] + "..." if len(text) > 500 else text, color="")]
            ),
            CriticalDeadlines=Section(title="Critical Deadlines", blocks=[]),
            KeyItemsDecisions=Section(title="Key Items & Decisions", blocks=[]),
            ImmediateActionItems=Section(title="Immediate Action Items", blocks=[]),
            NextSteps=Section(title="Next Steps", blocks=[]),
            MeetingNotes=MeetingNotes(
                meeting_name="Meeting Summary",
                sections=[Section(
                    title="Raw Content",
                    blocks=[Block(id="r1", type="text", content=text, color="gray")]
                )]
            )
        )

    def cleanup(self):
        """Clean up resources used by the TranscriptProcessor."""
        logger.info("Cleaning up TranscriptProcessor resources")
        try:
            # Close database connections if any
            if hasattr(self, 'db') and self.db is not None:
                logger.info("Database connection cleanup (using context managers)")

            # Cancel any active client sessions
            if hasattr(self, 'active_clients') and self.active_clients:
                logger.info(f"Terminating {len(self.active_clients)} active client sessions")
                for client in self.active_clients:
                    try:
                        if hasattr(client, '_client') and hasattr(client._client, 'close'):
                            asyncio.create_task(client._client.aclose())
                    except Exception as client_error:
                        logger.error(f"Error closing client: {client_error}", exc_info=True)
                self.active_clients.clear()
                logger.info("All client sessions terminated")
        except Exception as e:
            logger.error(f"Error during TranscriptProcessor cleanup: {str(e)}", exc_info=True)