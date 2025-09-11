import numpy as np
from typing import List, Dict, Any
import logging
from sqlalchemy import create_engine, text, Engine
import json
import asyncio
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class TiDBVectorStore:
    def __init__(self, engine: Engine):
        """Initialize TiDB vector store with existing engine"""
        self.engine = engine
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._init_tables()

    def _init_tables(self):
        """Initialize required tables"""
        with self.engine.connect() as conn:
            # Updated table schema to use VECTOR type for TiDB
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

    async def add_texts(self, texts: List[str], embeddings: List[List[float]], metadata: List[Dict] = None):
        """Add texts and their embeddings to the store"""
        if metadata is None:
            metadata = [{}] * len(texts)

        try:
            with self.engine.connect() as conn:
                for content, embedding, meta in zip(texts, embeddings, metadata):
                    # Convert embedding to proper format for TiDB VECTOR type
                    embedding_str = json.dumps(embedding)
                    
                    conn.execute(
                        text("""
                            INSERT INTO vector_store (text, embedding, metadata)
                            VALUES (:text, :embedding, :metadata)
                        """),
                        {
                            'text': content,
                            'embedding': embedding_str,
                            'metadata': json.dumps(meta)
                        }
                    )
                conn.commit()
                logger.info(f"Added {len(texts)} texts to vector store")
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            raise

    async def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find similar texts using cosine similarity"""
        try:
            with self.engine.connect() as conn:
                # Use TiDB's vector similarity search
                query_embedding_str = json.dumps(query_embedding)
                
                result = conn.execute(text("""
                    SELECT 
                        id, 
                        text, 
                        metadata,
                        VEC_COSINE_DISTANCE(embedding, :query_embedding) as similarity
                    FROM vector_store
                    ORDER BY similarity ASC
                    LIMIT :k
                """), {
                    'query_embedding': query_embedding_str,
                    'k': top_k
                })
                
                results = []
                for row in result:
                    results.append({
                        'id': row.id,
                        'text': row.text,
                        'metadata': json.loads(row.metadata) if row.metadata else {},
                        'similarity': 1 - row.similarity  # Convert distance to similarity
                    })
                
                return results
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            # Fallback to manual similarity calculation if TiDB vector functions not available
            return await self._manual_similarity_search(query_embedding, k)

    async def _manual_similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Fallback manual similarity search"""
        query_embedding = np.array(query_embedding)
        
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, text, embedding, metadata 
                FROM vector_store
            """))
            
            similarities = []
            for row in result:
                try:
                    # Parse embedding from JSON
                    stored_embedding = np.array(json.loads(row.embedding))
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )
                    similarities.append((similarity, row))
                except Exception as e:
                    logger.warning(f"Error processing embedding for row {row.id}: {e}")
                    continue
            
            # Sort by similarity and get top k
            similarities.sort(reverse=True, key=lambda x: x[0])
            return [{
                'id': row.id,
                'text': row.text,
                'metadata': json.loads(row.metadata) if row.metadata else {},
                'similarity': sim
            } for sim, row in similarities[:top_k]]

    def save_chat_history(self, session_id: str, user_message: str, bot_response: str, metadata: Dict = None):
        """Save chat interaction to history"""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO chat_history (session_id, user_message, bot_response, metadata)
                        VALUES (:session_id, :user_message, :bot_response, :metadata)
                    """),
                    {
                        'session_id': session_id,
                        'user_message': user_message,
                        'bot_response': bot_response,
                        'metadata': json.dumps(metadata or {})
                    }
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")

    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get chat history for a session"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT user_message, bot_response, metadata, created_at 
                        FROM chat_history 
                        WHERE session_id = :session_id 
                        ORDER BY created_at DESC 
                        LIMIT :limit
                    """),
                    {'session_id': session_id, 'limit': limit}
                )
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    def clear_chat_history(self, session_id: str) -> bool:
        """Clear chat history for a session"""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("DELETE FROM chat_history WHERE session_id = :session_id"),
                    {'session_id': session_id}
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
            return False

    async def bootstrap_knowledge_base(self):
        """Initialize the knowledge base with sample data"""
        sample_knowledge = [
            {
                "text": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. It's one of the fastest Python frameworks available.",
                "metadata": {"category": "web_development", "technology": "fastapi"}
            },
            {
                "text": "TiDB is an open-source, cloud-native, distributed, MySQL-Compatible database for elastic scale and real-time analytics. It supports both OLTP and OLAP workloads.",
                "metadata": {"category": "database", "technology": "tidb"}
            },
            {
                "text": "Vector databases store high-dimensional vectors and allow for similarity search. They're commonly used for AI applications like semantic search, recommendation systems, and RAG (Retrieval Augmented Generation).",
                "metadata": {"category": "ai", "technology": "vector_db"}
            },
            {
                "text": "Groq is an AI inference company that provides fast language model processing. It's known for extremely high token throughput and low latency responses.",
                "metadata": {"category": "ai", "technology": "groq"}
            },
            {
                "text": "RAG (Retrieval Augmented Generation) is a technique that combines information retrieval with language generation. It allows AI models to access external knowledge bases to provide more accurate and up-to-date responses.",
                "metadata": {"category": "ai", "concept": "rag"}
            },
            {
                "text": "Python asyncio is a library for writing concurrent code using the async/await syntax. It's particularly useful for I/O-bound tasks and can significantly improve performance in web applications.",
                "metadata": {"category": "programming", "technology": "python"}
            },
            {
                "text": "CORS (Cross-Origin Resource Sharing) is a security feature implemented by web browsers. It allows or restricts web applications running at one domain to access resources from another domain.",
                "metadata": {"category": "web_development", "concept": "security"}
            },
            {
                "text": "Sentence transformers are neural networks that map sentences and paragraphs to dense vector representations. They're commonly used for semantic similarity tasks and information retrieval.",
                "metadata": {"category": "ai", "technology": "transformers"}
            },
            {
                "text": "SQLAlchemy is the Python SQL toolkit and Object Relational Mapping (ORM) library. It provides a full suite of well known enterprise-level persistence patterns.",
                "metadata": {"category": "database", "technology": "python"}
            },
            {
                "text": "API endpoints are specific URLs where an API can access the resources they need. Each endpoint corresponds to a specific function or resource in the application.",
                "metadata": {"category": "web_development", "concept": "api"}
            }
        ]

        try:
            # Check if knowledge base already has data
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) as count FROM vector_store"))
                count = result.fetchone().count
                
                if count > 0:
                    logger.info(f"Knowledge base already contains {count} entries")
                    return

            # Generate embeddings for sample knowledge
            texts = [item["text"] for item in sample_knowledge]
            embeddings = self.embedding_model.encode(texts).tolist()
            metadata_list = [item["metadata"] for item in sample_knowledge]

            # Add to vector store
            await self.add_texts(texts, embeddings, metadata_list)
            logger.info(f"Successfully bootstrapped knowledge base with {len(sample_knowledge)} entries")

        except Exception as e:
            logger.error(f"Error bootstrapping knowledge base: {e}")
            raise