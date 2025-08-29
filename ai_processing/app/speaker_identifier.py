import re
import json
from typing import Dict, List, Optional
import asyncio

class SpeakerIdentifier:

    def __init__(self, ai_processor):

        self.ai_processor = ai_processor



    async def identify_speakers_advanced(self, text: str, context: str = "", participant_names: Optional[List[str]] = None) -> Dict:

        """Advanced speaker identification with multiple strategies"""


        # Handle null/empty input
        if not text or not text.strip():
            return {
                "speakers": [],
                "confidence": 0.0,
                "total_speakers": 0,
                "identification_method": "empty_input",
                "error": "No text provided for speaker identification"
            }

        try:
            # Strategy 1: Look for explicit speaker labels

            explicit_speakers = self._extract_explicit_speakers(text, participant_names if participant_names is not None else [])



            if explicit_speakers:

                return await self._process_explicit_speakers(text, explicit_speakers, participant_names if participant_names is not None else [])



            # Strategy 2: Use AI to infer speakers with participant context

            return await self._ai_speaker_identification(text, context, participant_names if participant_names is not None else [])
        except Exception as e:
            return {
                "speakers": [],
                "confidence": 0.0,
                "total_speakers": 0,
                "identification_method": "error",
                "error": f"Speaker identification failed: {str(e)}"
            }



    def _extract_explicit_speakers(self, text: str, participant_names: Optional[List[str]] = None) -> List[str]:

        """Extract speakers from text with explicit labels like 'John: text'"""

        # Handle null or empty input
        if not text or not text.strip():
            return []

        patterns = [

            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:\s*(.+)$',  # John: text

            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+says?\s*:\s*(.+)$',  # John says: text

            r'^\[([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\]\s*(.+)$',  # [John] text

        ]



        speakers = set()

        lines = text.split('\n')



        for line in lines:

            line = line.strip()

            if not line:

                continue



            for pattern in patterns:

                try:
                    match = re.match(pattern, line, re.MULTILINE)

                    if match:

                        speaker_name = match.group(1).strip()

                        if speaker_name and len(speaker_name.split()) <= 3:  # Reasonable name length
                            # If we have participant names, prefer exact matches
                            if participant_names:
                                for participant in participant_names:
                                    if participant.lower() == speaker_name.lower() or speaker_name.lower() in participant.lower():
                                        speakers.add(participant)
                                        break
                                else:
                                    speakers.add(speaker_name)
                            else:
                                speakers.add(speaker_name)
                except (AttributeError, IndexError) as e:
                    # Skip malformed matches
                    continue



        return list(speakers)



    async def _process_explicit_speakers(self, text: str, speakers: List[str], participant_names: Optional[List[str]] = None) -> Dict:

        """Process text with known speakers"""

        if not text or not speakers:
            return {
                "speakers": [],
                "confidence": 0.0,
                "total_speakers": 0,
                "identification_method": "explicit_labels",
                "error": "No text or speakers provided"
            }

        speaker_segments = {}



        for speaker in speakers:
            if speaker:  # Ensure speaker is not None or empty
                speaker_segments[speaker] = []



        lines = text.split('\n')

        current_speaker = None



        for line in lines:

            line = line.strip()

            if not line:

                continue



            # Check if line starts with a speaker name

            speaker_found = None

            text_content = ""

            for speaker in speakers:
                if speaker and line.startswith(f"{speaker}:"):

                    speaker_found = speaker

                    text_content = line[len(speaker)+1:].strip()

                    break



            if speaker_found:

                current_speaker = speaker_found

                if text_content:

                    speaker_segments[current_speaker].append(text_content)

            elif current_speaker and current_speaker in speaker_segments:

                # Continue previous speaker's text

                speaker_segments[current_speaker].append(line)



        # Format response

        formatted_speakers = []

        for i, (speaker, segments) in enumerate(speaker_segments.items()):

            if segments:  # Only include speakers with content
                try:
                    formatted_speakers.append({

                        "id": f"speaker_{i+1}",

                        "name": speaker or "Unknown Speaker",

                        "segments": segments,

                        "total_words": sum(len(seg.split()) for seg in segments if seg)

                    })
                except (TypeError, AttributeError):
                    # Skip malformed speaker data
                    continue



        return {

            "speakers": formatted_speakers,

            "confidence": 0.95,  # High confidence for explicit speakers

            "total_speakers": len(formatted_speakers),

            "identification_method": "explicit_labels"

        }



    async def _ai_speaker_identification(self, text: str, context: str, participant_names: Optional[List[str]] = None) -> Dict:

        """Use AI to identify speakers when no explicit labels exist"""

        if not text or not text.strip():
            return {
                "speakers": [],
                "confidence": 0.0,
                "total_speakers": 0,
                "identification_method": "ai_inference",
                "error": "No text provided for AI analysis"
            }

        system_prompt = """You are an expert at identifying different speakers in meeting transcripts.

        Analyze speech patterns, vocabulary, topics discussed, and conversation flow to identify distinct speakers.

        Look for:

        - Changes in speaking style or vocabulary

        - Topic transitions that suggest different speakers

        - Questions vs answers patterns

        - Formal vs informal language

        - Technical vs non-technical discussions"""



        participant_context = ""
        if participant_names:
            participant_context = f"\n\nKnown participants in this meeting: {', '.join(participant_names)}\nTry to match speech segments to these participant names when possible."

        prompt = f"""

        Analyze this meeting transcript and identify distinct speakers based on speech patterns and context:



        Context: {context}{participant_context}



        Transcript:

        {text}



        Please identify speakers and assign segments to them. Return JSON in this exact format:

        {{

            "speakers": [

                {{

                    "id": "speaker_1",

                    "name": "Speaker 1 (estimated role/characteristics)",

                    "segments": ["exact text segment 1", "exact text segment 2"],

                    "characteristics": "speaking style description"

                }}

            ],

            "confidence": 0.75,

            "total_speakers": 2,

            "identification_method": "ai_inference"

        }}

        """



        try:
            response = await self.ai_processor.call_ollama(prompt, system_prompt)

            if not response or not response.strip():
                raise ValueError("Empty AI response")

            result = json.loads(response)

            # Validate result structure
            if not isinstance(result, dict):
                raise ValueError("Invalid result format")

            if "speakers" not in result:
                result["speakers"] = []

            result["identification_method"] = "ai_inference"

            return result

        except (json.JSONDecodeError, ValueError, Exception) as e:

            # Fallback for unparseable response or AI errors

            return {

                "speakers": [

                    {

                        "id": "speaker_1",

                        "name": "Unknown Speaker",

                        "segments": [text[:500] + "..." if len(text) > 500 else text],

                        "characteristics": "Unable to identify distinct speakers"

                    }

                ],

                "confidence": 0.3,

                "total_speakers": 1,

                "identification_method": "fallback",
                "error": f"AI identification failed: {str(e)}"

            }