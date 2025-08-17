import re
import json
from typing import Dict, List, Tuple
import asyncio

class SpeakerIdentifier:

    def __init__(self, ai_processor):

        self.ai_processor = ai_processor

        

    async def identify_speakers_advanced(self, text: str, context: str = "") -> Dict:

        """Advanced speaker identification with multiple strategies"""

        

        # Strategy 1: Look for explicit speaker labels

        explicit_speakers = self._extract_explicit_speakers(text)

        

        if explicit_speakers:

            return await self._process_explicit_speakers(text, explicit_speakers)

        

        # Strategy 2: Use AI to infer speakers

        return await self._ai_speaker_identification(text, context)

    

    def _extract_explicit_speakers(self, text: str) -> List[str]:

        """Extract speakers from text with explicit labels like 'John: text'"""

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

                match = re.match(pattern, line, re.MULTILINE)

                if match:

                    speaker_name = match.group(1).strip()

                    if len(speaker_name.split()) <= 3:  # Reasonable name length

                        speakers.add(speaker_name)

        

        return list(speakers)

    

    async def _process_explicit_speakers(self, text: str, speakers: List[str]) -> Dict:

        """Process text with known speakers"""

        speaker_segments = {}

        

        for speaker in speakers:

            speaker_segments[speaker] = []

        

        lines = text.split('\n')

        current_speaker = None

        

        for line in lines:

            line = line.strip()

            if not line:

                continue

            

            # Check if line starts with a speaker name

            speaker_found = None

            for speaker in speakers:

                if line.startswith(f"{speaker}:"):

                    speaker_found = speaker

                    text_content = line[len(speaker)+1:].strip()

                    break

            

            if speaker_found:

                current_speaker = speaker_found

                if text_content:

                    speaker_segments[current_speaker].append(text_content)

            elif current_speaker:

                # Continue previous speaker's text

                speaker_segments[current_speaker].append(line)

        

        # Format response

        formatted_speakers = []

        for i, (speaker, segments) in enumerate(speaker_segments.items()):

            if segments:  # Only include speakers with content

                formatted_speakers.append({

                    "id": f"speaker_{i+1}",

                    "name": speaker,

                    "segments": segments,

                    "total_words": sum(len(seg.split()) for seg in segments)

                })

        

        return {

            "speakers": formatted_speakers,

            "confidence": 0.95,  # High confidence for explicit speakers

            "total_speakers": len(formatted_speakers),

            "identification_method": "explicit_labels"

        }

    

    async def _ai_speaker_identification(self, text: str, context: str) -> Dict:

        """Use AI to identify speakers when no explicit labels exist"""

        system_prompt = """You are an expert at identifying different speakers in meeting transcripts.

        Analyze speech patterns, vocabulary, topics discussed, and conversation flow to identify distinct speakers.

        Look for:

        - Changes in speaking style or vocabulary

        - Topic transitions that suggest different speakers

        - Questions vs answers patterns

        - Formal vs informal language

        - Technical vs non-technical discussions"""

        

        prompt = f"""

        Analyze this meeting transcript and identify distinct speakers based on speech patterns and context:

        

        Context: {context}

        

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

        

        response = await self.ai_processor.call_ollama(prompt, system_prompt)

        

        try:

            result = json.loads(response)

            result["identification_method"] = "ai_inference"

            return result

        except json.JSONDecodeError:

            # Fallback for unparseable response

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

                "identification_method": "fallback"

            }
