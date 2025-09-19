from sqlalchemy import create_engine
import os

class SharedDBConfig:
    @staticmethod
    def get_vector_store_url():
        host = os.getenv("CHATBOT_TIDB_HOST")
        port = os.getenv("CHATBOT_TIDB_PORT", "4000")
        user = os.getenv("CHATBOT_TIDB_USER")
        password = os.getenv("CHATBOT_TIDB_PASSWORD")
        database = os.getenv("CHATBOT_TIDB_DATABASE")
        
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    @staticmethod
    def get_engine():
        return create_engine(SharedDBConfig.get_vector_store_url())
