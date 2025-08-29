"""
SQLite Database Implementation for AI Processing
Wraps the existing DatabaseManager to implement DatabaseInterface
"""

import logging
import sqlite3
import aiosqlite
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from .database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation of DatabaseInterface"""

    def __init__(self, db_path: str = "meeting_minutes.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create meetings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create transcripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    transcript TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    summary TEXT,
                    action_items TEXT,
                    key_points TEXT,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
                )
            """)

            # Create summary_processes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summary_processes (
                    meeting_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT,
                    result TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    processing_time REAL DEFAULT 0.0,
                    metadata TEXT,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcript_chunks (
                    meeting_id TEXT PRIMARY KEY,
                    meeting_name TEXT,
                    transcript_text TEXT NOT NULL,
                    model TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    chunk_size INTEGER,
                    overlap INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
                )
            """)

            # Create settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    whisperModel TEXT NOT NULL,
                    groqApiKey TEXT,
                    openaiApiKey TEXT,
                    anthropicApiKey TEXT,
                    ollamaApiKey TEXT
                )
            """)

            # Create participants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    participant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    platform_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    join_time TEXT NOT NULL,
                    is_host BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
                    UNIQUE(meeting_id, participant_id)
                )
            """)

            conn.commit()

    async def create_process(self, meeting_id: str) -> str:
        """Create a new processing record and return process ID"""
        current_time = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO summary_processes
                (meeting_id, status, created_at, updated_at, start_time, chunk_count, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (meeting_id, "processing", current_time, current_time, current_time, 0, 0.0))

            conn.commit()
            return meeting_id  # Using meeting_id as process_id for simplicity

    async def update_process(self, process_id: str, status: str = None,
                           error: str = None, result: str = None,
                           start_time: str = None, end_time: str = None,
                           chunk_count: int = None, processing_time: float = None,
                           metadata: str = None) -> bool:
        """Update process record with new information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build dynamic update query
                updates = ["updated_at = ?"]
                params = [datetime.utcnow().isoformat()]

                if status is not None:
                    updates.append("status = ?")
                    params.append(status)
                if error is not None:
                    updates.append("error = ?")
                    params.append(error)
                if result is not None:
                    updates.append("result = ?")
                    params.append(result)
                if start_time is not None:
                    updates.append("start_time = ?")
                    params.append(start_time)
                if end_time is not None:
                    updates.append("end_time = ?")
                    params.append(end_time)
                if chunk_count is not None:
                    updates.append("chunk_count = ?")
                    params.append(chunk_count)
                if processing_time is not None:
                    updates.append("processing_time = ?")
                    params.append(processing_time)
                if metadata is not None:
                    updates.append("metadata = ?")
                    params.append(metadata)

                params.append(process_id)

                query = f"UPDATE summary_processes SET {', '.join(updates)} WHERE meeting_id = ?"
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating process {process_id}: {e}")
            return False

    async def save_transcript(self, meeting_id: str, transcript: str, model: str,
                             model_name: str, chunk_size: int, overlap: int) -> bool:
        """Save transcript data"""
        try:
            current_time = datetime.utcnow().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO transcript_chunks
                    (meeting_id, transcript_text, model, model_name, chunk_size, overlap, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (meeting_id, transcript, model, model_name, chunk_size, overlap, current_time))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
            return False

    async def update_meeting_name(self, meeting_id: str, name: str) -> bool:
        """Update meeting name"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE transcript_chunks SET meeting_name = ? WHERE meeting_id = ?
                """, (name, meeting_id))

                # Also update the meetings table title if it's empty or generic
                cursor.execute("""
                    UPDATE meetings SET title = ?, updated_at = ?
                    WHERE id = ? AND (title = '' OR title = 'Meeting')
                """, (name, datetime.utcnow().isoformat(), meeting_id))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating meeting name: {e}")
            return False

    async def get_transcript_data(self, meeting_id: str) -> Optional[Dict]:
        """Get transcript data for a meeting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get transcript chunk data
                cursor.execute("""
                    SELECT meeting_name, transcript_text, model, model_name, chunk_size, overlap, created_at
                    FROM transcript_chunks WHERE meeting_id = ?
                """, (meeting_id,))

                chunk_data = cursor.fetchone()
                if not chunk_data:
                    return None

                # Get process data
                cursor.execute("""
                    SELECT status, result, start_time, end_time, chunk_count, processing_time, error
                    FROM summary_processes WHERE meeting_id = ?
                """, (meeting_id,))

                process_data = cursor.fetchone()

                result = {
                    "meeting_id": meeting_id,
                    "meeting_name": chunk_data[0],
                    "transcript_text": chunk_data[1],
                    "model": chunk_data[2],
                    "model_name": chunk_data[3],
                    "chunk_size": chunk_data[4],
                    "overlap": chunk_data[5],
                    "created_at": chunk_data[6]
                }

                if process_data:
                    result.update({
                        "status": process_data[0],
                        "result": process_data[1],
                        "start_time": process_data[2],
                        "end_time": process_data[3],
                        "chunk_count": process_data[4],
                        "processing_time": process_data[5],
                        "error": process_data[6]
                    })

                return result

        except Exception as e:
            logger.error(f"Error getting transcript data: {e}")
            return None

    async def save_meeting(self, meeting_id: str, title: str) -> bool:
        """Save meeting information"""
        try:
            current_time = datetime.utcnow().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if meeting exists
                cursor.execute("SELECT id FROM meetings WHERE id = ?", (meeting_id,))
                existing = cursor.fetchone()

                if not existing:
                    cursor.execute("""
                        INSERT INTO meetings (id, title, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (meeting_id, title, current_time, current_time))
                else:
                    cursor.execute("""
                        UPDATE meetings SET title = ?, updated_at = ? WHERE id = ?
                    """, (title, current_time, meeting_id))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving meeting: {e}")
            return False

    async def save_meeting_transcript(self, meeting_id: str, transcript: str,
                                    timestamp: str, summary: str = "",
                                    action_items: str = "", key_points: str = "") -> bool:
        """Save meeting transcript segment"""
        try:
            transcript_id = f"transcript-{uuid.uuid4()}"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO transcripts
                    (id, meeting_id, transcript, timestamp, summary, action_items, key_points)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (transcript_id, meeting_id, transcript, timestamp, summary, action_items, key_points))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving meeting transcript: {e}")
            return False

    async def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        """Get meeting by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, title, created_at, updated_at FROM meetings WHERE id = ?
                """, (meeting_id,))

                meeting_data = cursor.fetchone()
                if not meeting_data:
                    return None

                # Get transcripts
                cursor.execute("""
                    SELECT id, transcript, timestamp, summary, action_items, key_points
                    FROM transcripts WHERE meeting_id = ? ORDER BY timestamp
                """, (meeting_id,))

                transcripts = cursor.fetchall()

                # Get participants
                participants = await self.get_participants(meeting_id)

                return {
                    "id": meeting_data[0],
                    "title": meeting_data[1],
                    "created_at": meeting_data[2],
                    "updated_at": meeting_data[3],
                    "transcripts": [
                        {
                            "id": t[0],
                            "text": t[1],
                            "timestamp": t[2],
                            "summary": t[3],
                            "action_items": t[4],
                            "key_points": t[5]
                        }
                        for t in transcripts
                    ],
                    "participants": participants
                }
        except Exception as e:
            logger.error(f"Error getting meeting: {e}")
            return None

    async def update_meeting_title(self, meeting_id: str, title: str) -> bool:
        """Update meeting title"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE meetings SET title = ?, updated_at = ? WHERE id = ?
                """, (title, datetime.utcnow().isoformat(), meeting_id))

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating meeting title: {e}")
            return False

    async def get_all_meetings(self) -> List[Dict]:
        """Get all meetings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, title, created_at, updated_at FROM meetings
                    ORDER BY updated_at DESC
                """)

                meetings = cursor.fetchall()
                return [
                    {
                        "id": m[0],
                        "title": m[1],
                        "created_at": m[2],
                        "updated_at": m[3]
                    }
                    for m in meetings
                ]
        except Exception as e:
            logger.error(f"Error getting all meetings: {e}")
            return []

    async def delete_meeting(self, meeting_id: str) -> bool:
        """Delete meeting and related data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete in order due to foreign key constraints
                cursor.execute("DELETE FROM participants WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM transcripts WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM transcript_chunks WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM summary_processes WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting meeting: {e}")
            return False

    # Participant management methods
    async def save_participant(self, meeting_id: str, participant_id: str,
                              name: str, platform_id: str, status: str,
                              join_time: str, is_host: bool = False) -> bool:
        """Save participant information"""
        try:
            participant_table_id = f"participant-{uuid.uuid4()}"
            current_time = datetime.utcnow().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO participants
                    (id, meeting_id, participant_id, name, platform_id, status, join_time, is_host, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (participant_table_id, meeting_id, participant_id, name, platform_id,
                     status, join_time, int(is_host), current_time))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving participant: {e}")
            return False

    async def get_participants(self, meeting_id: str) -> List[Dict]:
        """Get all participants for a meeting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT participant_id, name, platform_id, status, join_time, is_host, created_at
                    FROM participants WHERE meeting_id = ? ORDER BY join_time
                """, (meeting_id,))

                participants = cursor.fetchall()
                return [
                    {
                        "id": p[0],
                        "name": p[1],
                        "platform_id": p[2],
                        "status": p[3],
                        "join_time": p[4],
                        "is_host": bool(p[5]),
                        "created_at": p[6]
                    }
                    for p in participants
                ]
        except Exception as e:
            logger.error(f"Error getting participants: {e}")
            return []

    async def update_participant_status(self, meeting_id: str, participant_id: str,
                                       status: str) -> bool:
        """Update participant status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE participants SET status = ?
                    WHERE meeting_id = ? AND participant_id = ?
                """, (status, meeting_id, participant_id))

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating participant status: {e}")
            return False

    async def save_participants_batch(self, meeting_id: str, participants: List[Dict]) -> bool:
        """Save multiple participants at once"""
        try:
            current_time = datetime.utcnow().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for participant in participants:
                    participant_table_id = f"participant-{uuid.uuid4()}"

                    cursor.execute("""
                        INSERT OR REPLACE INTO participants
                        (id, meeting_id, participant_id, name, platform_id, status, join_time, is_host, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        participant_table_id,
                        meeting_id,
                        participant.get("id", participant.get("participant_id")),
                        participant.get("name", "Unknown"),
                        participant.get("platform_id", participant.get("id")),
                        participant.get("status", "active"),
                        participant.get("join_time", current_time),
                        int(participant.get("is_host", False)),
                        current_time
                    ))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving participants batch: {e}")
            return False

    # Configuration management
    async def get_model_config(self) -> Optional[Dict]:
        """Get current model configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT provider, model, whisperModel FROM settings LIMIT 1")
                config = cursor.fetchone()

                if config:
                    return {
                        "provider": config[0],
                        "model": config[1],
                        "whisperModel": config[2]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting model config: {e}")
            return None

    async def save_model_config(self, provider: str, model: str, whisper_model: str) -> bool:
        """Save model configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete existing config
                cursor.execute("DELETE FROM settings")

                # Insert new config
                cursor.execute("""
                    INSERT INTO settings (id, provider, model, whisperModel)
                    VALUES (?, ?, ?, ?)
                """, ("default_config", provider, model, whisper_model))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving model config: {e}")
            return False

    async def save_api_key(self, api_key: str, provider: str) -> bool:
        """Save API key for a provider"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Map provider to column
                key_column = f"{provider}ApiKey"

                cursor.execute(f"""
                    UPDATE settings SET {key_column} = ? WHERE id = 'default_config'
                """, (api_key,))

                if cursor.rowcount == 0:
                    # Create settings record if it doesn't exist
                    cursor.execute(f"""
                        INSERT INTO settings (id, provider, model, whisperModel, {key_column})
                        VALUES ('default_config', ?, ?, ?, ?)
                    """, (provider, "gpt-3.5-turbo", "whisper-1", api_key))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            return False

    async def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                key_column = f"{provider}ApiKey"
                cursor.execute(f"SELECT {key_column} FROM settings WHERE id = 'default_config'")

                result = cursor.fetchone()
                return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None

    async def delete_api_key(self, provider: str) -> bool:
        """Delete API key for a provider"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                key_column = f"{provider}ApiKey"
                cursor.execute(f"UPDATE settings SET {key_column} = NULL WHERE id = 'default_config'")

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False

    # Utility methods
    def clear_all(self) -> bool:
        """Clear all data (for testing)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM participants")
                cursor.execute("DELETE FROM transcript_chunks")
                cursor.execute("DELETE FROM summary_processes")
                cursor.execute("DELETE FROM transcripts")
                cursor.execute("DELETE FROM meetings")
                cursor.execute("DELETE FROM settings")

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing all data: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False