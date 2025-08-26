#!/usr/bin/env python3
"""
REST API Mock Server for Frontend Dashboard Testing

This server provides mock REST API endpoints that the frontend dashboard
expects, returning realistic data based on the enhanced audio integration contracts.
"""

import json
import logging
import os
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FrontendDashboardMockServer:
    """Mock REST API server for frontend dashboard testing"""

    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for frontend development

        # Load mock data
        self.mock_data_path = os.path.join(os.path.dirname(__file__), '..', 'shared', 'mock-meetings-data.json')
        self.mock_data = self.load_mock_data()

        # Setup routes
        self.setup_routes()

    def load_mock_data(self) -> dict:
        """Load mock meetings data from JSON file"""
        try:
            with open(self.mock_data_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded mock data with {len(data.get('meetings', []))} meetings")
                return data
        except FileNotFoundError:
            logger.error(f"Mock data file not found: {self.mock_data_path}")
            return {"meetings": [], "transcripts": {}, "speakers": {}, "summaries": {}, "tasks": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mock data file: {e}")
            return {"meetings": [], "transcripts": {}, "speakers": {}, "summaries": {}, "tasks": {}}

    def setup_routes(self):
        """Setup all API routes"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "server": "Frontend Dashboard Mock Server",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0"
            })

        @self.app.route('/get-meetings', methods=['GET'])
        def get_meetings():
            """Get all meetings with optional filtering"""
            try:
                meetings = self.mock_data.get('meetings', [])

                # Apply query parameters for filtering
                status_filter = request.args.get('status')
                platform_filter = request.args.get('platform')
                limit = request.args.get('limit', type=int)

                filtered_meetings = meetings.copy()

                if status_filter:
                    filtered_meetings = [m for m in filtered_meetings if m.get('status') == status_filter]

                if platform_filter:
                    filtered_meetings = [m for m in filtered_meetings if m.get('platform') == platform_filter]

                if limit:
                    filtered_meetings = filtered_meetings[:limit]

                # Add some dynamic data for realism
                for meeting in filtered_meetings:
                    if meeting.get('status') == 'in_progress':
                        # Update in-progress meetings with current time
                        meeting['updated_at'] = datetime.now(timezone.utc).isoformat()

                logger.info(f"Returned {len(filtered_meetings)} meetings (filtered from {len(meetings)})")

                return jsonify({
                    "meetings": filtered_meetings,
                    "total_count": len(meetings),
                    "filtered_count": len(filtered_meetings),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            except Exception as e:
                logger.error(f"Error in get_meetings: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route('/get-summary/<meeting_id>', methods=['GET'])
        def get_summary(meeting_id: str):
            """Get meeting summary by ID"""
            try:
                # Check if meeting exists
                meetings = self.mock_data.get('meetings', [])
                meeting = next((m for m in meetings if m['id'] == meeting_id), None)

                if not meeting:
                    return jsonify({"error": f"Meeting {meeting_id} not found"}), 404

                # Get summary data
                summaries = self.mock_data.get('summaries', {})
                speakers = self.mock_data.get('speakers', {})
                tasks = self.mock_data.get('tasks', {})

                if meeting_id not in summaries:
                    return jsonify({
                        "status": "processing",
                        "meeting_id": meeting_id,
                        "message": "Summary is being generated",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                response_data = {
                    "status": "completed",
                    "meeting_id": meeting_id,
                    "data": {
                        "speakers": speakers.get(meeting_id, {}),
                        "summary": summaries.get(meeting_id, {}),
                        "tasks": tasks.get(meeting_id, []),
                        "participants": summaries.get(meeting_id, {}).get('participants', {}),
                        "meeting": meeting
                    },
                    "generated_at": summaries.get(meeting_id, {}).get('summary_generated_at'),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                logger.info(f"Returned summary for meeting {meeting_id}")
                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error in get_summary for {meeting_id}: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route('/get-transcripts/<meeting_id>', methods=['GET'])
        def get_transcripts(meeting_id: str):
            """Get meeting transcripts by ID"""
            try:
                transcripts = self.mock_data.get('transcripts', {})

                if meeting_id not in transcripts:
                    return jsonify({"error": f"Transcripts for meeting {meeting_id} not found"}), 404

                meeting_transcripts = transcripts[meeting_id]

                # Apply pagination
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 50, type=int)
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page

                paginated_transcripts = meeting_transcripts[start_idx:end_idx]

                response_data = {
                    "meeting_id": meeting_id,
                    "transcripts": paginated_transcripts,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": len(meeting_transcripts),
                        "pages": (len(meeting_transcripts) + per_page - 1) // per_page
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                logger.info(f"Returned {len(paginated_transcripts)} transcripts for meeting {meeting_id}")
                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error in get_transcripts for {meeting_id}: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route('/get-tasks', methods=['GET'])
        def get_tasks():
            """Get tasks with optional filtering"""
            try:
                all_tasks = []
                tasks_data = self.mock_data.get('tasks', {})

                # Flatten all tasks from all meetings
                for meeting_id, meeting_tasks in tasks_data.items():
                    all_tasks.extend(meeting_tasks)

                # Apply filters
                assignee_filter = request.args.get('assignee')
                status_filter = request.args.get('status')
                priority_filter = request.args.get('priority')

                filtered_tasks = all_tasks.copy()

                if assignee_filter:
                    filtered_tasks = [t for t in filtered_tasks if t.get('assignee', '').lower() == assignee_filter.lower()]

                if status_filter:
                    filtered_tasks = [t for t in filtered_tasks if t.get('status') == status_filter]

                if priority_filter:
                    filtered_tasks = [t for t in filtered_tasks if t.get('priority') == priority_filter]

                # Sort by due date
                filtered_tasks.sort(key=lambda x: x.get('due_date', ''))

                response_data = {
                    "tasks": filtered_tasks,
                    "total_count": len(all_tasks),
                    "filtered_count": len(filtered_tasks),
                    "filters_applied": {
                        "assignee": assignee_filter,
                        "status": status_filter,
                        "priority": priority_filter
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                logger.info(f"Returned {len(filtered_tasks)} tasks (filtered from {len(all_tasks)})")
                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error in get_tasks: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route('/get-participants/<meeting_id>', methods=['GET'])
        def get_participants(meeting_id: str):
            """Get participants for a specific meeting"""
            try:
                meetings = self.mock_data.get('meetings', [])
                meeting = next((m for m in meetings if m['id'] == meeting_id), None)

                if not meeting:
                    return jsonify({"error": f"Meeting {meeting_id} not found"}), 404

                participants = meeting.get('participants', [])

                # Add basic engagement metrics from summary if available
                summaries = self.mock_data.get('summaries', {})
                if meeting_id in summaries:
                    summary_participants = summaries[meeting_id].get('participants', {}).get('participants', [])
                    # Add only basic participant information that our system supports
                    for participant in participants:
                        summary_data = next((sp for sp in summary_participants if sp['name'] == participant['name']), None)
                        if summary_data:
                            # Only add supported fields (just the name, which we already have)
                            pass  # No additional fields are currently supported

                response_data = {
                    "meeting_id": meeting_id,
                    "participants": participants,
                    "total_participants": len(participants),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                logger.info(f"Returned {len(participants)} participants for meeting {meeting_id}")
                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error in get_participants for {meeting_id}: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route('/process-transcript', methods=['POST'])
        def process_transcript():
            """Mock endpoint for transcript processing"""
            try:
                data = request.get_json()

                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                text = data.get('text', '')
                meeting_id = data.get('meeting_id', f'mock_meeting_{random.randint(1000, 9999)}')
                model = data.get('model', 'ollama')
                model_name = data.get('model_name', 'llama3.2:1b')

                if not text:
                    return jsonify({"error": "Text field is required"}), 400

                # Generate mock process ID
                process_id = f"process_{random.randint(100000, 999999)}"

                response_data = {
                    "process_id": process_id,
                    "status": "processing",
                    "meeting_id": meeting_id,
                    "model": model,
                    "model_name": model_name,
                    "text_length": len(text),
                    "estimated_completion": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                logger.info(f"Started processing transcript for meeting {meeting_id} (process: {process_id})")
                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error in process_transcript: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route('/process-transcript-with-tools', methods=['POST'])
        def process_transcript_with_tools():
            """Mock endpoint for transcript processing with tools"""
            try:
                data = request.get_json()

                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                text = data.get('text', '')
                meeting_id = data.get('meeting_id', f'mock_meeting_{random.randint(1000, 9999)}')
                participants = data.get('participants', [])

                if not text:
                    return jsonify({"error": "Text field is required"}), 400

                # Mock AI analysis and tools execution
                mock_analysis = f"Analysis of {len(text)} characters of meeting transcript with {len(participants)} participants identified."

                mock_speakers = []
                for i, participant in enumerate(participants):
                    mock_speakers.append({
                        "id": participant.get('id', f'participant_{i}'),
                        "name": participant.get('name', f'Participant {i+1}'),
                        "segments": [f"Sample segment from {participant.get('name', f'Participant {i+1}')}"],
                        "total_words": random.randint(50, 200),
                        "confidence": random.uniform(0.85, 0.98)
                    })

                mock_actions = [
                    {
                        "tool": "create_notion_task",
                        "arguments": {"task": "Sample task from meeting", "assignee": "Team Member"},
                        "result": {"status": "success", "task_id": f"task_{random.randint(1000, 9999)}"}
                    },
                    {
                        "tool": "send_slack_notification",
                        "arguments": {"message": "Meeting summary ready", "channel": "#team"},
                        "result": {"status": "success", "message_id": f"msg_{random.randint(1000, 9999)}"}
                    }
                ]

                response_data = {
                    "status": "success",
                    "meeting_id": meeting_id,
                    "analysis": mock_analysis,
                    "speakers": mock_speakers,
                    "actions_taken": mock_actions,
                    "tools_used": len(mock_actions),
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }

                logger.info(f"Processed transcript with tools for meeting {meeting_id}")
                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error in process_transcript_with_tools: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route('/available-tools', methods=['GET'])
        def get_available_tools():
            """Get available tools for processing"""
            mock_tools = [
                {
                    "name": "create_notion_task",
                    "description": "Create tasks in Notion workspace",
                    "parameters": ["task", "assignee", "due_date", "priority"]
                },
                {
                    "name": "send_slack_notification",
                    "description": "Send notifications to Slack channels",
                    "parameters": ["message", "channel", "urgency"]
                },
                {
                    "name": "create_calendar_event",
                    "description": "Schedule follow-up meetings",
                    "parameters": ["title", "datetime", "attendees", "duration"]
                },
                {
                    "name": "update_project_status",
                    "description": "Update project tracking systems",
                    "parameters": ["project_id", "status", "progress", "notes"]
                }
            ]

            response_data = {
                "tools": mock_tools,
                "tool_names": [tool["name"] for tool in mock_tools],
                "count": len(mock_tools),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            return jsonify(response_data)

        @self.app.route('/analytics/overview', methods=['GET'])
        def get_analytics_overview():
            """Get analytics overview dashboard data"""
            try:
                meetings = self.mock_data.get('meetings', [])
                tasks_data = self.mock_data.get('tasks', {})

                # Calculate metrics
                total_meetings = len(meetings)
                completed_meetings = len([m for m in meetings if m.get('status') == 'completed'])
                in_progress_meetings = len([m for m in meetings if m.get('status') == 'in_progress'])

                # Task metrics
                all_tasks = []
                for meeting_tasks in tasks_data.values():
                    all_tasks.extend(meeting_tasks)

                total_tasks = len(all_tasks)
                pending_tasks = len([t for t in all_tasks if t.get('status') == 'pending'])
                in_progress_tasks = len([t for t in all_tasks if t.get('status') == 'in_progress'])
                completed_tasks = len([t for t in all_tasks if t.get('status') == 'completed'])

                response_data = {
                    "meetings": {
                        "total": total_meetings,
                        "completed": completed_meetings,
                        "in_progress": in_progress_meetings,
                        "completion_rate": completed_meetings / max(total_meetings, 1)
                    },
                    "tasks": {
                        "total": total_tasks,
                        "pending": pending_tasks,
                        "in_progress": in_progress_tasks,
                        "completed": completed_tasks,
                        "completion_rate": completed_tasks / max(total_tasks, 1)
                    },
                    "platforms": {
                        "google-meet": len([m for m in meetings if m.get('platform') == 'google-meet']),
                        "zoom": len([m for m in meetings if m.get('platform') == 'zoom']),
                        "teams": len([m for m in meetings if m.get('platform') == 'teams'])
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error in analytics_overview: {e}")
                return jsonify({"error": "Internal server error"}), 500

        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "Endpoint not found"}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({"error": "Internal server error"}), 500

    def run(self, host: str = "0.0.0.0", port: int = 3001, debug: bool = False):
        """Run the mock server"""
        logger.info(f"Starting Frontend Dashboard Mock Server on http://{host}:{port}")
        logger.info(f"Available endpoints:")
        logger.info(f"  - GET  /health")
        logger.info(f"  - GET  /get-meetings")
        logger.info(f"  - GET  /get-summary/<meeting_id>")
        logger.info(f"  - GET  /get-transcripts/<meeting_id>")
        logger.info(f"  - GET  /get-tasks")
        logger.info(f"  - GET  /get-participants/<meeting_id>")
        logger.info(f"  - POST /process-transcript")
        logger.info(f"  - POST /process-transcript-with-tools")
        logger.info(f"  - GET  /available-tools")
        logger.info(f"  - GET  /analytics/overview")

        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Frontend Dashboard REST API Mock Server")
    parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=3001, help='Server port (default: 3001)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and start server
    mock_server = FrontendDashboardMockServer()
    mock_server.run(args.host, args.port, args.debug)

if __name__ == "__main__":
    main()
