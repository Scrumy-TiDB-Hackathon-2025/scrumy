from typing import List, Dict, Any, Optional
import httpx
import asyncio
from groq import AsyncGroq
import logging
import json
import uuid
import os
from .tidb_vector_store import TiDBVectorStore
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self, vector_store: TiDBVectorStore, model_name: str = "llama-3.3-70b-versatile"):
        self.vector_store = vector_store
        self.model_name = model_name
        
        # Get API key from environment variable
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
            
        # Initialize Groq client with API key from environment
        self.client = AsyncGroq(api_key=groq_api_key)
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_threshold = 0.7
        
    async def process_message(self, 
                            message: str, 
                            session_id: str = None,
                            context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a user message and generate a response"""
        if not session_id:
            session_id = str(uuid.uuid4())

        # Check if we need to call other endpoints
        if self._requires_meeting_processing(message):
            try:
                meeting_data = await self._call_meeting_endpoint(message)
                response = self._format_meeting_response(meeting_data)
            except Exception as e:
                logger.error(f"Error calling meeting endpoint: {e}")
                response = "I encountered an error processing the meeting data."
        else:
            # Get embedding for the message
            query_embedding = self.embedding_model.encode(message).tolist()
            
            # Get relevant context from vector store
            similar_docs = await self.vector_store.similarity_search(query_embedding, top_k=3)
            
            # Get chat history for conversation context
            history = self.vector_store.get_chat_history(session_id, limit=5)
            
            # Generate response using both knowledge base and chat history
            response = await self._generate_response(message, similar_docs, history)

        # Save interaction to history
        self.vector_store.save_chat_history(
            session_id=session_id,
            user_message=message,
            bot_response=response,
            metadata=context
        )

        return {
            "session_id": session_id,
            "response": response,
            "metadata": {
                "model": self.model_name,
                "context_used": len(similar_docs) > 0,
                "similarity_scores": [doc.get('similarity', 0) for doc in similar_docs]
            }
        }

    def _requires_meeting_processing(self, message: str) -> bool:
        """Check if message requires calling meeting processing endpoints"""
        keywords = ['meeting', 'transcript', 'summary', 'recording']
        return any(keyword in message.lower() for keyword in keywords)

    async def _call_meeting_endpoint(self, message: str) -> Dict:
        """Call appropriate meeting processing endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5167/process-complete-meeting",
                json={
                    "text": message,
                    "model": "groq",
                    "model_name": self.model_name,
                    "meeting_id": str(uuid.uuid4())
                }
            )
            return response.json()

    def _format_meeting_response(self, meeting_data: Dict) -> str:
        """Format meeting processing results into a response"""
        if meeting_data.get("status") == "success":
            summary = meeting_data.get("summary", {})
            return f"""Here's what I found in the meeting:
- Overview: {summary.get('overview', 'Not available')}
- Key Points: {', '.join(summary.get('key_points', ['None found']))}
- Action Items: {', '.join(summary.get('action_items', ['None found']))}"""
        return "I couldn't process the meeting data properly."

    def _format_history(self, history: List[Dict]) -> List[Dict[str, str]]:
        """Format chat history for context"""
        formatted_history = []
        for h in reversed(history[-5:]):  # Only last 5 exchanges
            formatted_history.extend([
                {"role": "user", "content": h["user_message"]},
                {"role": "assistant", "content": h["bot_response"]}
            ])
        return formatted_history

    def _format_knowledge_context(self, similar_docs: List[Dict]) -> str:
        """Format retrieved documents into context"""
        if not similar_docs:
            return ""
        
        # Only use documents above similarity threshold
        relevant_docs = [doc for doc in similar_docs if doc.get('similarity', 0) > self.similarity_threshold]
        
        if not relevant_docs:
            return ""
        
        context_parts = []
        for doc in relevant_docs[:3]:  # Top 3 most similar
            context_parts.append(f"Context: {doc['text']}")
        
        return "\n".join(context_parts)

    async def _generate_response(self, 
                               message: str, 
                               similar_docs: List[Dict], 
                               history: List[Dict]) -> str:
        """Generate response using Groq with retrieved context"""
        try:
            # Build context from knowledge base
            knowledge_context = self._format_knowledge_context(similar_docs)
            
            # Build conversation history
            context_messages = self._format_history(history)
            
            # Create system prompt with context
            system_prompt = """You are a helpful AI assistant. 
Use the provided context information to answer questions accurately. 
If the context doesn't contain relevant information, answer based on your general knowledge.
Be concise and helpful."""
            
            if knowledge_context:
                system_prompt += f"\n\nRelevant context:\n{knowledge_context}"
            
            # Build messages for Groq
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(context_messages)
            messages.append({"role": "user", "content": message})
            
            completion = await self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.7,
                max_tokens=1024
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            return "I'm having trouble generating a response right now. Please try again."

    async def add_knowledge(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add new knowledge to the vector store"""
        try:
            # Generate embedding for the content
            embedding = self.embedding_model.encode(content).tolist()
            
            # Add to vector store
            await self.vector_store.add_texts([content], [embedding], [metadata or {}])
            return True
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return False

    async def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search the knowledge base"""
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search vector store
            return await self.vector_store.similarity_search(query_embedding, top_k)
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []