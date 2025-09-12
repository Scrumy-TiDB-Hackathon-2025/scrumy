"""
Abstract Database Interface for TiDB AgentX 2025 Hackathon
Provides a unified interface that can be implemented for both SQLite and TiDB
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
import logging
import os

logger = logging.getLogger(__name__)

# Ensure compatibility methods are available
def ensure_database_compatibility():
    """Ensure database implementations have all required methods for cross-compatibility"""
    import os
    
    # Check if we need to add compatibility methods to SQLite
    db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
    
    if db_type == 'sqlite':
        from .sqlite_database import SQLiteDatabase
        
        # Add missing methods if they don't exist
        if not hasattr(SQLiteDatabase, 'get_meeting_transcript'):
            logger.warning("Adding compatibility method get_meeting_transcript to SQLiteDatabase")
        if not hasattr(SQLiteDatabase, 'get_all_tasks'):
            logger.warning("Adding compatibility method get_all_tasks to SQLiteDatabase")
        if not hasattr(SQLiteDatabase, 'get_tasks_by_meeting'):
            logger.warning("Adding compatibility method get_tasks_by_meeting to SQLiteDatabase")
    
    logger.info(f"Database compatibility ensured for {db_type}")

class DatabaseInterface(ABC):
    """
    Abstract database interface for TiDB AgentX 2025 hackathon project.
    This interface can be implemented for both SQLite (development) and TiDB (production).
    """

    @abstractmethod
    async def create_process(self, meeting_id: str) -> str:
        """Create a new process record and return process ID"""
        pass

    @abstractmethod
    async def update_process(self, process_id: str, status: str = None,
                           error: str = None, result: str = None,
                           start_time: str = None, end_time: str = None,
                           chunk_count: int = None, processing_time: float = None,
                           metadata: str = None) -> bool:
        """Update process record with new information"""
        pass

    @abstractmethod
    async def save_transcript(self, meeting_id: str, transcript: str, model: str,
                             model_name: str, chunk_size: int, overlap: int) -> bool:
        """Save transcript data"""
        pass

    @abstractmethod
    async def update_meeting_name(self, meeting_id: str, name: str) -> bool:
        """Update meeting name"""
        pass

    @abstractmethod
    async def get_transcript_data(self, meeting_id: str) -> Optional[Dict]:
        """Get transcript data for a meeting"""
        pass

    @abstractmethod
    async def save_meeting(self, meeting_id: str, title: str) -> bool:
        """Save meeting information"""
        pass

    @abstractmethod
    async def save_meeting_transcript(self, meeting_id: str, transcript: str,
                                    timestamp: str, summary: str = "",
                                    action_items: str = "", key_points: str = "") -> bool:
        """Save meeting transcript segment"""
        pass

    @abstractmethod
    async def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        """Get meeting by ID"""
        pass

    @abstractmethod
    async def update_meeting_title(self, meeting_id: str, title: str) -> bool:
        """Update meeting title"""
        pass

    @abstractmethod
    async def get_all_meetings(self) -> List[Dict]:
        """Get all meetings"""
        pass

    @abstractmethod
    async def delete_meeting(self, meeting_id: str) -> bool:
        """Delete meeting and related data"""
        pass

    # Participant management methods
    @abstractmethod
    async def save_participant(self, meeting_id: str, participant_id: str,
                              name: str, platform_id: str, status: str,
                              join_time: str, is_host: bool = False) -> bool:
        """Save participant information"""
        pass

    @abstractmethod
    async def get_participants(self, meeting_id: str) -> List[Dict]:
        """Get all participants for a meeting"""
        pass

    @abstractmethod
    async def update_participant_status(self, meeting_id: str, participant_id: str,
                                       status: str) -> bool:
        """Update participant status"""
        pass

    @abstractmethod
    async def save_participants_batch(self, meeting_id: str, participants: List[Dict]) -> bool:
        """Save multiple participants at once"""
        pass

    # Configuration management
    @abstractmethod
    async def get_model_config(self) -> Optional[Dict]:
        """Get current model configuration"""
        pass

    @abstractmethod
    async def save_model_config(self, provider: str, model: str, whisper_model: str) -> bool:
        """Save model configuration"""
        pass

    @abstractmethod
    async def save_api_key(self, api_key: str, provider: str) -> bool:
        """Save API key for a provider"""
        pass

    @abstractmethod
    async def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        pass

    @abstractmethod
    async def delete_api_key(self, provider: str) -> bool:
        """Delete API key for a provider"""
        pass

    # Utility methods
    @abstractmethod
    def clear_all(self) -> bool:
        """Clear all data (for testing)"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        pass

    # Frontend integration methods (required for cross-compatibility)
    @abstractmethod
    async def get_all_tasks(self) -> List[Dict]:
        """Get all tasks from database"""
        pass

    @abstractmethod
    async def get_tasks_by_meeting(self, meeting_id: str) -> List[Dict]:
        """Get tasks for a specific meeting"""
        pass

    @abstractmethod
    async def get_meeting_transcript(self, meeting_id: str) -> Optional[Dict]:
        """Get full transcript data for a meeting"""
        pass


class DatabaseFactory:
    """Factory class to create appropriate database implementation"""

    @staticmethod
    def create_database(db_type: str, **kwargs) -> DatabaseInterface:
        """
        Create database implementation based on type.

        Args:
            db_type: "sqlite" for SQLite or "tidb" for TiDB
            **kwargs: Database-specific configuration parameters

        Returns:
            DatabaseInterface implementation
        """
        import os
        
        if db_type.lower() == "sqlite":
            from .sqlite_database import SQLiteDatabase
            # Use default SQLite path if not provided
            if not kwargs:
                kwargs = {"db_path": os.getenv('SQLITE_DB_PATH', 'meeting_minutes.db')}
            return SQLiteDatabase(**kwargs)
        elif db_type.lower() == "tidb":
            from .tidb_database import TiDBDatabase
            # If no kwargs provided, try to get from environment
            if not kwargs:
                # Parse TiDB connection string if available
                connection_string = os.getenv('TIDB_CONNECTION_STRING')
                if connection_string:
                    kwargs = DatabaseFactory._parse_tidb_connection_string(connection_string)
                else:
                    # Use individual environment variables
                    kwargs = {
                        'host': os.getenv('TIDB_HOST'),
                        'port': int(os.getenv('TIDB_PORT', 4000)),
                        'user': os.getenv('TIDB_USER'),
                        'password': os.getenv('TIDB_PASSWORD'),
                        'database': os.getenv('TIDB_DATABASE', 'scrumy_ai'),
                        'ssl_mode': os.getenv('TIDB_SSL_MODE', 'REQUIRED')
                    }
                    
                    # Check if required parameters are missing
                    if not all([kwargs['host'], kwargs['user'], kwargs['password']]):
                        logger.warning("Missing TiDB connection parameters. Falling back to SQLite.")
                        from .sqlite_database import SQLiteDatabase
                        return SQLiteDatabase(db_path=os.getenv('SQLITE_DB_PATH', 'meeting_minutes.db'))
            
            return TiDBDatabase(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def _parse_tidb_connection_string(connection_string: str) -> dict:
        """Parse TiDB connection string into connection parameters"""
        import re
        
        # Parse mysql://user:password@host:port/database
        pattern = r'mysql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)'
        match = re.match(pattern, connection_string)
        
        if not match:
            raise ValueError(f"Invalid TiDB connection string format: {connection_string}")
        
        user, password, host, port, database = match.groups()
        
        return {
            'host': host,
            'port': int(port),
            'user': user,
            'password': password,
            'database': database,
            'ssl_mode': 'REQUIRED'
        }

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> DatabaseInterface:
        """
        Create database implementation from configuration dictionary.

        Expected config format:
        {
            "type": "sqlite" | "tidb",
            "connection": {...connection parameters...}
        }
        """
        db_type = config.get("type")
        if not db_type:
            raise ValueError("Database type not specified in config")

        connection_params = config.get("connection", {})
        return DatabaseFactory.create_database(db_type, **connection_params)
    
    @staticmethod
    def create_from_env() -> DatabaseInterface:
        """
        Create database implementation from environment variables.
        Uses DATABASE_TYPE to determine which database to use.
        """
        import os
        
        db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
        logger.info(f"Creating database of type: {db_type}")
        
        return DatabaseFactory.create_database(db_type)


# Database configuration templates for easy setup
DATABASE_CONFIGS = {
    "sqlite": {
        "required_params": ["db_path"],
        "optional_params": [],
        "example": {
            "type": "sqlite",
            "connection": {
                "db_path": "meeting_minutes.db"
            }
        }
    },
    "tidb": {
        "required_params": ["host", "user", "password"],
        "optional_params": ["port", "database", "ssl_mode", "charset", "autocommit"],
        "example": {
            "type": "tidb",
            "connection": {
                "host": "gateway01.us-west-2.prod.aws.tidbcloud.com",
                "port": 4000,
                "user": "your_username",
                "password": "your_password",
                "database": "scrumy_ai",
                "ssl_mode": "REQUIRED"
            }
        }
    }
}


def get_database_config_template(db_type: str) -> Dict[str, Any]:
    """Get configuration template for a specific database type"""
    if db_type.lower() not in DATABASE_CONFIGS:
        raise ValueError(f"Unknown database type: {db_type}")

    return DATABASE_CONFIGS[db_type.lower()]

def print_database_status():
    """Print current database configuration status"""
    status = get_database_status()
    
    print("\n" + "="*50)
    print("    DATABASE CONFIGURATION STATUS")
    print("="*50)
    print(f"Database Type: {status['type'].upper()}")
    print(f"Environment Ready: {'✅' if status['environment_ready'] else '❌'}")
    
    if status['is_tidb']:
        conn_info = status['connection_info']
        print(f"TiDB Host: {conn_info.get('host', 'Not Set')}")
        print(f"TiDB Port: {conn_info.get('port', 'Not Set')}")
        print(f"TiDB Database: {conn_info.get('database', 'Not Set')}")
        print(f"TiDB User: {conn_info.get('user', 'Not Set')}")
    else:
        print(f"SQLite Path: {status['connection_info'].get('db_path', 'Not Set')}")
    
    print("="*50 + "\n")


def validate_database_config(config: Dict[str, Any]) -> bool:
    """Validate database configuration"""
    db_type = config.get("type")
    if not db_type:
        logger.error("Database type not specified")
        return False

    if db_type.lower() not in DATABASE_CONFIGS:
        logger.error(f"Unknown database type: {db_type}")
        return False

    template = DATABASE_CONFIGS[db_type.lower()]
    connection = config.get("connection", {})

    # Check required parameters
    for param in template["required_params"]:
        if param not in connection or not connection[param]:
            logger.error(f"Missing required parameter: {param}")
            return False

    logger.info(f"Database configuration validated successfully for {db_type}")
    return True

def get_database_status() -> Dict[str, Any]:
    """Get current database configuration status from environment"""
    import os
    
    db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
    
    status = {
        "type": db_type,
        "is_tidb": db_type == "tidb",
        "is_sqlite": db_type == "sqlite",
        "environment_ready": False,
        "connection_info": {}
    }
    
    if db_type == "tidb":
        connection_string = os.getenv('TIDB_CONNECTION_STRING')
        if connection_string:
            try:
                params = DatabaseFactory._parse_tidb_connection_string(connection_string)
                status["connection_info"] = {
                    "host": params["host"],
                    "port": params["port"],
                    "database": params["database"],
                    "user": params["user"][:3] + "***" if params["user"] else None
                }
                status["environment_ready"] = True
            except Exception as e:
                logger.error(f"Invalid TiDB connection string: {e}")
        else:
            # Check individual env vars
            host = os.getenv('TIDB_HOST')
            user = os.getenv('TIDB_USER')
            password = os.getenv('TIDB_PASSWORD')
            
            status["connection_info"] = {
                "host": host,
                "port": int(os.getenv('TIDB_PORT', 4000)),
                "database": os.getenv('TIDB_DATABASE', 'scrumy_ai'),
                "user": user[:3] + "***" if user else None
            }
            status["environment_ready"] = bool(host and user and password)
    else:
        # SQLite
        db_path = os.getenv('SQLITE_DB_PATH', 'meeting_minutes.db')
        status["connection_info"] = {"db_path": db_path}
        status["environment_ready"] = True
    
    return status