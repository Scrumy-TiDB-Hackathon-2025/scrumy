import aiomysql
import json
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, host='localhost', port=4000, user='root', password='', db='meeting_minutes'):
        self.db_config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db,
            'charset': 'utf8mb4'
        }

    async def _init_db(self):
        """Initialize the database with required tables"""
        pool = await aiomysql.create_pool(**self.db_config)
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Create meetings table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS meetings (
                            id VARCHAR(255) PRIMARY KEY,
                            title TEXT NOT NULL,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL
                        )
                    """)
                    
                    # Create transcripts table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS transcripts (
                            id VARCHAR(255) PRIMARY KEY,
                            meeting_id VARCHAR(255) NOT NULL,
                            transcript TEXT NOT NULL,
                            timestamp DATETIME NOT NULL,
                            summary TEXT,
                            action_items TEXT,
                            key_points TEXT,
                            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
                        )
                    """)
                    
                    # Create summary_processes table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS summary_processes (
                            meeting_id VARCHAR(255) PRIMARY KEY,
                            status VARCHAR(50) NOT NULL,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            error TEXT,
                            result TEXT,
                            start_time DATETIME,
                            end_time DATETIME,
                            chunk_count INT DEFAULT 0,
                            processing_time FLOAT DEFAULT 0.0,
                            metadata TEXT,
                            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
                        )
                    """)

                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS transcript_chunks (
                            meeting_id VARCHAR(255) PRIMARY KEY,
                            meeting_name TEXT,
                            transcript_text TEXT NOT NULL,
                            model VARCHAR(50) NOT NULL,
                            model_name VARCHAR(50) NOT NULL,
                            chunk_size INT,
                            overlap INT,
                            created_at DATETIME NOT NULL,
                            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
                        )
                    """)

                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS settings (
                            id VARCHAR(255) PRIMARY KEY,
                            provider VARCHAR(50) NOT NULL,
                            model VARCHAR(50) NOT NULL,
                            whisperModel VARCHAR(50) NOT NULL,
                            groqApiKey TEXT,
                            openaiApiKey TEXT,
                            anthropicApiKey TEXT,
                            ollamaApiKey TEXT
                        )
                    """)

                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS participants (
                            id VARCHAR(255) PRIMARY KEY,
                            meeting_id VARCHAR(255) NOT NULL,
                            participant_id VARCHAR(255) NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            platform_id VARCHAR(255) NOT NULL,
                            status VARCHAR(50) NOT NULL,
                            join_time DATETIME NOT NULL,
                            is_host BOOLEAN NOT NULL DEFAULT 0,
                            created_at DATETIME NOT NULL,
                            FOREIGN KEY (meeting_id) REFERENCES meetings(id),
                            UNIQUE(meeting_id, participant_id)
                        )
                    """)

                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def _get_pool(self):
        """Get a database connection pool"""
        return await aiomysql.create_pool(**self.db_config)

    async def create_process(self, meeting_id: str) -> str:
        """Create a new process entry or update existing one and return its ID"""
        now = datetime.utcnow()
        
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # First try to update existing process
                    await cursor.execute(
                        """
                        UPDATE summary_processes 
                        SET status = %s, updated_at = %s, start_time = %s, error = NULL, result = NULL
                        WHERE meeting_id = %s
                        """,
                        ("PENDING", now, now, meeting_id)
                    )
                    
                    # If no rows were updated, insert a new one
                    if cursor.rowcount == 0:
                        await cursor.execute(
                            "INSERT INTO summary_processes (meeting_id, status, created_at, updated_at, start_time) VALUES (%s, %s, %s, %s, %s)",
                            (meeting_id, "PENDING", now, now, now)
                        )
                    
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()
        
        return meeting_id

    async def update_process(self, meeting_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None, 
                           chunk_count: Optional[int] = None, processing_time: Optional[float] = None, 
                           metadata: Optional[Dict] = None):
        """Update a process status and result"""
        now = datetime.utcnow()
        
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    update_fields = ["status = %s", "updated_at = %s"]
                    params = [status, now]
                    
                    if result:
                        update_fields.append("result = %s")
                        params.append(json.dumps(result))
                    if error:
                        update_fields.append("error = %s")
                        params.append(error)
                    if chunk_count is not None:
                        update_fields.append("chunk_count = %s")
                        params.append(chunk_count)
                    if processing_time is not None:
                        update_fields.append("processing_time = %s")
                        params.append(processing_time)
                    if metadata:
                        update_fields.append("metadata = %s")
                        params.append(json.dumps(metadata))
                    if status == 'COMPLETED' or status == 'FAILED':
                        update_fields.append("end_time = %s")
                        params.append(now)
                        
                    params.append(meeting_id)
                    query = f"UPDATE summary_processes SET {', '.join(update_fields)} WHERE meeting_id = %s"
                    await cursor.execute(query, params)
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def save_transcript(self, meeting_id: str, transcript_text: str, model: str, model_name: str, 
                            chunk_size: int, overlap: int):
        """Save transcript data"""
        now = datetime.utcnow()
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # First try to update existing transcript
                    await cursor.execute("""
                        UPDATE transcript_chunks 
                        SET transcript_text = %s, model = %s, model_name = %s, chunk_size = %s, overlap = %s, created_at = %s
                        WHERE meeting_id = %s
                    """, (transcript_text, model, model_name, chunk_size, overlap, now, meeting_id))
                    
                    # If no rows were updated, insert a new one
                    if cursor.rowcount == 0:
                        await cursor.execute("""
                            INSERT INTO transcript_chunks (meeting_id, transcript_text, model, model_name, chunk_size, overlap, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (meeting_id, transcript_text, model, model_name, chunk_size, overlap, now))
                    
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def update_meeting_name(self, meeting_id: str, meeting_name: str):
        """Update meeting name in both meetings and transcript_chunks tables"""
        now = datetime.utcnow()
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Update meetings table
                    await cursor.execute("""
                        UPDATE meetings
                        SET title = %s, updated_at = %s
                        WHERE id = %s
                    """, (meeting_name, now, meeting_id))
                    
                    # Update transcript_chunks table
                    await cursor.execute("""
                        UPDATE transcript_chunks
                        SET meeting_name = %s
                        WHERE meeting_id = %s
                    """, (meeting_name, meeting_id))
                    
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def get_transcript_data(self, meeting_id: str):
        """Get transcript data for a meeting"""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT t.*, p.status, p.result 
                        FROM transcript_chunks t 
                        JOIN summary_processes p ON t.meeting_id = p.meeting_id 
                        WHERE t.meeting_id = %s
                    """, (meeting_id,))
                    row = await cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, row))
                    return None
        finally:
            pool.close()
            await pool.wait_closed()

    async def save_meeting(self, meeting_id: str, title: str):
        """Save or update a meeting"""
        try:
            pool = await self._get_pool()
            try:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        # Only check if meeting ID exists (not title, as titles can be duplicated)
                        await cursor.execute("SELECT id FROM meetings WHERE id = %s", (meeting_id,))
                        existing_meeting = await cursor.fetchone()
                        
                        if not existing_meeting:
                            # Create new meeting
                            await cursor.execute("""
                                INSERT INTO meetings (id, title, created_at, updated_at)
                                VALUES (%s, %s, NOW(), NOW())
                            """, (meeting_id, title))
                        else:
                            # If we get here and meeting exists, throw error since we don't want duplicates
                            raise Exception(f"Meeting with ID {meeting_id} already exists")
                        await conn.commit()
                        return True
            finally:
                pool.close()
                await pool.wait_closed()
        except Exception as e:
            logger.error(f"Error saving meeting: {str(e)}")
            raise

    async def save_meeting_transcript(self, meeting_id: str, transcript: str, timestamp: str, summary: str = "", action_items: str = "", key_points: str = ""):
        """Save a transcript for a meeting"""
        try:
            pool = await self._get_pool()
            try:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        # Generate a unique ID for the transcript
                        transcript_id = f"{meeting_id}_{timestamp}"
                        # Save transcript
                        await cursor.execute("""
                            INSERT INTO transcripts (
                                id, meeting_id, transcript, timestamp, summary, action_items, key_points
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (transcript_id, meeting_id, transcript, timestamp, summary, action_items, key_points))
                        
                        await conn.commit()
                        return True
            finally:
                pool.close()
                await pool.wait_closed()
        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
            raise

    async def get_meeting(self, meeting_id: str):
        """Get a meeting by ID with all its transcripts"""
        try:
            pool = await self._get_pool()
            try:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        # Get meeting details
                        await cursor.execute("""
                            SELECT id, title, created_at, updated_at
                            FROM meetings
                            WHERE id = %s
                        """, (meeting_id,))
                        meeting = await cursor.fetchone()
                        
                        if not meeting:
                            return None
                        
                        # Get all transcripts for this meeting
                        await cursor.execute("""
                            SELECT transcript, timestamp
                            FROM transcripts
                            WHERE meeting_id = %s
                        """, (meeting_id,))
                        transcripts = await cursor.fetchall()
                        
                        return {
                            'id': meeting[0],
                            'title': meeting[1],
                            'created_at': meeting[2],
                            'updated_at': meeting[3],
                            'transcripts': [{
                                'id': meeting_id,
                                'text': transcript[0],
                                'timestamp': transcript[1]
                            } for transcript in transcripts]
                        }
            finally:
                pool.close()
                await pool.wait_closed()
        except Exception as e:
            logger.error(f"Error getting meeting: {str(e)}")
            raise

    async def update_meeting_title(self, meeting_id: str, new_title: str):
        """Update a meeting's title"""
        now = datetime.utcnow()
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        UPDATE meetings
                        SET title = %s, updated_at = %s
                        WHERE id = %s
                    """, (new_title, now, meeting_id))
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def get_all_meetings(self):
        """Get all meetings with basic information"""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT id, title, created_at
                        FROM meetings
                        ORDER BY created_at DESC
                    """)
                    rows = await cursor.fetchall()
                    return [{
                        'id': row[0],
                        'title': row[1],
                        'created_at': row[2]
                    } for row in rows]
        finally:
            pool.close()
            await pool.wait_closed()

    async def delete_meeting(self, meeting_id: str):
        """Delete a meeting and all its associated data"""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    try:
                        # Delete from transcript_chunks
                        await cursor.execute("DELETE FROM transcript_chunks WHERE meeting_id = %s", (meeting_id,))
                        
                        # Delete from summary_processes
                        await cursor.execute("DELETE FROM summary_processes WHERE meeting_id = %s", (meeting_id,))
                        
                        # Delete from transcripts
                        await cursor.execute("DELETE FROM transcripts WHERE meeting_id = %s", (meeting_id,))
                        
                        # Delete from participants
                        await cursor.execute("DELETE FROM participants WHERE meeting_id = %s", (meeting_id,))
                        
                        # Delete from meetings
                        await cursor.execute("DELETE FROM meetings WHERE id = %s", (meeting_id,))
                        
                        await conn.commit()
                        return True
                    except Exception as e:
                        logger.error(f"Error deleting meeting {meeting_id}: {str(e)}")
                        return False
        finally:
            pool.close()
            await pool.wait_closed()

    async def get_model_config(self):
        """Get the current model configuration"""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT provider, model, whisperModel FROM settings WHERE id = '1'")
                    row = await cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, row))
                    return None
        finally:
            pool.close()
            await pool.wait_closed()

    async def save_model_config(self, provider: str, model: str, whisperModel: str):
        """Save the model configuration"""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Check if the configuration already exists
                    await cursor.execute("SELECT id FROM settings WHERE id = '1'")
                    existing_config = await cursor.fetchone()
                    if existing_config:
                        # Update existing configuration
                        await cursor.execute("""
                            UPDATE settings 
                            SET provider = %s, model = %s, whisperModel = %s
                            WHERE id = '1'    
                        """, (provider, model, whisperModel))
                    else:
                        # Insert new configuration
                        await cursor.execute("""
                            INSERT INTO settings (id, provider, model, whisperModel)
                            VALUES (%s, %s, %s, %s)
                        """, ('1', provider, model, whisperModel))
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def save_api_key(self, api_key: str, provider: str):
        """Save the API key"""
        provider_list = ["openai", "claude", "groq", "ollama"]
        if provider not in provider_list:
            raise ValueError(f"Invalid provider: {provider}")
        if provider == "openai":
            api_key_name = "openaiApiKey"
        elif provider == "claude":
            api_key_name = "anthropicApiKey"
        elif provider == "groq":
            api_key_name = "groqApiKey"
        elif provider == "ollama":
            api_key_name = "ollamaApiKey"
        
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(f"UPDATE settings SET {api_key_name} = %s WHERE id = '1'", (api_key,))
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def get_api_key(self, provider: str):
        """Get the API key"""
        provider_map = {
            "openai": "openaiApiKey",
            "claude": "anthropicApiKey",
            "anthropic": "anthropicApiKey",
            "groq": "groqApiKey",
            "ollama": "ollamaApiKey"
        }
        provider_key = str(provider).lower()
        api_key_name = provider_map.get(provider_key)
        if not api_key_name:
            # fallback: try to match partials (e.g., "string" -> "openaiApiKey" if "openai" in provider)
            for k, v in provider_map.items():
                if k in provider_key:
                    api_key_name = v
                    break
        if not api_key_name:
            raise ValueError(f"Invalid provider: {provider}")
        
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(f"SELECT {api_key_name} FROM settings WHERE id = '1'")
                    row = await cursor.fetchone()
                    return row[0] if row else None
        finally:
            pool.close()
            await pool.wait_closed()
        
    async def delete_api_key(self, provider: str):
        """Delete the API key"""
        provider_list = ["openai", "claude", "groq", "ollama"]
        if provider not in provider_list:
            raise ValueError(f"Invalid provider: {provider}")
        if provider == "openai":
            api_key_name = "openaiApiKey"
        elif provider == "claude":
            api_key_name = "anthropicApiKey"
        elif provider == "groq":
            api_key_name = "groqApiKey"
        elif provider == "ollama":
            api_key_name = "ollamaApiKey"
        
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(f"UPDATE settings SET {api_key_name} = NULL WHERE id = '1'", ())
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()

    async def clear_all(self):
        """Delete all rows from all tables (for tests)"""
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("DELETE FROM transcript_chunks")
                    await cursor.execute("DELETE FROM summary_processes")
                    await cursor.execute("DELETE FROM transcripts")
                    await cursor.execute("DELETE FROM participants")
                    await cursor.execute("DELETE FROM meetings")
                    await cursor.execute("DELETE FROM settings")
                    await conn.commit()
        finally:
            pool.close()
            await pool.wait_closed()