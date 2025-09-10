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
from .utils.key_manager import GroqKeyManager

logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self, vector_store: TiDBVectorStore, model_name: str = "llama-3.3-70b-versatile", key_manager: Optional[GroqKeyManager] = None):
        self.vector_store = vector_store
        self.model_name = model_name
        self.key_manager = key_manager or GroqKeyManager()
        self.client = None  # Will be initialized per request
        
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
        
        relevant_docs = [doc for doc in similar_docs if doc.get('similarity', 0) > self.similarity_threshold]
        if not relevant_docs:
            return ""
        
        context_parts = []
        for doc in relevant_docs[:3]:
            metadata = doc.get('metadata', {})
            if metadata.get('type') == 'meeting_transcript':
                context_parts.append(f"Meeting Context ({metadata.get('timestamp', 'Unknown date')}):\n"
                                   f"Summary: {metadata.get('summary', 'Not available')}\n"
                                   f"Content: {doc['text']}")
            else:
                context_parts.append(f"Context: {doc['text']}")
        
        return "\n\n".join(context_parts)

    async def _get_groq_client(self):
        """Get a Groq client with the current API key"""
        api_key = await self.key_manager.get_key()
        return AsyncGroq(api_key=api_key)

    async def _generate_response(self, 
                               message: str, 
                               similar_docs: List[Dict], 
                               history: List[Dict]) -> str:
        """Generate response using Groq with retrieved context"""
        try:
            client = await self._get_groq_client()
            
            # Filter out irrelevant docs based on similarity threshold
            relevant_docs = [doc for doc in similar_docs if doc.get('similarity', 0) > self.similarity_threshold]
            knowledge_context = self._format_knowledge_context(relevant_docs)
            
            system_prompt = """You are Scrumy, an AI-powered project management assistant. 
Format your responses as follows:

**Analysis of Available Data**

[Provide a clear, concise analysis of the relevant information from the knowledge base]

**Key Points**
- [List key points extracted from the data]
- [Include only information that directly answers the user's question]

**Additional Context**
[If applicable, provide relevant project management context]

If the data doesn't contain information relevant to the question, clearly state:
"I don't have enough information in the available data to answer this question accurately."

Be concise and professional. Never mention source numbers or irrelevant information."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Available context:\n{knowledge_context}" if knowledge_context else "No relevant data found."},
                {"role": "user", "content": message}
            ]

            # Add historical context if available
            if history:
                messages[1:1] = self._format_history(history)
            
            completion = await client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.3,  # Lower temperature for more consistent formatting
                max_tokens=1024
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
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

    async def search_knowledge(self, query: str, top_k: int = 5, session_id: str = None) -> Dict:
        """Search the knowledge base and generate a response"""
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search vector store
            similar_docs = await self.vector_store.similarity_search(query_embedding, top_k)
            
            # Get chat history if session_id is provided
            history = self.vector_store.get_chat_history(session_id, limit=5) if session_id else []
            
            # Generate response using the search results
            response = await self._generate_response(query, similar_docs, history)
            
            return {
                "response": response,
                "sources": len(similar_docs)
            }
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return {
                "response": "I encountered an error while searching the knowledge base.",
                "sources": 0,
                "metadata": {"error": str(e)}
            }