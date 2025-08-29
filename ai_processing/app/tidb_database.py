"""
TiDB Database Implementation for AI Processing
Uses TiDB for production deployment in the AgentX 2025 hackathon
"""

import logging
import json
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from .database_interface import DatabaseInterface

# Try to import mysql connector
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    mysql = None
    Error = Exception

logger = logging.getLogger(__name__)


class TiDBDatabase(DatabaseInterface):
    """TiDB implementation of DatabaseInterface for hackathon production deployment"""

    def __init__(self, host: str, port: int = 4000, user: str = None,
                 password: str = None, database: str = "scrumy_ai",
                 ssl_mode: str = "REQUIRED", **kwargs):

        if not MYSQL_AVAILABLE:
            raise ImportError("mysql-connector-python is required for TiDB. Install with: pip install mysql-connector-python")

        self.connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'ssl_disabled': ssl_mode != "REQUIRED",
            'autocommit': True
        }

        # Add any additional connection parameters
        self.connection_params.update(kwargs)

        self.connection = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize TiDB connection and create tables"""
        try:
            self.connection = mysql.connector.connect(**self.connection_params)
            if self.connection.is_connected():
                logger.info("Successfully connected to TiDB")
                self._init_tables()
            else:
                raise ConnectionError("Failed to connect to TiDB")
        except Error as e:
            logger.error(f"Error connecting to TiDB: {e}")
            raise

    def _init_tables(self):
        """Create tables if they don't exist"""
        cursor = self.connection.cursor()

        try:
            # Meetings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id VARCHAR(255) PRIMARY KEY,
                    title VARCHAR(500) NOT NULL DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            # Transcripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id VARCHAR(255) PRIMARY KEY,
                    meeting_id VARCHAR(255) NOT NULL,
                    transcript TEXT NOT NULL,
                    timestamp VARCHAR(255) NOT NULL,
                    summary TEXT DEFAULT '',
                    action_items TEXT DEFAULT '',
                    key_points TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                    INDEX idx_meeting_timestamp (meeting_id, timestamp)
                )
            """)

            # Summary processes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summary_processes (
                    meeting_id VARCHAR(255) PRIMARY KEY,
                    status VARCHAR(50) NOT NULL DEFAULT 'processing',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    error TEXT,
                    result TEXT,
                    start_time VARCHAR(255),
                    end_time VARCHAR(255),
                    chunk_count INTEGER DEFAULT 0,
                    processing_time FLOAT DEFAULT 0.0,
                    metadata TEXT,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
                )
            """)

            # Transcript chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcript_chunks (
                    meeting_id VARCHAR(255) PRIMARY KEY,
                    meeting_name VARCHAR(500),
                    transcript_text TEXT NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    chunk_size INTEGER,
                    overlap INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id VARCHAR(255) PRIMARY KEY,
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    whisperModel VARCHAR(100) NOT NULL,
                    groqApiKey TEXT,
                    openaiApiKey TEXT,
                    anthropicApiKey TEXT,
                    ollamaApiKey TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            # Participants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id VARCHAR(255) PRIMARY KEY,
                    meeting_id VARCHAR(255) NOT NULL,
                    participant_id VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    platform_id VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    join_time VARCHAR(255) NOT NULL,
                    is_host BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_meeting_participant (meeting_id, participant_id),
                    INDEX idx_meeting_status (meeting_id, status)
                )
            """)

            self.connection.commit()
            logger.info("TiDB tables initialized successfully")

        except Error as e:
            logger.error(f"Error creating TiDB tables: {e}")
            raise
        finally:
            cursor.close()

    def _get_cursor(self):
        """Get a cursor, reconnecting if necessary"""
        try:
            if not self.connection or not self.connection.is_connected():
                self._initialize_connection()
            return self.connection.cursor(dictionary=True)
        except Error as e:
            logger.error(f"Error getting cursor: {e}")
            raise

    async def create_process(self, meeting_id: str) -> str:
        """Create a new processing record and return process ID"""
        cursor = self._get_cursor()
        try:
            current_time = datetime.utcnow().isoformat()

            cursor.execute("""
                INSERT INTO summary_processes
                (meeting_id, status, created_at, updated_at, start_time, chunk_count, processing_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                updated_at = VALUES(updated_at),
                start_time = VALUES(start_time)
            """, (meeting_id, "processing", current_time, current_time, current_time, 0, 0.0))

            self.connection.commit()
            return meeting_id  # Using meeting_id as process_id
        except Error as e:
            logger.error(f"Error creating process: {e}")
            raise
        finally:
            cursor.close()

    async def update_process(self, process_id: str, status: str = None,
                           error: str = None, result: str = None,
                           start_time: str = None, end_time: str = None,
                           chunk_count: int = None, processing_time: float = None,
                           metadata: str = None) -> bool:
        """Update process record with new information"""
        cursor = self._get_cursor()
        try:
            # Build dynamic update query
            updates = ["updated_at = %s"]
            params = [datetime.utcnow().isoformat()]

            if status is not None:
                updates.append("status = %s")
                params.append(status)
            if error is not None:
                updates.append("error = %s")
                params.append(error)
            if result is not None:
                updates.append("result = %s")
                params.append(result)
            if start_time is not None:
                updates.append("start_time = %s")
                params.append(start_time)
            if end_time is not None:
                updates.append("end_time = %s")
                params.append(end_time)
            if chunk_count is not None:
                updates.append("chunk_count = %s")
                params.append(chunk_count)
            if processing_time is not None:
                updates.append("processing_time = %s")
                params.append(processing_time)
            if metadata is not None:
                updates.append("metadata = %s")
                params.append(metadata)

            params.append(process_id)

            query = f"UPDATE summary_processes SET {', '.join(updates)} WHERE meeting_id = %s"
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            logger.error(f"Error updating process {process_id}: {e}")
            return False
        finally:
            cursor.close()

    async def save_transcript(self, meeting_id: str, transcript: str, model: str,
                             model_name: str, chunk_size: int, overlap: int) -> bool:
        """Save transcript data"""
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                INSERT INTO transcript_chunks
                (meeting_id, transcript_text, model, model_name, chunk_size, overlap)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                transcript_text = VALUES(transcript_text),
                model = VALUES(model),
                model_name = VALUES(model_name),
                chunk_size = VALUES(chunk_size),
                overlap = VALUES(overlap)
            """, (meeting_id, transcript, model, model_name, chunk_size, overlap))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving transcript: {e}")
            return False
        finally:
            cursor.close()

    async def update_meeting_name(self, meeting_id: str, name: str) -> bool:
        """Update meeting name"""
        cursor = self._get_cursor()
        try:
            # Update transcript chunks
            cursor.execute("""
                UPDATE transcript_chunks SET meeting_name = %s WHERE meeting_id = %s
            """, (name, meeting_id))

            # Also update the meetings table title if it's empty or generic
            cursor.execute("""
                UPDATE meetings SET title = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND (title = '' OR title = 'Meeting')
            """, (name, meeting_id))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error updating meeting name: {e}")
            return False
        finally:
            cursor.close()

    async def get_transcript_data(self, meeting_id: str) -> Optional[Dict]:
        """Get transcript data for a meeting"""
        cursor = self._get_cursor()
        try:
            # Get transcript chunk data
            cursor.execute("""
                SELECT meeting_name, transcript_text, model, model_name, chunk_size, overlap, created_at
                FROM transcript_chunks WHERE meeting_id = %s
            """, (meeting_id,))

            chunk_data = cursor.fetchone()
            if not chunk_data:
                return None

            # Get process data
            cursor.execute("""
                SELECT status, result, start_time, end_time, chunk_count, processing_time, error
                FROM summary_processes WHERE meeting_id = %s
            """, (meeting_id,))

            process_data = cursor.fetchone()

            result = {
                "meeting_id": meeting_id,
                "meeting_name": chunk_data["meeting_name"],
                "transcript_text": chunk_data["transcript_text"],
                "model": chunk_data["model"],
                "model_name": chunk_data["model_name"],
                "chunk_size": chunk_data["chunk_size"],
                "overlap": chunk_data["overlap"],
                "created_at": chunk_data["created_at"].isoformat() if chunk_data["created_at"] else None
            }

            if process_data:
                result.update({
                    "status": process_data["status"],
                    "result": process_data["result"],
                    "start_time": process_data["start_time"],
                    "end_time": process_data["end_time"],
                    "chunk_count": process_data["chunk_count"],
                    "processing_time": process_data["processing_time"],
                    "error": process_data["error"]
                })

            return result

        except Error as e:
            logger.error(f"Error getting transcript data: {e}")
            return None
        finally:
            cursor.close()

    async def save_meeting(self, meeting_id: str, title: str) -> bool:
        """Save meeting information"""
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                INSERT INTO meetings (id, title)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                updated_at = CURRENT_TIMESTAMP
            """, (meeting_id, title))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving meeting: {e}")
            return False
        finally:
            cursor.close()

    async def save_meeting_transcript(self, meeting_id: str, transcript: str,
                                    timestamp: str, summary: str = "",
                                    action_items: str = "", key_points: str = "") -> bool:
        """Save meeting transcript segment"""
        cursor = self._get_cursor()
        try:
            transcript_id = f"transcript-{uuid.uuid4()}"

            cursor.execute("""
                INSERT INTO transcripts
                (id, meeting_id, transcript, timestamp, summary, action_items, key_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (transcript_id, meeting_id, transcript, timestamp, summary, action_items, key_points))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving meeting transcript: {e}")
            return False
        finally:
            cursor.close()

    async def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        """Get meeting by ID"""
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                SELECT id, title, created_at, updated_at FROM meetings WHERE id = %s
            """, (meeting_id,))

            meeting_data = cursor.fetchone()
            if not meeting_data:
                return None

            # Get transcripts
            cursor.execute("""
                SELECT id, transcript, timestamp, summary, action_items, key_points
                FROM transcripts WHERE meeting_id = %s ORDER BY timestamp
            """, (meeting_id,))

            transcripts = cursor.fetchall()

            # Get participants
            participants = await self.get_participants(meeting_id)

            return {
                "id": meeting_data["id"],
                "title": meeting_data["title"],
                "created_at": meeting_data["created_at"].isoformat() if meeting_data["created_at"] else None,
                "updated_at": meeting_data["updated_at"].isoformat() if meeting_data["updated_at"] else None,
                "transcripts": [
                    {
                        "id": t["id"],
                        "text": t["transcript"],
                        "timestamp": t["timestamp"],
                        "summary": t["summary"],
                        "action_items": t["action_items"],
                        "key_points": t["key_points"]
                    }
                    for t in transcripts
                ],
                "participants": participants
            }
        except Error as e:
            logger.error(f"Error getting meeting: {e}")
            return None
        finally:
            cursor.close()

    async def update_meeting_title(self, meeting_id: str, title: str) -> bool:
        """Update meeting title"""
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                UPDATE meetings SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
            """, (title, meeting_id))

            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            logger.error(f"Error updating meeting title: {e}")
            return False
        finally:
            cursor.close()

    async def get_all_meetings(self) -> List[Dict]:
        """Get all meetings"""
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                SELECT id, title, created_at, updated_at FROM meetings
                ORDER BY updated_at DESC
            """)

            meetings = cursor.fetchall()
            return [
                {
                    "id": m["id"],
                    "title": m["title"],
                    "created_at": m["created_at"].isoformat() if m["created_at"] else None,
                    "updated_at": m["updated_at"].isoformat() if m["updated_at"] else None
                }
                for m in meetings
            ]
        except Error as e:
            logger.error(f"Error getting all meetings: {e}")
            return []
        finally:
            cursor.close()

    async def delete_meeting(self, meeting_id: str) -> bool:
        """Delete meeting and related data"""
        cursor = self._get_cursor()
        try:
            # TiDB handles cascading deletes via foreign keys
            cursor.execute("DELETE FROM meetings WHERE id = %s", (meeting_id,))

            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            logger.error(f"Error deleting meeting: {e}")
            return False
        finally:
            cursor.close()

    # Participant management methods
    async def save_participant(self, meeting_id: str, participant_id: str,
                              name: str, platform_id: str, status: str,
                              join_time: str, is_host: bool = False) -> bool:
        """Save participant information"""
        cursor = self._get_cursor()
        try:
            participant_table_id = f"participant-{uuid.uuid4()}"

            cursor.execute("""
                INSERT INTO participants
                (id, meeting_id, participant_id, name, platform_id, status, join_time, is_host)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                platform_id = VALUES(platform_id),
                status = VALUES(status),
                is_host = VALUES(is_host)
            """, (participant_table_id, meeting_id, participant_id, name, platform_id,
                 status, join_time, is_host))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving participant: {e}")
            return False
        finally:
            cursor.close()

    async def get_participants(self, meeting_id: str) -> List[Dict]:
        """Get all participants for a meeting"""
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                SELECT participant_id, name, platform_id, status, join_time, is_host, created_at
                FROM participants WHERE meeting_id = %s ORDER BY join_time
            """, (meeting_id,))

            participants = cursor.fetchall()
            return [
                {
                    "id": p["participant_id"],
                    "name": p["name"],
                    "platform_id": p["platform_id"],
                    "status": p["status"],
                    "join_time": p["join_time"],
                    "is_host": bool(p["is_host"]),
                    "created_at": p["created_at"].isoformat() if p["created_at"] else None
                }
                for p in participants
            ]
        except Error as e:
            logger.error(f"Error getting participants: {e}")
            return []
        finally:
            cursor.close()

    async def update_participant_status(self, meeting_id: str, participant_id: str,
                                       status: str) -> bool:
        """Update participant status"""
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                UPDATE participants SET status = %s
                WHERE meeting_id = %s AND participant_id = %s
            """, (status, meeting_id, participant_id))

            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            logger.error(f"Error updating participant status: {e}")
            return False
        finally:
            cursor.close()

    async def save_participants_batch(self, meeting_id: str, participants: List[Dict]) -> bool:
        """Save multiple participants at once"""
        cursor = self._get_cursor()
        try:
            for participant in participants:
                participant_table_id = f"participant-{uuid.uuid4()}"

                cursor.execute("""
                    INSERT INTO participants
                    (id, meeting_id, participant_id, name, platform_id, status, join_time, is_host)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    platform_id = VALUES(platform_id),
                    status = VALUES(status),
                    is_host = VALUES(is_host)
                """, (
                    participant_table_id,
                    meeting_id,
                    participant.get("id", participant.get("participant_id")),
                    participant.get("name", "Unknown"),
                    participant.get("platform_id", participant.get("id")),
                    participant.get("status", "active"),
                    participant.get("join_time", datetime.utcnow().isoformat()),
                    participant.get("is_host", False)
                ))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving participants batch: {e}")
            return False
        finally:
            cursor.close()

    # Configuration management
    async def get_model_config(self) -> Optional[Dict]:
        """Get current model configuration"""
        cursor = self._get_cursor()
        try:
            cursor.execute("SELECT provider, model, whisperModel FROM settings ORDER BY updated_at DESC LIMIT 1")
            config = cursor.fetchone()

            if config:
                return {
                    "provider": config["provider"],
                    "model": config["model"],
                    "whisperModel": config["whisperModel"]
                }
            return None
        except Error as e:
            logger.error(f"Error getting model config: {e}")
            return None
        finally:
            cursor.close()

    async def save_model_config(self, provider: str, model: str, whisper_model: str) -> bool:
        """Save model configuration"""
        cursor = self._get_cursor()
        try:
            # Delete existing config
            cursor.execute("DELETE FROM settings")

            # Insert new config
            cursor.execute("""
                INSERT INTO settings (id, provider, model, whisperModel)
                VALUES (%s, %s, %s, %s)
            """, ("default_config", provider, model, whisper_model))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving model config: {e}")
            return False
        finally:
            cursor.close()

    async def save_api_key(self, api_key: str, provider: str) -> bool:
        """Save API key for a provider"""
        cursor = self._get_cursor()
        try:
            # Map provider to column
            key_column_map = {
                "groq": "groqApiKey",
                "openai": "openaiApiKey",
                "anthropic": "anthropicApiKey",
                "ollama": "ollamaApiKey"
            }

            key_column = key_column_map.get(provider.lower())
            if not key_column:
                logger.error(f"Unknown provider: {provider}")
                return False

            cursor.execute(f"""
                UPDATE settings SET {key_column} = %s WHERE id = 'default_config'
            """, (api_key,))

            if cursor.rowcount == 0:
                # Create settings record if it doesn't exist
                cursor.execute(f"""
                    INSERT INTO settings (id, provider, model, whisperModel, {key_column})
                    VALUES ('default_config', %s, %s, %s, %s)
                """, (provider, "gpt-3.5-turbo", "whisper-1", api_key))

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving API key: {e}")
            return False
        finally:
            cursor.close()

    async def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        cursor = self._get_cursor()
        try:
            key_column_map = {
                "groq": "groqApiKey",
                "openai": "openaiApiKey",
                "anthropic": "anthropicApiKey",
                "ollama": "ollamaApiKey"
            }

            key_column = key_column_map.get(provider.lower())
            if not key_column:
                return None

            cursor.execute(f"SELECT {key_column} FROM settings WHERE id = 'default_config'")
            result = cursor.fetchone()

            return result[key_column] if result and result[key_column] else None
        except Error as e:
            logger.error(f"Error getting API key: {e}")
            return None
        finally:
            cursor.close()

    async def delete_api_key(self, provider: str) -> bool:
        """Delete API key for a provider"""
        cursor = self._get_cursor()
        try:
            key_column_map = {
                "groq": "groqApiKey",
                "openai": "openaiApiKey",
                "anthropic": "anthropicApiKey",
                "ollama": "ollamaApiKey"
            }

            key_column = key_column_map.get(provider.lower())
            if not key_column:
                return False

            cursor.execute(f"UPDATE settings SET {key_column} = NULL WHERE id = 'default_config'")
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error deleting API key: {e}")
            return False
        finally:
            cursor.close()

    # Utility methods
    def clear_all(self) -> bool:
        """Clear all data (for testing)"""
        cursor = self._get_cursor()
        try:
            # Clear in reverse order due to foreign keys
            cursor.execute("DELETE FROM participants")
            cursor.execute("DELETE FROM transcript_chunks")
            cursor.execute("DELETE FROM summary_processes")
            cursor.execute("DELETE FROM transcripts")
            cursor.execute("DELETE FROM meetings")
            cursor.execute("DELETE FROM settings")

            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error clearing all data: {e}")
            return False
        finally:
            cursor.close()

    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            if not self.connection or not self.connection.is_connected():
                self._initialize_connection()

            cursor = self._get_cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"TiDB health check failed: {e}")
            return False

    def __del__(self):
        """Clean up database connection"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info("TiDB connection closed")
        except:
            pass  # Ignore cleanup errors