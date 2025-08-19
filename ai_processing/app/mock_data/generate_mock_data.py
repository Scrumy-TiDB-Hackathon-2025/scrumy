import json

import random

import uuid

from datetime import datetime, timedelta

from typing import List, Dict

class MockDataGenerator:

    def __init__(self):

        self.speakers = [

            "John Smith", "Sarah Johnson", "Mike Chen", "Emily Davis",

            "Alex Rodriguez", "Lisa Wang", "David Brown", "Anna Kim"

        ]

        

        self.meeting_types = [

            "Daily Standup", "Sprint Planning", "Retrospective", 

            "Product Review", "Architecture Discussion", "Client Meeting"

        ]

        

        self.topics = [

            "user authentication", "database optimization", "UI improvements",

            "API integration", "testing strategy", "deployment pipeline",

            "performance issues", "security updates", "feature requests"

        ]

    def generate_meeting_transcript(self, duration_minutes: int = 30) -> Dict:

        """Generate a realistic meeting transcript"""

        num_speakers = random.randint(2, 4)

        meeting_speakers = random.sample(self.speakers, num_speakers)

        meeting_type = random.choice(self.meeting_types)

        

        transcript_segments = []

        current_time = 0

        

        # Generate opening

        transcript_segments.append({

            "speaker": meeting_speakers[0],

            "text": f"Good morning everyone, let's start our {meeting_type}. We have about {duration_minutes} minutes today.",

            "timestamp": current_time,

            "duration": 5

        })

        current_time += 5

        

        # Generate discussion segments

        for _ in range(random.randint(8, 15)):

            speaker = random.choice(meeting_speakers)

            topic = random.choice(self.topics)

            

            texts = [

                f"I think we should focus on {topic} this sprint.",

                f"The {topic} is causing some issues for our users.",

                f"Can we prioritize {topic} for the next release?",

                f"I've been working on {topic} and have some updates.",

                f"We need to discuss the approach for {topic}.",

                f"The team should review the {topic} implementation.",

                f"I'll take ownership of the {topic} task.",

                f"Let's schedule a follow-up meeting about {topic}."

            ]

            

            segment = {

                "speaker": speaker,

                "text": random.choice(texts),

                "timestamp": current_time,

                "duration": random.randint(10, 30)

            }

            

            transcript_segments.append(segment)

            current_time += segment["duration"]

            

            if current_time >= duration_minutes * 60:

                break

        

        # Generate closing

        transcript_segments.append({

            "speaker": meeting_speakers[0],

            "text": "Thanks everyone, let's wrap up here. I'll send out the action items after this meeting.",

            "timestamp": current_time,

            "duration": 5

        })

        

        # Create full transcript text

        full_transcript = "\n".join([

            f"{seg['speaker']}: {seg['text']}" for seg in transcript_segments

        ])

        

        return {

            "meeting_id": f"meeting-{uuid.uuid4()}",

            "meeting_type": meeting_type,

            "participants": meeting_speakers,

            "duration_minutes": duration_minutes,

            "transcript_segments": transcript_segments,

            "full_transcript": full_transcript,

            "generated_at": datetime.now().isoformat()

        }

    def generate_multiple_meetings(self, count: int = 10) -> List[Dict]:

        """Generate multiple meeting transcripts"""

        meetings = []

        for _ in range(count):

            duration = random.randint(15, 60)

            meeting = self.generate_meeting_transcript(duration)

            meetings.append(meeting)

        return meetings

    def save_mock_data(self, filename: str = "mock_meetings.json"):

        """Save mock data to file"""

        meetings = self.generate_multiple_meetings(20)

        with open(filename, 'w') as f:

            json.dump(meetings, f, indent=2)

        print(f"Generated {len(meetings)} mock meetings saved to {filename}")

if __name__ == "__main__":

    generator = MockDataGenerator()

    generator.save_mock_data()
