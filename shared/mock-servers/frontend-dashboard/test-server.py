#!/usr/bin/env python3
"""
Test script for Frontend Dashboard REST API Mock Server

This script tests the REST API mock server by making HTTP requests
to all endpoints and verifying the responses.
"""

import json
import logging
import requests
import time
from typing import Dict, List, Optional, Any
import argparse
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FrontendDashboardMockServerTest:
    """Test client for Frontend Dashboard REST API Mock Server"""

    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results: Dict[str, bool] = {}
        self.response_times: Dict[str, float] = {}

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                    timeout: int = 10) -> Optional[requests.Response]:
        """Make HTTP request to the server"""
        url = f"{self.base_url}{endpoint}"

        try:
            start_time = time.time()

            if method.upper() == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            end_time = time.time()
            self.response_times[endpoint] = end_time - start_time

            logger.debug(f"{method} {endpoint} - Status: {response.status_code} - Time: {self.response_times[endpoint]:.3f}s")
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method} {endpoint}: {e}")
            return None

    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint"""
        logger.info("Testing health endpoint...")

        response = self.make_request('GET', '/health')

        if response and response.status_code == 200:
            try:
                data = response.json()
                if (data.get('status') == 'healthy' and
                    'server' in data and
                    'timestamp' in data):
                    logger.info("✓ Health endpoint test passed")
                    self.test_results['health'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Health endpoint returned invalid JSON")

        logger.error("✗ Health endpoint test failed")
        self.test_results['health'] = False
        return False

    def test_get_meetings_endpoint(self) -> bool:
        """Test the get meetings endpoint"""
        logger.info("Testing get meetings endpoint...")

        response = self.make_request('GET', '/get-meetings')

        if response and response.status_code == 200:
            try:
                data = response.json()
                if ('meetings' in data and
                    isinstance(data['meetings'], list) and
                    'total_count' in data and
                    'timestamp' in data):
                    meetings_count = len(data['meetings'])
                    logger.info(f"✓ Get meetings test passed - Found {meetings_count} meetings")
                    self.test_results['get_meetings'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Get meetings endpoint returned invalid JSON")

        logger.error("✗ Get meetings endpoint test failed")
        self.test_results['get_meetings'] = False
        return False

    def test_get_meetings_with_filters(self) -> bool:
        """Test the get meetings endpoint with query filters"""
        logger.info("Testing get meetings with filters...")

        # Test with status filter
        response = self.make_request('GET', '/get-meetings?status=completed&limit=2')

        if response and response.status_code == 200:
            try:
                data = response.json()
                meetings = data.get('meetings', [])

                # Check that filter was applied
                if (len(meetings) <= 2 and
                    all(meeting.get('status') == 'completed' for meeting in meetings)):
                    logger.info("✓ Get meetings with filters test passed")
                    self.test_results['get_meetings_filtered'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Get meetings filtered endpoint returned invalid JSON")

        logger.error("✗ Get meetings with filters test failed")
        self.test_results['get_meetings_filtered'] = False
        return False

    def test_get_summary_endpoint(self) -> bool:
        """Test the get summary endpoint"""
        logger.info("Testing get summary endpoint...")

        # First get a meeting ID
        meetings_response = self.make_request('GET', '/get-meetings?limit=1')

        if not meetings_response or meetings_response.status_code != 200:
            logger.error("Could not get meetings to test summary endpoint")
            self.test_results['get_summary'] = False
            return False

        try:
            meetings_data = meetings_response.json()
            meetings = meetings_data.get('meetings', [])

            if not meetings:
                logger.error("No meetings available to test summary endpoint")
                self.test_results['get_summary'] = False
                return False

            meeting_id = meetings[0]['id']
            response = self.make_request('GET', f'/get-summary/{meeting_id}')

            if response and response.status_code == 200:
                data = response.json()
                if (data.get('status') in ['completed', 'processing'] and
                    data.get('meeting_id') == meeting_id):
                    if data.get('status') == 'completed' and 'data' in data:
                        logger.info("✓ Get summary test passed - Complete summary received")
                    else:
                        logger.info("✓ Get summary test passed - Processing status received")
                    self.test_results['get_summary'] = True
                    return True

        except json.JSONDecodeError:
            logger.error("Get summary endpoint returned invalid JSON")

        logger.error("✗ Get summary endpoint test failed")
        self.test_results['get_summary'] = False
        return False

    def test_get_summary_not_found(self) -> bool:
        """Test get summary endpoint with non-existent meeting ID"""
        logger.info("Testing get summary endpoint with invalid ID...")

        response = self.make_request('GET', '/get-summary/non_existent_meeting')

        if response and response.status_code == 404:
            try:
                data = response.json()
                if 'error' in data:
                    logger.info("✓ Get summary not found test passed")
                    self.test_results['get_summary_not_found'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Get summary not found returned invalid JSON")

        logger.error("✗ Get summary not found test failed")
        self.test_results['get_summary_not_found'] = False
        return False

    def test_get_transcripts_endpoint(self) -> bool:
        """Test the get transcripts endpoint"""
        logger.info("Testing get transcripts endpoint...")

        # Use a known meeting ID from mock data
        meeting_id = "meeting_001"
        response = self.make_request('GET', f'/get-transcripts/{meeting_id}')

        if response and response.status_code == 200:
            try:
                data = response.json()
                if ('transcripts' in data and
                    isinstance(data['transcripts'], list) and
                    'pagination' in data and
                    data.get('meeting_id') == meeting_id):
                    transcripts_count = len(data['transcripts'])
                    logger.info(f"✓ Get transcripts test passed - Found {transcripts_count} transcripts")
                    self.test_results['get_transcripts'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Get transcripts endpoint returned invalid JSON")

        logger.error("✗ Get transcripts endpoint test failed")
        self.test_results['get_transcripts'] = False
        return False

    def test_get_tasks_endpoint(self) -> bool:
        """Test the get tasks endpoint"""
        logger.info("Testing get tasks endpoint...")

        response = self.make_request('GET', '/get-tasks')

        if response and response.status_code == 200:
            try:
                data = response.json()
                if ('tasks' in data and
                    isinstance(data['tasks'], list) and
                    'total_count' in data and
                    'filtered_count' in data):
                    tasks_count = len(data['tasks'])
                    logger.info(f"✓ Get tasks test passed - Found {tasks_count} tasks")
                    self.test_results['get_tasks'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Get tasks endpoint returned invalid JSON")

        logger.error("✗ Get tasks endpoint test failed")
        self.test_results['get_tasks'] = False
        return False

    def test_get_tasks_with_filters(self) -> bool:
        """Test the get tasks endpoint with filters"""
        logger.info("Testing get tasks with filters...")

        response = self.make_request('GET', '/get-tasks?status=pending&priority=high')

        if response and response.status_code == 200:
            try:
                data = response.json()
                tasks = data.get('tasks', [])
                filters_applied = data.get('filters_applied', {})

                if (isinstance(tasks, list) and
                    filters_applied.get('status') == 'pending' and
                    filters_applied.get('priority') == 'high'):
                    logger.info("✓ Get tasks with filters test passed")
                    self.test_results['get_tasks_filtered'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Get tasks filtered endpoint returned invalid JSON")

        logger.error("✗ Get tasks with filters test failed")
        self.test_results['get_tasks_filtered'] = False
        return False

    def test_get_participants_endpoint(self) -> bool:
        """Test the get participants endpoint"""
        logger.info("Testing get participants endpoint...")

        # Use a known meeting ID from mock data
        meeting_id = "meeting_001"
        response = self.make_request('GET', f'/get-participants/{meeting_id}')

        if response and response.status_code == 200:
            try:
                data = response.json()
                if ('participants' in data and
                    isinstance(data['participants'], list) and
                    data.get('meeting_id') == meeting_id and
                    'total_participants' in data):
                    participants_count = len(data['participants'])
                    logger.info(f"✓ Get participants test passed - Found {participants_count} participants")
                    self.test_results['get_participants'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Get participants endpoint returned invalid JSON")

        logger.error("✗ Get participants endpoint test failed")
        self.test_results['get_participants'] = False
        return False

    def test_process_transcript_endpoint(self) -> bool:
        """Test the process transcript endpoint"""
        logger.info("Testing process transcript endpoint...")

        test_data = {
            "text": "This is a test transcript for processing",
            "meeting_id": "test_meeting_123",
            "model": "ollama",
            "model_name": "llama3.2:1b"
        }

        response = self.make_request('POST', '/process-transcript', test_data)

        if response and response.status_code == 200:
            try:
                data = response.json()
                if ('process_id' in data and
                    data.get('status') == 'processing' and
                    data.get('meeting_id') == test_data['meeting_id']):
                    logger.info("✓ Process transcript test passed")
                    self.test_results['process_transcript'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Process transcript endpoint returned invalid JSON")

        logger.error("✗ Process transcript endpoint test failed")
        self.test_results['process_transcript'] = False
        return False

    def test_process_transcript_with_tools_endpoint(self) -> bool:
        """Test the process transcript with tools endpoint"""
        logger.info("Testing process transcript with tools endpoint...")

        test_data = {
            "text": "This is a test transcript for processing with tools",
            "meeting_id": "test_meeting_tools_123",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": "google-meet",
            "participants": [
                {
                    "id": "participant_1",
                    "name": "Test User",
                    "status": "active",
                    "is_host": True
                }
            ],
            "participant_count": 1
        }

        response = self.make_request('POST', '/process-transcript-with-tools', test_data)

        if response and response.status_code == 200:
            try:
                data = response.json()
                if (data.get('status') == 'success' and
                    'analysis' in data and
                    'speakers' in data and
                    'actions_taken' in data):
                    logger.info("✓ Process transcript with tools test passed")
                    self.test_results['process_transcript_tools'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Process transcript with tools endpoint returned invalid JSON")

        logger.error("✗ Process transcript with tools endpoint test failed")
        self.test_results['process_transcript_tools'] = False
        return False

    def test_available_tools_endpoint(self) -> bool:
        """Test the available tools endpoint"""
        logger.info("Testing available tools endpoint...")

        response = self.make_request('GET', '/available-tools')

        if response and response.status_code == 200:
            try:
                data = response.json()
                if ('tools' in data and
                    isinstance(data['tools'], list) and
                    'tool_names' in data and
                    'count' in data):
                    tools_count = data.get('count', 0)
                    logger.info(f"✓ Available tools test passed - Found {tools_count} tools")
                    self.test_results['available_tools'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Available tools endpoint returned invalid JSON")

        logger.error("✗ Available tools endpoint test failed")
        self.test_results['available_tools'] = False
        return False

    def test_analytics_overview_endpoint(self) -> bool:
        """Test the analytics overview endpoint"""
        logger.info("Testing analytics overview endpoint...")

        response = self.make_request('GET', '/analytics/overview')

        if response and response.status_code == 200:
            try:
                data = response.json()
                if ('meetings' in data and
                    'tasks' in data and
                    'platforms' in data and
                    isinstance(data['meetings'], dict) and
                    isinstance(data['tasks'], dict)):
                    logger.info("✓ Analytics overview test passed")
                    self.test_results['analytics_overview'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Analytics overview endpoint returned invalid JSON")

        logger.error("✗ Analytics overview endpoint test failed")
        self.test_results['analytics_overview'] = False
        return False

    def test_invalid_endpoints(self) -> bool:
        """Test invalid endpoints return 404"""
        logger.info("Testing invalid endpoint handling...")

        response = self.make_request('GET', '/non-existent-endpoint')

        if response and response.status_code == 404:
            try:
                data = response.json()
                if 'error' in data:
                    logger.info("✓ Invalid endpoint test passed")
                    self.test_results['invalid_endpoints'] = True
                    return True
            except json.JSONDecodeError:
                logger.error("Invalid endpoint returned invalid JSON")

        logger.error("✗ Invalid endpoint test failed")
        self.test_results['invalid_endpoints'] = False
        return False

    def test_cors_headers(self) -> bool:
        """Test CORS headers are present"""
        logger.info("Testing CORS headers...")

        response = self.make_request('GET', '/health')

        if response and 'Access-Control-Allow-Origin' in response.headers:
            logger.info("✓ CORS headers test passed")
            self.test_results['cors_headers'] = True
            return True

        logger.error("✗ CORS headers test failed")
        self.test_results['cors_headers'] = False
        return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests"""
        logger.info("Starting Frontend Dashboard Mock Server tests...")
        logger.info("=" * 70)

        # Test server connectivity first
        try:
            response = self.make_request('GET', '/health')
            if not response:
                logger.error("Cannot connect to server. Is it running?")
                return {"connection": False}
        except Exception as e:
            logger.error(f"Server connection failed: {e}")
            return {"connection": False}

        # Run all tests
        test_methods = [
            self.test_health_endpoint,
            self.test_get_meetings_endpoint,
            self.test_get_meetings_with_filters,
            self.test_get_summary_endpoint,
            self.test_get_summary_not_found,
            self.test_get_transcripts_endpoint,
            self.test_get_tasks_endpoint,
            self.test_get_tasks_with_filters,
            self.test_get_participants_endpoint,
            self.test_process_transcript_endpoint,
            self.test_process_transcript_with_tools_endpoint,
            self.test_available_tools_endpoint,
            self.test_analytics_overview_endpoint,
            self.test_invalid_endpoints,
            self.test_cors_headers
        ]

        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed with exception: {e}")
                test_name = test_method.__name__.replace('test_', '').replace('_endpoint', '')
                self.test_results[test_name] = False

        return self.test_results

    def print_test_summary(self):
        """Print test results summary"""
        logger.info("=" * 70)
        logger.info("Test Results Summary:")
        logger.info("=" * 70)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        for test_name, passed in self.test_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            time_taken = self.response_times.get(f"/{test_name.replace('_', '-')}", 0)
            time_str = f"({time_taken:.3f}s)" if time_taken > 0 else ""
            logger.info(f"{test_name.replace('_', ' ').title():<35} {status} {time_str}")

        logger.info("-" * 70)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        # Performance summary
        if self.response_times:
            avg_response_time = sum(self.response_times.values()) / len(self.response_times)
            max_response_time = max(self.response_times.values())
            logger.info(f"Average Response Time: {avg_response_time:.3f}s")
            logger.info(f"Max Response Time: {max_response_time:.3f}s")

        if passed_tests == total_tests:
            logger.info("🎉 All tests passed!")
        else:
            logger.warning("⚠️  Some tests failed. Check the logs above.")

        logger.info("=" * 70)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Frontend Dashboard REST API Mock Server")
    parser.add_argument('--server', default='http://localhost:3001',
                       help='Server base URL (default: http://localhost:3001)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run tests
    tester = FrontendDashboardMockServerTest(args.server)

    try:
        results = tester.run_all_tests()
        tester.print_test_summary()

        # Exit with appropriate code
        all_passed = all(results.values()) if results else False
        exit_code = 0 if all_passed else 1

        return exit_code

    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
