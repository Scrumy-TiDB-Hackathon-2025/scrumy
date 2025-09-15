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
        self.similarity_threshold = 0.4  # Lowered from 0.7 for better meeting data retrieval
        
    async def process_message(self, 
                            message: str, 
                            session_id: str = None,
                            context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a user message and generate a response"""
        if not session_id:
            session_id = str(uuid.uuid4())

        # Initialize variables
        similar_docs = []
        
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
            similar_docs = await self.vector_store.similarity_search(query_embedding, top_k=5)
            
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
        # Check for comprehensive meeting data queries
        meeting_keywords = ['meetings do i have', 'what meetings', 'list meetings', 'all meetings', 'meeting data']
        return any(keyword in message.lower() for keyword in meeting_keywords)

    async def _call_meeting_endpoint(self, message: str) -> Dict:
        """Call comprehensive meeting data endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/meetings/comprehensive")
            return response.json()

    def _format_meeting_response(self, meeting_data: Dict) -> str:
        """Format comprehensive meeting data into a response"""
        if meeting_data.get("status") != "success":
            return "I couldn't retrieve the meeting data properly."
        
        data = meeting_data.get("data", {})
        meetings = data.get("meetings", [])
        tasks = data.get("tasks", [])
        summary = data.get("summary", {})
        
        response_parts = []
        
        # Meeting Overview
        response_parts.append("**Meeting Overview**")
        response_parts.append(f"I have data for {summary.get('total_meetings', 0)} meetings:")
        response_parts.append("")
        
        for meeting in meetings:
            response_parts.append(f"• **{meeting['id']}**")
            response_parts.append(f"  - Title: {meeting['title']}")
            response_parts.append(f"  - Platform: {meeting['platform']}")
            response_parts.append(f"  - Date: {meeting['created_at']}")
            response_parts.append(f"  - Tasks: {meeting['task_count']} tasks")
            if meeting['task_titles'] != "No tasks":
                response_parts.append(f"  - Task Summary: {meeting['task_titles']}")
            response_parts.append("")
        
        # Task Summary
        response_parts.append("**Task Summary**")
        response_parts.append(f"Total Tasks: {summary.get('total_tasks', 0)}")
        response_parts.append("")
        
        # Group tasks by assignee
        assignee_tasks = {}
        for task in tasks:
            assignee = task.get('assignee', 'Unassigned')
            if assignee not in assignee_tasks:
                assignee_tasks[assignee] = []
            assignee_tasks[assignee].append(task)
        
        for assignee, assignee_task_list in assignee_tasks.items():
            response_parts.append(f"**{assignee}** ({len(assignee_task_list)} tasks):")
            for task in assignee_task_list[:3]:  # Show first 3 tasks per assignee
                response_parts.append(f"  - {task['title']} (Priority: {task['priority']}, Status: {task['status']})")
            if len(assignee_task_list) > 3:
                response_parts.append(f"  - ... and {len(assignee_task_list) - 3} more tasks")
            response_parts.append("")
        
        # Data Completeness
        response_parts.append("**Data Completeness**")
        response_parts.append(f"- Meetings: {summary.get('total_meetings', 0)}")
        response_parts.append(f"- Tasks: {summary.get('total_tasks', 0)}")
        response_parts.append(f"- Transcripts: {summary.get('total_transcripts', 0)} transcript segments")
        
        return "\n".join(response_parts)

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
        for doc in relevant_docs[:5]:  # Increased from 3 to 5
            metadata = doc.get('metadata', {})
            doc_type = metadata.get('type', 'general')
            
            if doc_type == 'meeting_summary':
                meeting_id = metadata.get('meeting_id', 'Unknown')
                context_parts.append(f"Meeting {meeting_id}: {doc['text']}")
            elif doc_type == 'task':
                assignee = metadata.get('assignee', 'Unassigned')
                meeting_id = metadata.get('meeting_id', 'Unknown')
                context_parts.append(f"Task from meeting {meeting_id}: {doc['text']} (Assigned to: {assignee})")
            elif doc_type == 'meeting_transcript':
                context_parts.append(f"Meeting Transcript ({metadata.get('timestamp', 'Unknown date')}):\n"
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
            
            system_prompt = """You are Scrumy, an AI-powered project management assistant with comprehensive access to meeting data, tasks, transcripts, and project information.

When asked about "What meetings do I have data for?" or similar queries, provide a COMPLETE overview including:

**Meeting Overview**
- List ALL meetings with their IDs, titles, platforms, and dates
- Include task counts and brief task summaries for each meeting
- Show meeting status and any available transcript information

**Task Summary**
- Total number of tasks across all meetings
- Breakdown by meeting, assignee, priority, and status
- Highlight any overdue or high-priority items

**Data Completeness**
- Specify what types of data are available (transcripts, summaries, tasks)
- Note any meetings with missing information
- Provide context about data quality and completeness

For specific meeting queries, be detailed about:
- Meeting IDs, dates, and platforms
- All participants and their roles
- Complete task assignments with assignees, priorities, and due dates
- Transcript excerpts when relevant
- Action items and follow-up requirements

Always structure responses clearly with headers and bullet points. Be comprehensive rather than brief when listing available data.

If no relevant data is found, clearly state: "I don't have access to meeting data matching your query. The available data includes [list what is available]."

Prioritize completeness and accuracy in data presentation."""

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