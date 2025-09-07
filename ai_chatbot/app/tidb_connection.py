import os
import logging
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class TiDBConnection:
    """TiDB Connection Manager for ChatBot"""

    def __init__(self):
        self.connection_string = (
            "mysql+pymysql://WJcVZ6rUiG4pBPB.root:{password}"
            "@gateway01.eu-central-1.prod.aws.tidbcloud.com:4000/chatbot"
        )
        self.engine = None

    def initialize(self, password: str) -> bool:
        """Initialize TiDB connection with password"""
        try:
            conn_str = self.connection_string.format(password=password)
            self.engine = create_engine(
                conn_str,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,
                connect_args={
                    "ssl": {
                        "ca": "/etc/ssl/cert.pem"
                    },
                    "charset": "utf8mb4"
                }
            )
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                self._ensure_schema_exists(conn)

            logger.info("Successfully connected to TiDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to TiDB: {e}")
            return False

    def _ensure_schema_exists(self, conn):
        """Ensure required tables exist"""
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vector_store (
                id INT PRIMARY KEY AUTO_INCREMENT,
                text TEXT NOT NULL,
                embedding VECTOR(384) NOT NULL COMMENT 'MiniLM embedding dimension',
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """))

            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT PRIMARY KEY AUTO_INCREMENT,
                session_id VARCHAR(255) NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session (session_id)
            )
            """))

            conn.commit()
            logger.info("Database schema ensured")
        except Exception as e:
            logger.error(f"Error ensuring schema: {e}")
            raise

    def get_engine(self):
        if not self.engine:
            raise ValueError("TiDB connection not initialized")
        return self.engine
