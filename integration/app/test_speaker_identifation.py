import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import pytest
import json
from app.ai_processor import AIProcessor
from app.speaker_identifier import SpeakerIdentifier

@pytest.mark.asyncio
async def test_speaker_identification():

    processor = AIProcessor()

    identifier = SpeakerIdentifier(processor)

    

    # Test with explicit speakers

    explicit_text = """

    John: Good morning everyone, let's start our daily standup.

    Sarah: Thanks John. I completed the user authentication module yesterday.

    Mike: Great work Sarah. I'm working on the database optimization today.

    John: Excellent. Any blockers we need to discuss?

    Sarah: I need help with the OAuth integration. Mike, can you assist?

    Mike: Sure, I can help after lunch.

    """

    

    print("Testing explicit speaker identification...")

    result1 = await identifier.identify_speakers_advanced(explicit_text)

    print(json.dumps(result1, indent=2))

    

    # Test with implicit speakers

    implicit_text = """

    Good morning everyone, let's start our meeting. We have several items to discuss today.

    Thanks for organizing this. I wanted to update everyone on the project status.

    That's great to hear. What about the timeline for the next milestone?

    I think we can meet the deadline if we prioritize the core features first.

    Agreed. Should we postpone the nice-to-have features to the next sprint?

    Yes, that makes sense. Let's focus on what's essential for the MVP.

    """

    

    print("\nTesting AI speaker identification...")

    result2 = await identifier.identify_speakers_advanced(implicit_text)

    print(json.dumps(result2, indent=2))

if __name__ == "__main__":

    asyncio.run(test_speaker_identification())
