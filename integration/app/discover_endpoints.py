#!/usr/bin/env python3
"""
Endpoint Discovery Script for ScrumBot

This script scans the backend API to discover available endpoints related to participant data.
It helps identify which endpoints are implemented and can be used for integration.

Usage:
  python discover_endpoints.py [--url BASE_URL] [--verbose]

Example:
  python discover_endpoints.py --url http://localhost:5167 --verbose
"""

import argparse
import asyncio
import json
import sys
import os
from datetime import datetime
import aiohttp
from typing import Dict, List, Any, Tuple

class EndpointDiscoverer:
    """Discovers available endpoints in the ScrumBot backend"""

    def __init__(self, base_url: str = "http://localhost:5167", verbose: bool = False):
        self.base_url = base_url
        self.verbose = verbose
        self.results = {
            "discovery_time": datetime.now().isoformat(),
            "base_url": base_url,
            "endpoints": {},
            "summary": {
                "total_tested": 0,
                "available": 0,
                "unavailable": 0
            }
        }

    def log(self, message: str):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(message)

    async def check_endpoint(self, endpoint: str, method: str = "GET",
                           data: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """Check if an endpoint is available"""
        url = f"{self.base_url}{endpoint}"
        self.log(f"Testing {method} {url}...")

        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, timeout=5) as response:
                        status = response.status
                        try:
                            response_data = await response.json()
                            content_type = "json"
                        except:
                            response_data = await response.text()
                            content_type = "text"

                elif method == "POST":
                    async with session.post(url, json=data, timeout=5) as response:
                        status = response.status
                        try:
                            response_data = await response.json()
                            content_type = "json"
                        except:
                            response_data = await response.text()
                            content_type = "text"

                is_available = 200 <= status < 500
                result = {
                    "status": status,
                    "available": is_available,
                    "content_type": content_type,
                    "response": response_data if is_available else str(response_data)[:200]
                }

                if is_available:
                    self.log(f"✅ {method} {endpoint} - Status: {status}")
                else:
                    self.log(f"❌ {method} {endpoint} - Status: {status}")

                return is_available, result

        except aiohttp.ClientError as e:
            self.log(f"❌ {method} {endpoint} - Error: {str(e)}")
            return False, {
                "status": 0,
                "available": False,
                "error": str(e),
                "content_type": "error"
            }
        except asyncio.TimeoutError:
            self.log(f"❌ {method} {endpoint} - Timeout")
            return False, {
                "status": 0,
                "available": False,
                "error": "Timeout",
                "content_type": "error"
            }

    async def discover_endpoints(self):
        """Discover available endpoints"""
        print(f"🔍 Discovering endpoints at {self.base_url}...")

        # List of endpoints to check
        endpoints_to_check = [
            # Basic health endpoint
            {"path": "/health", "method": "GET"},

            # Speaker identification endpoints
            {"path": "/identify-speakers", "method": "POST", "data": {
                "text": "John: Hello, Sarah: Hi there!",
                "context": "Known participants: John Smith (host), Sarah Johnson"
            }},
            {"path": "/api/v1/identify-speakers", "method": "POST", "data": {
                "text": "John: Hello, Sarah: Hi there!",
                "context": "Known participants: John Smith (host), Sarah Johnson"
            }},
            {"path": "/speaker-identification", "method": "POST", "data": {
                "text": "John: Hello, Sarah: Hi there!",
                "context": "Known participants: John Smith (host), Sarah Johnson"
            }},

            # Transcript processing endpoints
            {"path": "/process-transcript", "method": "POST", "data": {
                "text": "John: Hello everyone, let's start the meeting.",
                "meeting_id": "test-meeting-001",
                "metadata": {
                    "participants": [
                        {"id": "p1", "name": "John Smith", "is_host": True}
                    ]
                }
            }},
            {"path": "/api/v1/process-transcript", "method": "POST", "data": {
                "text": "John: Hello everyone, let's start the meeting.",
                "meeting_id": "test-meeting-001",
                "metadata": {
                    "participants": [
                        {"id": "p1", "name": "John Smith", "is_host": True}
                    ]
                }
            }},
            {"path": "/transcribe", "method": "POST", "data": {
                "data": "base64_audio_placeholder",
                "metadata": {
                    "participants": [
                        {"id": "p1", "name": "John Smith", "is_host": True}
                    ]
                }
            }},

            # Meeting management endpoints
            {"path": "/meetings", "method": "GET"},
            {"path": "/get-meetings", "method": "GET"},
            {"path": "/meetings", "method": "POST", "data": {
                "meeting_id": "test-meeting-002",
                "meeting_title": "Test Meeting",
                "platform": "test",
                "participants": [
                    {"id": "p1", "name": "John Smith", "is_host": True}
                ]
            }},
            {"path": "/save-meeting", "method": "POST", "data": {
                "meeting_id": "test-meeting-003",
                "meeting_title": "Test Meeting",
                "platform": "test",
                "participants": [
                    {"id": "p1", "name": "John Smith", "is_host": True}
                ]
            }},

            # WebSocket check (this will likely fail as regular HTTP request)
            {"path": "/ws", "method": "GET"},
            {"path": "/ws/audio-stream", "method": "GET"},

            # Tools and integration endpoints
            {"path": "/api/v1/tools", "method": "GET"},
            {"path": "/api/v1/available-tools", "method": "GET"},
        ]

        # Check each endpoint
        for endpoint_info in endpoints_to_check:
            path = endpoint_info["path"]
            method = endpoint_info["method"]
            data = endpoint_info.get("data")

            is_available, result = await self.check_endpoint(path, method, data)

            # Store result
            self.results["endpoints"][f"{method} {path}"] = result

            # Update summary
            self.results["summary"]["total_tested"] += 1
            if is_available:
                self.results["summary"]["available"] += 1
            else:
                self.results["summary"]["unavailable"] += 1

        # Print summary
        print("\n🔍 Endpoint Discovery Summary:")
        print(f"Total Tested: {self.results['summary']['total_tested']}")
        print(f"Available: {self.results['summary']['available']}")
        print(f"Unavailable: {self.results['summary']['unavailable']}")

        # Save results
        filename = f"endpoint_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to {filename}")

        return self.results

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Discover ScrumBot API endpoints")
    parser.add_argument("--url", default="http://localhost:5167", help="Base URL of the API")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    discoverer = EndpointDiscoverer(args.url, args.verbose)
    await discoverer.discover_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
