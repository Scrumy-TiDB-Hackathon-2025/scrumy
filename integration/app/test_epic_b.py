import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio

import json

import time

from app.integrated_processor import IntegratedAIProcessor

from app.mock_data.generate_mock_data import MockDataGenerator

class EpicBTestSuite:

    def __init__(self):

        self.processor = IntegratedAIProcessor()

        self.mock_generator = MockDataGenerator()

        self.test_results = []

    

    async def run_all_tests(self):

        """Run comprehensive test suite for Epic B"""

        print("🚀 Starting Epic B Integration Tests...")

        

        # Generate test data

        test_meetings = self.mock_generator.generate_multiple_meetings(5)

        

        # Run tests

        await self.test_ollama_connection()

        await self.test_speaker_identification(test_meetings[0])

        await self.test_meeting_summarization(test_meetings[1])

        await self.test_task_extraction(test_meetings[2])

        await self.test_complete_processing(test_meetings[3])

        await self.test_performance(test_meetings[4])

        

        self.print_results()

    

    async def test_ollama_connection(self):

        """Test Ollama connection and model availability"""

        try:

            response = await self.processor.ai_processor.call_ollama("Hello, are you working?")

            success = len(response) > 0

            

            self.test_results.append({

                "test": "Ollama Connection",

                "passed": success,

                "details": f"Response length: {len(response)}"

            })

        except Exception as e:

            self.test_results.append({

                "test": "Ollama Connection",

                "passed": False,

                "details": str(e)

            })

    

    async def test_speaker_identification(self, meeting_data):

        """Test speaker identification functionality"""

        try:

            transcript = meeting_data["full_transcript"]

            result = await self.processor.speaker_identifier.identify_speakers_advanced(transcript)

            

            success = (

                "speakers" in result and

                len(result["speakers"]) > 0 and

                result.get("confidence", 0) > 0.3

            )

            

            self.test_results.append({

                "test": "Speaker Identification",

                "passed": success,

                "details": f"Found {len(result.get('speakers', []))} speakers, confidence: {result.get('confidence', 0)}"

            })

        except Exception as e:

            self.test_results.append({

                "test": "Speaker Identification",

                "passed": False,

                "details": str(e)

            })

    

    async def test_meeting_summarization(self, meeting_data):

        """Test meeting summarization functionality"""

        try:

            transcript = meeting_data["full_transcript"]

            context = {"title": meeting_data["meeting_type"]}

            

            result = await self.processor.meeting_summarizer.generate_comprehensive_summary(transcript, context)

            

            success = (

                "executive_summary" in result and

                "key_decisions" in result and

                len(result.get("executive_summary", {}).get("overview", "")) > 10

            )

            

            self.test_results.append({

                "test": "Meeting Summarization",

                "passed": success,

                "details": f"Summary sections: {len(result.keys())}"

            })

        except Exception as e:

            self.test_results.append({

                "test": "Meeting Summarization",

                "passed": False,

                "details": str(e)

            })

    

    async def test_task_extraction(self, meeting_data):

        """Test task extraction functionality"""

        try:

            transcript = meeting_data["full_transcript"]

            result = await self.processor.task_extractor.extract_comprehensive_tasks(transcript)

            

            success = (

                "tasks" in result and

                "task_summary" in result and

                isinstance(result["tasks"], list)

            )

            

            self.test_results.append({

                "test": "Task Extraction",

                "passed": success,

                "details": f"Extracted {len(result.get('tasks', []))} tasks"

            })

        except Exception as e:

            self.test_results.append({

                "test": "Task Extraction",

                "passed": False,

                "details": str(e)

            })

    

    async def test_complete_processing(self, meeting_data):

        """Test complete integrated processing"""

        try:

            transcript = meeting_data["full_transcript"]

            context = {

                "meeting_id": meeting_data["meeting_id"],

                "title": meeting_data["meeting_type"]

            }

            

            start_time = time.time()

            result = await self.processor.process_complete_meeting(transcript, context)

            processing_time = time.time() - start_time

            

            success = (

                result.get("status") == "success" and

                "processing_results" in result and

                all(key in result["processing_results"] for key in ["speakers", "summary", "tasks"])

            )

            

            self.test_results.append({

                "test": "Complete Processing",

                "passed": success,

                "details": f"Processing time: {processing_time:.2f}s"

            })

        except Exception as e:

            self.test_results.append({

                "test": "Complete Processing",

                "passed": False,

                "details": str(e)

            })

    

    async def test_performance(self, meeting_data):

        """Test performance with longer transcript"""

        try:

            # Create longer transcript by repeating

            long_transcript = meeting_data["full_transcript"] * 3

            

            start_time = time.time()

            result = await self.processor.process_complete_meeting(long_transcript)

            processing_time = time.time() - start_time

            

            success = (

                result.get("status") == "success" and

                processing_time < 60  # Should complete within 60 seconds

            )

            

            self.test_results.append({

                "test": "Performance Test",

                "passed": success,

                "details": f"Processed {len(long_transcript)} chars in {processing_time:.2f}s"

            })

        except Exception as e:

            self.test_results.append({

                "test": "Performance Test",

                "passed": False,

                "details": str(e)

            })

    

    def print_results(self):

        """Print test results"""

        print("\n" + "="*50)

        print("🧪 EPIC B TEST RESULTS")

        print("="*50)

        

        passed = 0

        total = len(self.test_results)

        

        for result in self.test_results:

            status = "✅ PASS" if result["passed"] else "❌ FAIL"

            print(f"{status} {result['test']}: {result['details']}")

            if result["passed"]:

                passed += 1

        

        print(f"\n📊 Summary: {passed}/{total} tests passed")

        

        if passed == total:

            print("🎉 Epic B is ready for integration!")

        else:

            print("⚠️  Some tests failed. Please review and fix.")

async def main():

    test_suite = EpicBTestSuite()

    await test_suite.run_all_tests()

if __name__ == "__main__":

    asyncio.run(main())
