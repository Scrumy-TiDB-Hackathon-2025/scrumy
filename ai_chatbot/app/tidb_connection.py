import os
import logging
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)
class TiDBConnection:
    """TiDB Connection Manager"""

    def __init__(self):
        # Read environment variables
        host = os.getenv("CHATBOT_TIDB_HOST")
        port = os.getenv("CHATBOT_TIDB_PORT", "4000")
        user = os.getenv("CHATBOT_TIDB_USER")
        password = os.getenv("CHATBOT_TIDB_PASSWORD")
        database = os.getenv("CHATBOT_TIDB_DATABASE")

        if not all([host, port, user, password, database]):
            raise ValueError("Missing required CHATBOT_TIDB_* environment variables")

        self.connection_string = (
            f"mysql+pymysql://{user}:{password}"
            f"@{host}:{port}/{database}"
        )

        self.engine = create_engine(
            self.connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
            connect_args={
                "ssl": {"ca": "/etc/ssl/cert.pem"},
                "charset": "utf8mb4"
            }
        )

    def initialize(self) -> bool:
        """Initialize TiDB connection and ensure schema exists"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                self._ensure_schema_exists(conn)
            logger.info("✅ Connected to TiDB (chatbot)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to TiDB (chatbot): {e}")
            return False

    def _ensure_schema_exists(self, conn):
        """Ensure required tables exist in chatbot DB"""
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
            logger.info("✅ Schema ensured for chatbot DB")
        except Exception as e:
            logger.error(f"❌ Error ensuring schema: {e}")
            raise

    def get_engine(self):
        if not self.engine:
            raise ValueError("TiDB connection not initialized")
        return self.engine