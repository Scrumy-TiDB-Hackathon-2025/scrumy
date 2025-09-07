"""
Database Configuration Helper for TiDB AgentX 2025 Hackathon
Provides easy configuration switching between SQLite (dev) and TiDB (production)
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management for hackathon project"""

    # Default configurations
    SQLITE_CONFIG = {
        "type": "sqlite",
        "connection": {
            "db_path": "meeting_minutes.db"
        }
    }

    TIDB_CONFIG_TEMPLATE = {
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

    @staticmethod
    def get_config_from_env() -> Dict[str, Any]:
        """Get database configuration from environment variables"""
        db_type = os.getenv('DATABASE_TYPE', 'tidb').lower()

        if db_type == 'tidb':
            return DatabaseConfig._get_tidb_config_from_env()
        else:
            return DatabaseConfig._get_sqlite_config_from_env()

    @staticmethod
    def _get_sqlite_config_from_env() -> Dict[str, Any]:
        """Get SQLite configuration from environment"""
        config = DatabaseConfig.SQLITE_CONFIG.copy()
        config["connection"]["db_path"] = os.getenv('SQLITE_DB_PATH', 'meeting_minutes.db')
        return config

    @staticmethod
    def _get_tidb_config_from_env() -> Dict[str, Any]:
        """Get TiDB configuration from environment variables"""
        config = {
            "type": "tidb",
            "connection": {
                "host": os.getenv('TIDB_HOST'),
                "port": int(os.getenv('TIDB_PORT', 4000)),
                "user": os.getenv('TIDB_USER'),
                "password": os.getenv('TIDB_PASSWORD'),
                "database": os.getenv('TIDB_DATABASE', 'scrumy_ai'),
                "ssl_mode": os.getenv('TIDB_SSL_MODE', 'REQUIRED')
            }
        }

        # Validate required TiDB parameters
        required_params = ['host', 'user', 'password']
        missing_params = [param for param in required_params if not config["connection"][param]]

        if missing_params:
            logger.warning(f"Missing TiDB parameters: {missing_params}. Falling back to SQLite.")
            return DatabaseConfig._get_sqlite_config_from_env()

        return config

    @staticmethod
    def get_tidb_connection_string() -> Optional[str]:
        """Get TiDB connection string for integration with existing TiDB manager"""
        config = DatabaseConfig._get_tidb_config_from_env()

        if config["type"] != "tidb":
            return None

        conn = config["connection"]
        return f"mysql://{conn['user']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['database']}"

    @staticmethod
    def create_env_file_template(file_path: str = ".env.tidb"):
        """Create a template .env file for TiDB configuration"""
        template = """# TiDB AgentX 2025 Hackathon Configuration
# Copy this to .env and fill in your TiDB credentials

# Database Type: 'sqlite' for development, 'tidb' for production
DATABASE_TYPE=tidb

# TiDB Connection Parameters
TIDB_HOST=gateway01.us-west-2.prod.aws.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=your_username_here
TIDB_PASSWORD=your_password_here
TIDB_DATABASE=scrumy_ai
TIDB_SSL_MODE=REQUIRED

# Alternative: SQLite Configuration (for development)
# DATABASE_TYPE=sqlite
# SQLITE_DB_PATH=meeting_minutes.db

# AI Model Configuration
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Whisper Server Configuration
WHISPER_SERVER_URL=http://localhost:8000
"""

        try:
            with open(file_path, 'w') as f:
                f.write(template)
            logger.info(f"Created TiDB configuration template at {file_path}")
        except Exception as e:
            logger.error(f"Failed to create config template: {e}")

    @staticmethod
    def validate_tidb_connection(config: Dict[str, Any]) -> bool:
        """Validate TiDB connection configuration"""
        if config.get("type") != "tidb":
            return True  # SQLite doesn't need validation

        conn = config.get("connection", {})
        required_fields = ["host", "user", "password", "database"]

        for field in required_fields:
            if not conn.get(field):
                logger.error(f"Missing required TiDB field: {field}")
                return False

        # Validate port is numeric
        try:
            int(conn.get("port", 4000))
        except (ValueError, TypeError):
            logger.error("Invalid TiDB port number")
            return False

        return True

    @staticmethod
    def get_database_status() -> Dict[str, Any]:
        """Get current database configuration status"""
        config = DatabaseConfig.get_config_from_env()

        return {
            "type": config["type"],
            "is_tidb": config["type"] == "tidb",
            "is_sqlite": config["type"] == "sqlite",
            "connection_info": {
                k: v for k, v in config["connection"].items()
                if k not in ["password"]  # Don't expose password
            },
            "hackathon_ready": config["type"] == "tidb",
            "config_valid": DatabaseConfig.validate_tidb_connection(config)
        }

    @staticmethod
    def setup_development():
        """Quick setup for development environment"""
        os.environ['DATABASE_TYPE'] = 'sqlite'
        os.environ['SQLITE_DB_PATH'] = 'meeting_minutes_dev.db'
        logger.info("Configured for SQLite development environment")

    @staticmethod
    def setup_hackathon_demo():
        """Setup for hackathon demonstration (requires TiDB credentials)"""
        if not os.getenv('TIDB_HOST'):
            logger.error("TiDB credentials not found. Please set TIDB_* environment variables.")
            return False

        os.environ['DATABASE_TYPE'] = 'tidb'
        logger.info("Configured for TiDB hackathon demonstration")
        return True

    @staticmethod
    def get_demo_instructions() -> str:
        """Get setup instructions for hackathon demo"""
        return """
🏆 TiDB AgentX 2025 Hackathon Setup Instructions

1. Development Setup (SQLite):
   export DATABASE_TYPE=sqlite
   export SQLITE_DB_PATH=meeting_minutes.db

2. Production Setup (TiDB):
   export DATABASE_TYPE=tidb
   export TIDB_HOST=your-tidb-cluster.com
   export TIDB_USER=your_username
   export TIDB_PASSWORD=your_password
   export TIDB_DATABASE=scrumy_ai

3. Verify Setup:
   python -c "from app.database_config import DatabaseConfig; print(DatabaseConfig.get_database_status())"

4. Create Config Template:
   python -c "from app.database_config import DatabaseConfig; DatabaseConfig.create_env_file_template()"

🚀 Ready for hackathon demonstration!
        """


def print_hackathon_banner():
    """Print hackathon banner with database status"""
    status = DatabaseConfig.get_database_status()

    print("🏆" * 50)
    print("    TiDB AgentX 2025 Hackathon - Scrumy AI")
    print("🏆" * 50)
    print(f"Database Type: {status['type'].upper()}")
    print(f"Hackathon Ready: {'✅' if status['hackathon_ready'] else '❌'}")
    print(f"Config Valid: {'✅' if status['config_valid'] else '❌'}")

    if status['is_tidb']:
        conn_info = status['connection_info']
        print(f"TiDB Host: {conn_info.get('host', 'Not Set')}")
        print(f"Database: {conn_info.get('database', 'Not Set')}")

    print("🏆" * 50)


if __name__ == "__main__":
    # Demo/test the configuration
    print_hackathon_banner()
    print("\n" + DatabaseConfig.get_demo_instructions())

    # Create template file
    DatabaseConfig.create_env_file_template()