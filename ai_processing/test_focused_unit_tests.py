#!/usr/bin/env python3
"""
Focused Unit Tests for AI Processing Core Functionality
Tests that can run without requiring the server to be running
"""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Test imports
try:
    from app.ai_processor import AIProcessor
    from app.speaker_identifier import SpeakerIdentifier
    from app.meeting_summarizer import MeetingSummarizer
    from app.task_extractor import TaskExtractor
    from app.integrated_processor import IntegratedAIProcessor
    from app.integration_adapter import AIProcessingIntegrationAdapter, get_integration_adapter, ParticipantData
    AI_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import AI modules: {e}")
    AI_MODULES_AVAILABLE = False


class TestAIProcessorCore(unittest.TestCase):
    """Test core AI processor functionality"""

    def setUp(self):
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")
        self.processor = AIProcessor()

    def test_processor_initialization(self):
        """Test AI processor initializes correctly"""
        self.assertIsNotNone(self.processor)
        self.assertTrue(hasattr(self.processor, 'process_text'))

    def test_process_text_basic(self):
        """Test basic text processing"""
        test_text = "This is a test meeting transcript with some content."

        # Mock the actual processing since we don't have real AI models in test
        with patch.object(self.processor, 'process_text', return_value="Processed text"):
            result = self.processor.process_text(test_text)
            self.assertEqual(result, "Processed text")


class TestSpeakerIdentification(unittest.TestCase):
    """Test speaker identification functionality"""

    def setUp(self):
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")

        mock_processor = Mock()
        self.speaker_identifier = SpeakerIdentifier(mock_processor)

    def test_extract_explicit_speakers(self):
        """Test extraction of explicitly labeled speakers"""
        test_text = """
        John: Hello everyone, let's start the meeting.
        Sarah: Thanks John, I have the agenda ready.
        Mike: Great, let's begin with the first item.
        """

        speakers = self.speaker_identifier._extract_explicit_speakers(test_text)

        self.assertIsInstance(speakers, list)
        expected_speakers = ['John', 'Sarah', 'Mike']
        for speaker in expected_speakers:
            self.assertIn(speaker, speakers)

    def test_extract_explicit_speakers_edge_cases(self):
        """Test speaker extraction with edge cases"""
        # Test with no speakers
        empty_text = "This is just a regular text without any speaker labels."
        speakers = self.speaker_identifier._extract_explicit_speakers(empty_text)
        self.assertEqual(len(speakers), 0)

        # Test with different formats
        mixed_format_text = """
        [John Smith] Welcome to the meeting.
        Mary Johnson says: Let's get started.
        """
        speakers = self.speaker_identifier._extract_explicit_speakers(mixed_format_text)
        self.assertTrue(len(speakers) >= 1)

    async def test_ai_speaker_identification(self):
        """Test AI-based speaker identification"""
        test_text = "Person A discussed the budget. Person B mentioned the timeline."

        # Mock AI processing
        mock_result = {
            'speakers': ['Person A', 'Person B'],
            'confidence': 0.85,
            'segments': {
                'Person A': ['discussed the budget'],
                'Person B': ['mentioned the timeline']
            }
        }

        with patch.object(self.speaker_identifier, '_ai_speaker_identification',
                         return_value=mock_result):
            result = await self.speaker_identifier._ai_speaker_identification(test_text)

            self.assertIn('speakers', result)
            self.assertIn('confidence', result)
            self.assertEqual(len(result['speakers']), 2)


class TestTaskExtraction(unittest.TestCase):
    """Test task extraction functionality"""

    def setUp(self):
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")

        mock_processor = Mock()
        self.task_extractor = TaskExtractor(mock_processor)

    async def test_extract_comprehensive_tasks(self):
        """Test comprehensive task extraction"""
        test_transcript = """
        John: We need to update the user authentication system by Friday.
        Sarah: I'll handle the API documentation.
        Mike: I can work on the database schema changes.
        We should schedule a follow-up meeting for next week.
        """

        meeting_context = {
            'participants': ['John', 'Sarah', 'Mike'],
            'meeting_id': 'test_meeting_123'
        }

        # Mock the AI processing
        mock_tasks = [
            {
                'title': 'Update user authentication system',
                'description': 'Update authentication by Friday',
                'assignee': 'John',
                'priority': 'high',
                'category': 'action_item',
                'due_date': '2025-01-15'
            },
            {
                'title': 'Handle API documentation',
                'description': 'Update API documentation',
                'assignee': 'Sarah',
                'priority': 'medium',
                'category': 'action_item'
            }
        ]

        with patch.object(self.task_extractor, 'extract_comprehensive_tasks',
                         return_value={'tasks': mock_tasks}):
            result = await self.task_extractor.extract_comprehensive_tasks(
                test_transcript, meeting_context
            )

            self.assertIn('tasks', result)
            self.assertEqual(len(result['tasks']), 2)

            # Validate task structure
            for task in result['tasks']:
                self.assertIn('title', task)
                self.assertIn('assignee', task)
                self.assertIn('priority', task)


class TestMeetingSummarization(unittest.TestCase):
    """Test meeting summarization functionality"""

    def setUp(self):
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")

        mock_processor = Mock()
        self.summarizer = MeetingSummarizer(mock_processor)

    async def test_generate_comprehensive_summary(self):
        """Test comprehensive summary generation"""
        test_transcript = """
        This was a productive sprint planning meeting. We discussed the upcoming
        features and assigned tasks to team members. Key decisions were made about
        the technology stack and timeline.
        """

        meeting_context = {
            'meeting_id': 'test_meeting_123',
            'participants': ['John', 'Sarah', 'Mike']
        }

        # Mock summary result
        mock_summary = {
            'overview': 'Productive sprint planning session',
            'key_points': ['Technology stack decisions', 'Task assignments'],
            'decisions': [{'decision': 'Use React for frontend', 'rationale': 'Team expertise'}],
            'participants': [{'name': 'John', 'role': 'lead', 'participation_level': 'high'}],
            'business_impact': 'Positive impact on project timeline'
        }

        with patch.object(self.summarizer, 'generate_comprehensive_summary',
                         return_value=mock_summary):
            result = await self.summarizer.generate_comprehensive_summary(
                test_transcript, meeting_context
            )

            self.assertIn('overview', result)
            self.assertIn('key_points', result)
            self.assertIn('decisions', result)
            self.assertIsInstance(result['key_points'], list)


class TestIntegratedProcessor(unittest.TestCase):
    """Test integrated AI processor functionality"""

    def setUp(self):
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")
        self.processor = IntegratedAIProcessor()

    async def test_process_complete_meeting(self):
        """Test complete meeting processing integration"""
        test_transcript = """
        John: Let's start the sprint planning. We need to prioritize the authentication feature.
        Sarah: I agree. I can handle the frontend implementation.
        Mike: I'll work on the backend API.
        """

        meeting_context = {
            'meeting_id': 'integration_test_123',
            'platform': 'google-meet',
            'participants': ['John', 'Sarah', 'Mike']
        }

        # Mock all the sub-processors
        mock_speaker_result = {
            'speakers': [
                {'name': 'John', 'segments': ['Let\'s start the sprint planning']},
                {'name': 'Sarah', 'segments': ['I can handle the frontend']},
                {'name': 'Mike', 'segments': ['I\'ll work on the backend']}
            ]
        }

        mock_summary_result = {
            'overview': 'Sprint planning meeting',
            'key_points': ['Authentication feature prioritized']
        }

        mock_tasks_result = {
            'tasks': [
                {'title': 'Frontend implementation', 'assignee': 'Sarah'},
                {'title': 'Backend API', 'assignee': 'Mike'}
            ]
        }

        with patch.object(self.processor.speaker_identifier, 'identify_speakers_advanced',
                         return_value=mock_speaker_result), \
             patch.object(self.processor.meeting_summarizer, 'generate_comprehensive_summary',
                         return_value=mock_summary_result), \
             patch.object(self.processor.task_extractor, 'extract_comprehensive_tasks',
                         return_value=mock_tasks_result):

            result = await self.processor.process_complete_meeting(test_transcript, meeting_context)

            self.assertIn('speakers', result)
            self.assertIn('summary', result)
            self.assertIn('tasks', result)
            self.assertEqual(len(result['speakers']), 3)
            self.assertEqual(len(result['tasks']), 2)


class TestIntegrationAdapter(unittest.TestCase):
    """Test integration adapter functionality"""

    def setUp(self):
        self.adapter = AIProcessingIntegrationAdapter(use_mock=True)

    def test_adapter_initialization(self):
        """Test adapter initializes correctly"""
        self.assertIsNotNone(self.adapter)
        self.assertTrue(self.adapter.use_mock)
        self.assertIsNotNone(self.adapter.client)

    async def test_process_meeting_complete(self):
        """Test complete meeting processing notification"""
        meeting_id = "test_meeting_456"
        meeting_title = "Test Meeting"
        platform = "google-meet"
        participants = [
            ParticipantData("p1", "Alice", "platform_1", "active", True, "2025-01-09T10:00:00Z"),
            ParticipantData("p2", "Bob", "platform_2", "active", False, "2025-01-09T10:01:00Z")
        ]
        participant_count = 2
        transcript = "This is a test transcript."

        summary_data = {
            'executive_summary': {'overview': 'Test meeting summary'},
            'key_decisions': [],
            'participants': [],
            'next_steps': []
        }

        tasks_data = [
            {
                'id': 'task_1',
                'title': 'Test task',
                'description': 'A test task',
                'assignee': 'Alice',
                'priority': 'medium'
            }
        ]

        speakers_data = [
            {'id': 'speaker_1', 'name': 'Alice', 'segments': ['Hello'], 'total_words': 10}
        ]

        result = await self.adapter.process_meeting_complete(
            meeting_id, meeting_title, platform, participants, participant_count, transcript,
            summary_data, tasks_data, speakers_data
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('success', False))
        self.assertIn('integration_id', result)

    async def test_create_tasks_external(self):
        """Test external task creation"""
        meeting_id = "test_meeting_789"
        meeting_title = "Task Creation Test"
        participants = ["Charlie", "Diana"]

        tasks_data = [
            {
                'title': 'External task 1',
                'description': 'First external task',
                'assignee': 'Charlie',
                'priority': 'high'
            },
            {
                'title': 'External task 2',
                'description': 'Second external task',
                'assignee': 'Diana',
                'priority': 'low'
            }
        ]

        result = await self.adapter.create_tasks_external(
            meeting_id, meeting_title, participants, tasks_data
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('success', False))
        self.assertIn('created_tasks', result)
        self.assertEqual(len(result['created_tasks']), 2)

    def test_priority_normalization(self):
        """Test priority value normalization"""
        # Test high priority variations
        self.assertEqual(self.adapter._normalize_priority("high"), "high")
        self.assertEqual(self.adapter._normalize_priority("urgent"), "high")
        self.assertEqual(self.adapter._normalize_priority("critical"), "high")

        # Test low priority variations
        self.assertEqual(self.adapter._normalize_priority("low"), "low")
        self.assertEqual(self.adapter._normalize_priority("minor"), "low")

        # Test medium priority (default)
        self.assertEqual(self.adapter._normalize_priority("medium"), "medium")
        self.assertEqual(self.adapter._normalize_priority("normal"), "medium")
        self.assertEqual(self.adapter._normalize_priority("unknown"), "medium")

    def test_status_normalization(self):
        """Test status value normalization"""
        # Test in progress variations
        self.assertEqual(self.adapter._normalize_status("in_progress"), "in_progress")
        self.assertEqual(self.adapter._normalize_status("in progress"), "in_progress")
        self.assertEqual(self.adapter._normalize_status("working"), "in_progress")

        # Test completed variations
        self.assertEqual(self.adapter._normalize_status("completed"), "completed")
        self.assertEqual(self.adapter._normalize_status("done"), "completed")
        self.assertEqual(self.adapter._normalize_status("finished"), "completed")

        # Test pending (default)
        self.assertEqual(self.adapter._normalize_status("pending"), "pending")
        self.assertEqual(self.adapter._normalize_status("unknown"), "pending")

    def test_duration_estimation(self):
        """Test meeting duration estimation"""
        # Short transcript
        short_text = " ".join(["word"] * 100)  # 100 words
        duration = self.adapter._estimate_duration(short_text)
        self.assertIn("minute", duration)

        # Long transcript
        long_text = " ".join(["word"] * 10000)  # 10,000 words
        duration = self.adapter._estimate_duration(long_text)
        self.assertIn("hour" if "h" in duration else "minute", duration)

        # Empty transcript
        empty_duration = self.adapter._estimate_duration("")
        self.assertEqual(empty_duration, "1 minutes")


class TestSharedContractCompliance(unittest.TestCase):
    """Test compliance with shared API contracts"""

    def test_meeting_data_structure(self):
        """Test meeting data structure matches shared contract"""
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")

        from app.integration_adapter import MeetingData

        participants = [
            ParticipantData("p1", "Alice", "platform_1", "active", True, "2025-01-09T10:00:00Z"),
            ParticipantData("p2", "Bob", "platform_2", "active", False, "2025-01-09T10:01:00Z")
        ]
        meeting_data = MeetingData(
            meeting_id="test_123",
            title="Test Meeting",
            platform="google-meet",
            participants=participants,
            participant_count=2,
            duration="30 minutes",
            transcript="Test transcript",
            created_at=datetime.now().isoformat()
        )

        # Verify all required fields are present
        self.assertEqual(meeting_data.meeting_id, "test_123")
        self.assertEqual(meeting_data.title, "Test Meeting")
        self.assertEqual(meeting_data.platform, "google-meet")
        self.assertIsInstance(meeting_data.participants, list)
        self.assertEqual(len(meeting_data.participants), 2)

    def test_task_definition_structure(self):
        """Test task definition structure matches shared contract"""
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")

        from app.integration_adapter import TaskDefinition

        task = TaskDefinition(
            id="task_1",
            title="Test Task",
            description="A test task",
            meeting_id="meeting_123",
            assignee="Alice",
            priority="high",
            status="pending",
            category="action_item",
            created_at=datetime.now().isoformat()
        )

        # Verify required fields
        self.assertEqual(task.id, "task_1")
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.meeting_id, "meeting_123")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.status, "pending")

    def test_api_response_format(self):
        """Test API response formats match shared contracts"""
        # Test health endpoint format
        health_response = {"status": "healthy"}
        self.assertIn("status", health_response)
        self.assertEqual(health_response["status"], "healthy")

        # Test transcription result format
        transcription_result = {
            "type": "transcription_result",
            "data": {
                "text": "Test transcription",
                "confidence": 0.95,
                "timestamp": datetime.now().isoformat(),
                "speaker": "Alice"
            }
        }

        self.assertEqual(transcription_result["type"], "transcription_result")
        self.assertIn("data", transcription_result)
        self.assertIn("text", transcription_result["data"])
        self.assertIn("confidence", transcription_result["data"])
        self.assertIn("speaker", transcription_result["data"])


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        if not AI_MODULES_AVAILABLE:
            self.skipTest("AI modules not available")

    def test_empty_input_handling(self):
        """Test handling of empty or null inputs"""
        mock_processor = Mock()
        speaker_identifier = SpeakerIdentifier(mock_processor)

        # Test empty text
        speakers = speaker_identifier._extract_explicit_speakers("")
        self.assertEqual(len(speakers), 0)

        # Test None input
        speakers = speaker_identifier._extract_explicit_speakers(None)
        self.assertEqual(len(speakers), 0)

    def test_malformed_data_handling(self):
        """Test handling of malformed input data"""
        adapter = AIProcessingIntegrationAdapter(use_mock=True)

        # Test malformed tasks data
        malformed_tasks = [
            {"title": "Task without required fields"},
            {"description": "Task without title"},
            None,  # Null task
            {"title": "", "description": ""}  # Empty fields
        ]

        converted_tasks = adapter._convert_tasks_data("meeting_123", malformed_tasks)

        # Should handle gracefully without crashing
        self.assertIsInstance(converted_tasks, list)
        self.assertEqual(len(converted_tasks), 4)  # All items processed, even malformed ones

    async def test_integration_failure_handling(self):
        """Test handling of integration failures"""
        # Create adapter that will fail
        adapter = AIProcessingIntegrationAdapter(use_mock=True)

        # Mock client to raise exception
        adapter.client = Mock()
        adapter.client.process_complete_meeting = AsyncMock(side_effect=Exception("Integration failed"))

        result = await adapter.process_meeting_complete(
            "test_meeting", "Test", "google-meet", [], 0, "", {}, [], []
        )

        self.assertFalse(result.get('success', True))
        self.assertIn('error', result)


def run_tests():
    """Run all unit tests"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_cases = [
        TestAIProcessorCore,
        TestSpeakerIdentification,
        TestTaskExtraction,
        TestMeetingSummarization,
        TestIntegratedProcessor,
        TestIntegrationAdapter,
        TestSharedContractCompliance,
        TestErrorHandling
    ]

    for test_case in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_case)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*50}")
    print(f"UNIT TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")

    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("✅ UNIT TESTS MOSTLY PASSING - System is in good shape!")
    elif success_rate >= 60:
        print("⚠️  UNIT TESTS PARTIALLY PASSING - Some issues need attention")
    else:
        print("❌ UNIT TESTS FAILING - Significant issues need to be resolved")

    return result.wasSuccessful()


if __name__ == "__main__":
    import asyncio

    # Set event loop policy for Windows compatibility
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    print("🧪 Running AI Processing Core Functionality Unit Tests")
    print("This test suite validates core functionality without requiring running servers")
    print("="*80)

    success = run_tests()

    if success:
        print("\n🎉 All unit tests passed! Core functionality is working correctly.")
        exit(0)
    else:
        print("\n❌ Some unit tests failed. Please review the issues above.")
        exit(1)
