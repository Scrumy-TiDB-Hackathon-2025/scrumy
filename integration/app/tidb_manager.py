"""
TiDB Manager for ScrumBot
Handles database connections and operations with TiDB Serverless
"""

import os
import logging
import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def load_shared_env():
    """Load shared environment variables from /shared/.tidb.env"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    shared_env_path = os.path.join(project_root, 'shared', '.tidb.env')
    
    if os.path.exists(shared_env_path):
        with open(shared_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
        logger.info(f"Loaded shared environment from {shared_env_path}")
    else:
        logger.warning(f"Shared environment file not found: {shared_env_path}")

class TiDBManager:
    def __init__(self):
        # Load shared environment first
        load_shared_env()
        
        self.connection = None
        self.connection_string = os.getenv('TIDB_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError("TIDB_CONNECTION_STRING environment variable is required")
        
        # Parse connection string
        self.connection_params = self._parse_connection_string(self.connection_string)
        
    def _parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse TiDB connection string into connection parameters"""
        try:
            # Handle mysql:// format
            if connection_string.startswith('mysql://'):
                parsed = urlparse(connection_string)
                return {
                    'host': parsed.hostname,
                    'port': parsed.port or 4000,
                    'user': parsed.username,
                    'password': parsed.password,
                    'database': parsed.path.lstrip('/') or 'test',
                    'ssl_disabled': False,
                    'autocommit': True
                }
            else:
                raise ValueError("Unsupported connection string format")
        except Exception as e:
            logger.error(f"Failed to parse connection string: {e}")
            raise
    
    async def connect(self) -> bool:
        """Establish connection to TiDB"""
        try:
            self.connection = mysql.connector.connect(**self.connection_params)
            if self.connection.is_connected():
                logger.info("Successfully connected to TiDB")
                await self._initialize_tables()
                return True
        except Error as e:
            logger.error(f"Error connecting to TiDB: {e}")
            return False
    
    async def disconnect(self):
        """Close TiDB connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("TiDB connection closed")
    
    async def _initialize_tables(self):
        """Create tables if they don't exist"""
        tables = {
            'meetings': '''
                CREATE TABLE IF NOT EXISTS meetings (
                    id VARCHAR(255) PRIMARY KEY,
                    platform VARCHAR(50) NOT NULL,
                    title VARCHAR(500),
                    participants TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''',
            'transcripts': '''
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    meeting_id VARCHAR(255) NOT NULL,
                    speaker VARCHAR(255),
                    text TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence FLOAT DEFAULT 1.0,
                    segment_start FLOAT,
                    segment_end FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                    INDEX idx_meeting_timestamp (meeting_id, timestamp)
                )
            ''',
            'ai_summaries': '''
                CREATE TABLE IF NOT EXISTS ai_summaries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    meeting_id VARCHAR(255) NOT NULL,
                    summary_type VARCHAR(50) NOT NULL,
                    content JSON NOT NULL,
                    model_used VARCHAR(100),
                    processing_time FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                    INDEX idx_meeting_type (meeting_id, summary_type)
                )
            ''',
            'tasks': '''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    meeting_id VARCHAR(255) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    description TEXT,
                    assignee VARCHAR(255),
                    priority VARCHAR(20) DEFAULT 'medium',
                    status VARCHAR(50) DEFAULT 'not_started',
                    due_date DATE,
                    notion_page_id VARCHAR(255),
                    slack_message_ts VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                    INDEX idx_meeting_status (meeting_id, status),
                    INDEX idx_assignee_status (assignee, status)
                )
            '''
        }
        
        cursor = self.connection.cursor()
        try:
            for table_name, create_sql in tables.items():
                cursor.execute(create_sql)
                logger.info(f"Table {table_name} ready")
            self.connection.commit()
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
        finally:
            cursor.close()
    
    async def save_meeting(self, meeting_data: Dict[str, Any]) -> bool:
        """Save meeting information"""
        try:
            cursor = self.connection.cursor()
            query = '''
                INSERT INTO meetings (id, platform, title, participants, metadata)
                VALUES (%(id)s, %(platform)s, %(title)s, %(participants)s, %(metadata)s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                participants = VALUES(participants),
                metadata = VALUES(metadata),
                updated_at = CURRENT_TIMESTAMP
            '''
            
            # Convert participants list to JSON string if needed
            participants = meeting_data.get('participants', [])
            if isinstance(participants, list):
                participants = json.dumps(participants)
            
            # Convert metadata to JSON string if needed
            metadata = meeting_data.get('metadata', {})
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata)
            
            data = {
                'id': meeting_data['id'],
                'platform': meeting_data.get('platform', 'unknown'),
                'title': meeting_data.get('title', ''),
                'participants': participants,
                'metadata': metadata
            }
            
            cursor.execute(query, data)
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error saving meeting: {e}")
            return False
    
    async def save_transcript(self, transcript_data: Dict[str, Any]) -> bool:
        """Save transcript segment"""
        try:
            cursor = self.connection.cursor()
            query = '''
                INSERT INTO transcripts (meeting_id, speaker, text, confidence, segment_start, segment_end)
                VALUES (%(meeting_id)s, %(speaker)s, %(text)s, %(confidence)s, %(segment_start)s, %(segment_end)s)
            '''
            
            data = {
                'meeting_id': transcript_data['meeting_id'],
                'speaker': transcript_data.get('speaker', 'Unknown'),
                'text': transcript_data['text'],
                'confidence': transcript_data.get('confidence', 1.0),
                'segment_start': transcript_data.get('segment_start'),
                'segment_end': transcript_data.get('segment_end')
            }
            
            cursor.execute(query, data)
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error saving transcript: {e}")
            return False
    
    async def save_ai_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Save AI-generated summary"""
        try:
            cursor = self.connection.cursor()
            query = '''
                INSERT INTO ai_summaries (meeting_id, summary_type, content, model_used, processing_time)
                VALUES (%(meeting_id)s, %(summary_type)s, %(content)s, %(model_used)s, %(processing_time)s)
            '''
            
            # Convert content to JSON string if needed
            content = summary_data['content']
            if isinstance(content, dict):
                content = json.dumps(content)
            
            data = {
                'meeting_id': summary_data['meeting_id'],
                'summary_type': summary_data.get('summary_type', 'general'),
                'content': content,
                'model_used': summary_data.get('model_used', 'unknown'),
                'processing_time': summary_data.get('processing_time', 0.0)
            }
            
            cursor.execute(query, data)
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error saving AI summary: {e}")
            return False
    
    async def save_task(self, meeting_id: str, title: str, description: str = "", 
                       assignee: str = "", priority: str = "medium", status: str = "not_started",
                       due_date: str = None, notion_page_id: str = None, 
                       slack_message_ts: str = None, task_id: str = None) -> Optional[int]:
        """Save task and return task ID"""
        try:
            cursor = self.connection.cursor()
            query = '''
                INSERT INTO tasks (meeting_id, title, description, assignee, priority, status, due_date, notion_page_id, slack_message_ts)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            
            cursor.execute(query, (
                meeting_id, title, description, assignee, priority, 
                status, due_date, notion_page_id, slack_message_ts
            ))
            self.connection.commit()
            task_id = cursor.lastrowid
            cursor.close()
            logger.info(f"Saved task '{title}' with ID {task_id} for meeting {meeting_id}")
            return task_id
            
        except Error as e:
            logger.error(f"Error saving task: {e}")
            return None
    
    async def get_meeting_transcripts(self, meeting_id: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a meeting"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = '''
                SELECT * FROM transcripts 
                WHERE meeting_id = %s 
                ORDER BY timestamp ASC
            '''
            cursor.execute(query, (meeting_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except Error as e:
            logger.error(f"Error getting transcripts: {e}")
            return []
    
    async def get_meeting_tasks(self, meeting_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a meeting"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = '''
                SELECT * FROM tasks 
                WHERE meeting_id = %s 
                ORDER BY created_at ASC
            '''
            cursor.execute(query, (meeting_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except Error as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    async def update_task_notion_id(self, task_id: int, notion_page_id: str) -> bool:
        """Update task with Notion page ID"""
        try:
            cursor = self.connection.cursor()
            query = '''
                UPDATE tasks 
                SET notion_page_id = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            '''
            cursor.execute(query, (notion_page_id, task_id))
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error updating task Notion ID: {e}")
            return False
    
    async def update_task_slack_ts(self, task_id: int, slack_message_ts: str) -> bool:
        """Update task with Slack message timestamp"""
        try:
            cursor = self.connection.cursor()
            query = '''
                UPDATE tasks 
                SET slack_message_ts = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            '''
            cursor.execute(query, (slack_message_ts, task_id))
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error updating task Slack timestamp: {e}")
            return False

# Global instance
tidb_manager = TiDBManager()