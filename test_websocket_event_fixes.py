#!/usr/bin/env python3
"""
WebSocket Event Fixes Validation Test Script
Tests the fixes for duplicate WebSocket transcription events and validates standardized event handling.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict
from unittest.mock import Mock, AsyncMock

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_processing', 'app'))

try:
    from websocket_events import WebSocketEventTypes, WebSocketEventData, WebSocketEventValidator, DEPRECATED_EVENT_NAMES
    from websocket_event_monitor import WebSocketEventMonitor
except ImportError as e:
    print(f"❌ Failed to import WebSocket modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketEventFixesTest:
    """Test suite for WebSocket event fixes."""

    def __init__(self):
        self.monitor = WebSocketEventMonitor()
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0

    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result and update counters."""
        status = "✅ PASS" if passed else "❌ FAIL"
        full_message = f"{status}: {test_name}"
        if message:
            full_message += f" - {message}"

        print(full_message)
        logger.info(full_message)

        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now()
        })

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def test_event_constants_availability(self):
        """Test that all required event constants are available."""
        required_constants = [
            'TRANSCRIPTION_RESULT',
            'HANDSHAKE',
            'HANDSHAKE_ACK',
            'MEETING_EVENT',
            'PROCESSING_STATUS',
            'ERROR'
        ]

        missing_constants = []
        for const in required_constants:
            if not hasattr(WebSocketEventTypes, const):
                missing_constants.append(const)

        passed = len(missing_constants) == 0
        message = f"Missing constants: {missing_constants}" if missing_constants else "All constants available"
        self.log_test_result("Event Constants Available", passed, message)

    def test_deprecated_event_mapping(self):
        """Test that deprecated events are properly mapped to new ones."""
        test_cases = [
            ("transcription_result", "TRANSCRIPTION_RESULT"),
            ("meeting_update", "MEETING_UPDATE"),
            ("processing_complete", "PROCESSING_COMPLETE")
        ]

        all_passed = True
        for old_event, expected_new in test_cases:
            if old_event not in DEPRECATED_EVENT_NAMES:
                all_passed = False
                break
            if DEPRECATED_EVENT_NAMES[old_event] != expected_new:
                all_passed = False
                break

        self.log_test_result("Deprecated Event Mapping", all_passed)

    def test_event_data_structure_validation(self):
        """Test event data structure validation."""
        # Test valid transcription result
        valid_data = WebSocketEventData.transcription_result(
            text="Test transcription",
            confidence=0.95,
            timestamp="2024-01-01T10:00:00Z",
            speaker="Speaker1"
        )

        is_valid, error_msg = WebSocketEventValidator.validate_event(
            WebSocketEventTypes.TRANSCRIPTION_RESULT,
            valid_data
        )

        self.log_test_result("Valid Event Data Structure", is_valid, error_msg)

        # Test invalid data (missing required fields)
        invalid_data = {"speaker": "Speaker1"}  # Missing text, confidence, timestamp

        is_valid, error_msg = WebSocketEventValidator.validate_event(
            WebSocketEventTypes.TRANSCRIPTION_RESULT,
            invalid_data
        )

        self.log_test_result("Invalid Event Data Detection", not is_valid, f"Correctly rejected: {error_msg}")

    def test_duplicate_event_detection(self):
        """Test duplicate event detection functionality."""
        # Create identical events
        event_data = {
            "text": "Hello world",
            "confidence": 0.9,
            "timestamp": "2024-01-01T10:00:00Z",
            "speaker": "Speaker1"
        }

        # First event should not be duplicate
        result1 = self.monitor.record_event(
            WebSocketEventTypes.TRANSCRIPTION_RESULT,
            event_data,
            source="test_client",
            session_id="test_session"
        )

        # Second identical event should be detected as duplicate
        result2 = self.monitor.record_event(
            WebSocketEventTypes.TRANSCRIPTION_RESULT,
            event_data,
            source="test_client",
            session_id="test_session"
        )

        first_not_duplicate = not result1['is_duplicate']
        second_is_duplicate = result2['is_duplicate']

        self.log_test_result("Duplicate Event Detection",
                           first_not_duplicate and second_is_duplicate,
                           f"First: {result1['is_duplicate']}, Second: {result2['is_duplicate']}")

    def test_deprecated_event_detection(self):
        """Test deprecated event type detection."""
        # Test deprecated event
        result = self.monitor.record_event(
            "transcription_result",  # Deprecated lowercase version
            {"text": "Test", "confidence": 0.9, "timestamp": "2024-01-01T10:00:00Z"},
            source="test_client"
        )

        self.log_test_result("Deprecated Event Detection",
                           result['is_deprecated'],
                           f"Recommendations: {result['recommendations']}")

    def test_event_monitoring_statistics(self):
        """Test event monitoring statistics collection."""
        # Generate some test events
        for i in range(5):
            self.monitor.record_event(
                WebSocketEventTypes.TRANSCRIPTION_RESULT,
                {
                    "text": f"Test message {i}",
                    "confidence": 0.9,
                    "timestamp": f"2024-01-01T10:0{i}:00Z",
                    "speaker": "TestSpeaker"
                },
                source="test_stats",
                session_id="stats_session"
            )

        # Generate deprecated event
        self.monitor.record_event(
            "transcription_result",
            {"text": "Deprecated test", "confidence": 0.8, "timestamp": "2024-01-01T10:05:00Z"},
            source="test_stats"
        )

        stats = self.monitor.stats
        has_events = stats['total_events'] > 0
        has_deprecated = stats['deprecated_events'] > 0

        self.log_test_result("Monitoring Statistics Collection",
                           has_events and has_deprecated,
                           f"Total: {stats['total_events']}, Deprecated: {stats['deprecated_events']}")

    def test_comprehensive_monitoring_report(self):
        """Test comprehensive monitoring report generation."""
        try:
            report = self.monitor.get_comprehensive_report()

            required_sections = ['summary', 'duplicates', 'deprecated_usage', 'recommendations']
            has_all_sections = all(section in report for section in required_sections)

            self.log_test_result("Comprehensive Report Generation",
                               has_all_sections,
                               f"Report sections: {list(report.keys())}")
        except Exception as e:
            self.log_test_result("Comprehensive Report Generation", False, str(e))

    async def test_websocket_server_integration(self):
        """Test WebSocket server integration (mock test)."""
        try:
            # Mock WebSocket server components
            mock_websocket = Mock()
            mock_websocket.send = AsyncMock()

            # Test event creation and validation
            transcription_data = WebSocketEventData.transcription_result(
                text="Integration test message",
                confidence=0.95,
                timestamp=datetime.now().isoformat(),
                speaker="TestSpeaker",
                chunk_id=123
            )

            # Validate the data structure
            is_valid, error_msg = WebSocketEventValidator.validate_event(
                WebSocketEventTypes.TRANSCRIPTION_RESULT,
                transcription_data
            )

            self.log_test_result("WebSocket Server Integration Mock",
                               is_valid,
                               error_msg if not is_valid else "Event data structure valid")

        except Exception as e:
            self.log_test_result("WebSocket Server Integration Mock", False, str(e))

    def test_chrome_extension_compatibility(self):
        """Test Chrome extension event handling compatibility."""
        # Test that old event types can be converted to new ones
        old_events = ["transcription_result", "meeting_update", "processing_complete"]

        conversion_results = []
        for old_event in old_events:
            if old_event in DEPRECATED_EVENT_NAMES:
                new_event = DEPRECATED_EVENT_NAMES[old_event]
                conversion_results.append(new_event is not None)
            else:
                conversion_results.append(False)

        all_convertible = all(conversion_results)
        self.log_test_result("Chrome Extension Compatibility",
                           all_convertible,
                           f"Conversion results: {conversion_results}")

    def test_event_data_helper_functions(self):
        """Test event data helper functions."""
        # Test transcription result helper
        result_data = WebSocketEventData.transcription_result(
            text="Helper test",
            confidence=0.88,
            timestamp="2024-01-01T12:00:00Z",
            speaker="HelperSpeaker",
            chunk_id=456,
            is_final=True
        )

        has_required_fields = all(field in result_data for field in ['text', 'confidence', 'timestamp', 'speaker'])
        has_optional_fields = 'chunkId' in result_data and 'is_final' in result_data

        self.log_test_result("Event Data Helper Functions",
                           has_required_fields and has_optional_fields,
                           f"Data: {list(result_data.keys())}")

    def run_all_tests(self):
        """Run all tests and return results."""
        print("🚀 Starting WebSocket Event Fixes Validation Tests")
        print("=" * 60)

        # Run synchronous tests
        self.test_event_constants_availability()
        self.test_deprecated_event_mapping()
        self.test_event_data_structure_validation()
        self.test_duplicate_event_detection()
        self.test_deprecated_event_detection()
        self.test_event_monitoring_statistics()
        self.test_comprehensive_monitoring_report()
        self.test_chrome_extension_compatibility()
        self.test_event_data_helper_functions()

        print("\n" + "=" * 60)
        print("🔄 Running Async Tests")

        # Run async tests
        asyncio.run(self.test_websocket_server_integration())

        print("\n" + "=" * 60)
        self.print_summary()

        return {
            'passed': self.passed_tests,
            'failed': self.failed_tests,
            'total': self.passed_tests + self.failed_tests,
            'results': self.test_results,
            'monitoring_report': self.monitor.get_comprehensive_report()
        }

    def print_summary(self):
        """Print test summary."""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0

        print("📊 TEST SUMMARY")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {self.passed_tests} ✅")
        print(f"   Failed: {self.failed_tests} ❌")
        print(f"   Pass Rate: {pass_rate:.1f}%")

        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['test']}: {result['message']}")

        print("\n🎯 RECOMMENDATIONS:")
        if self.failed_tests == 0:
            print("   ✅ All tests passed! WebSocket event fixes are working correctly.")
        else:
            print("   ⚠️  Some tests failed. Review the failed tests and fix issues before deployment.")

        # Print monitoring insights
        report = self.monitor.get_comprehensive_report()
        if report['summary']['duplicates_detected'] > 0:
            print(f"   🔍 Detected {report['summary']['duplicates_detected']} duplicate events during testing")
        if report['summary']['deprecated_events'] > 0:
            print(f"   📢 Detected {report['summary']['deprecated_events']} deprecated events during testing")


def main():
    """Main test execution."""
    print("🤖 ScrumBot WebSocket Event Fixes Validation")
    print(f"📅 Test run started: {datetime.now()}")

    try:
        tester = WebSocketEventFixesTest()
        results = tester.run_all_tests()

        # Save results to file
        results_file = f"websocket_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            serializable_results = {
                **results,
                'test_timestamp': datetime.now().isoformat(),
                'results': [
                    {
                        **result,
                        'timestamp': result['timestamp'].isoformat()
                    } for result in results['results']
                ]
            }
            json.dump(serializable_results, f, indent=2)

        print(f"\n💾 Test results saved to: {results_file}")

        # Exit with appropriate code
        exit_code = 0 if results['failed'] == 0 else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.exception("Test execution failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
