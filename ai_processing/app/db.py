"""
Unified Database Manager - Uses TiDB by default
"""

import os
import logging
from .database_interface import DatabaseInterface

logger = logging.getLogger(__name__)

def get_database() -> DatabaseInterface:
    """Get database instance - TiDB by default, SQLite fallback"""
    
    # Try TiDB first
    connection_string = os.getenv('TIDB_CONNECTION_STRING')
    if connection_string:
        try:
            # Parse connection string
            import re
            match = re.match(r'mysql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)', connection_string)
            if match:
                user, password, host, port, database = match.groups()
                
                from .tidb_database import TiDBDatabase
                db = TiDBDatabase(
                    host=host,
                    port=int(port),
                    user=user,
                    password=password,
                    database=database
                )
                logger.info(f"Using TiDB database: {database}")
                return db
        except Exception as e:
            logger.error(f"TiDB connection failed: {e}")
    
    # Fallback to SQLite
    from .sqlite_database import SQLiteDatabase
    db_path = os.getenv('DATABASE_PATH', 'meetings.db')
    db = SQLiteDatabase(db_path)
    logger.info(f"Using SQLite database: {db_path}")
    return db