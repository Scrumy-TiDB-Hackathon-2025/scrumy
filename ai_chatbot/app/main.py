from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
import asyncio
from dotenv import load_dotenv
from .chatbot import ChatBot
from .tidb_vector_store import TiDBVectorStore
from .tidb_connection import TiDBConnection
from .utils.key_manager import GroqKeyManager
from sqlalchemy import text

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Chatbot API",
    description="Chatbot API with TiDB vector store and Groq",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize TiDB connection
tidb_conn = TiDBConnection()
if not tidb_conn.initialize():
    raise RuntimeError("Failed to initialize TiDB connection")

# Initialize vector store
vector_store = TiDBVectorStore(tidb_conn.get_engine())

# Initialize key manager
key_manager = GroqKeyManager()

# Initialize chatbot with Groq and key manager
chatbot = ChatBot(vector_store, model_name="llama-3.3-70b-versatile", key_manager=key_manager)

# Initialize knowledge base on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the knowledge base with sample data"""
    try:
        await vector_store.bootstrap_knowledge_base()
        print("✅ Knowledge base initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize knowledge base: {e}")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    metadata: Dict

class KnowledgeRequest(BaseModel):
    content: str
    metadata: Optional[Dict] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process a chat message and return a response"""
    try:
        result = await chatbot.process_message(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/add")
async def add_knowledge(request: KnowledgeRequest):
    """Add new knowledge to the vector store"""
    try:
        success = await chatbot.add_knowledge(request.content, request.metadata)
        if success:
            return {"status": "success", "message": "Knowledge added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/search")
async def search_knowledge(query: str, session_id: Optional[str] = None, top_k: int = 5):
    """Search the knowledge base"""
    try:
        results = await chatbot.search_knowledge(query, top_k, session_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 10):
    """Get chat history for a session"""
    try:
        history = vector_store.get_chat_history(session_id, limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    try:
        success = vector_store.clear_chat_history(session_id)
        if success:
            return {"status": "success", "message": "Chat history cleared"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear chat history")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Check if the chatbot service is healthy"""
    try:
        # Test TiDB connection
        with tidb_conn.get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "services": {
                "tidb": "connected",
                "groq": "configured",
                "vector_store": "ready"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Add a new endpoint to get key usage statistics
@app.get("/stats/keys")
async def get_key_stats():
    """Get usage statistics for API keys"""
    return {"keys": key_manager.get_key_stats()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)