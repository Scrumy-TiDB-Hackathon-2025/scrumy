# ScrumBot Chatbot Context Analysis

## Complete Context Flow Analysis

### Current Architecture

```
User Query → ChatBot.process_message() → Context Sources → LLM → Response
                        ↓
            1. Vector Store Search (similarity_search)
            2. Chat History (get_chat_history) 
            3. Meeting Endpoint (disabled)
                        ↓
            _generate_response() → Groq LLM → Formatted Response
```

## Context Sources Deep Dive

### 1. **Vector Store Context** (Primary Source)
**Location**: `TiDBVectorStore.similarity_search()`
**Data**: `vector_store` table in TiDB
**Process**:
```python
# In chatbot.py process_message()
query_embedding = self.embedding_model.encode(message).tolist()
similar_docs = await self.vector_store.similarity_search(query_embedding, top_k=3)
```

**Current Issues**:
- **Similarity Threshold**: 0.7 (too high - filters out relevant meeting data)
- **Limited Results**: Only top 3 documents
- **No Meeting-Specific Search**: Treats all content equally

### 2. **Chat History Context** (Secondary Source)
**Location**: `TiDBVectorStore.get_chat_history()`
**Data**: `chat_history` table in TiDB
**Process**:
```python
history = self.vector_store.get_chat_history(session_id, limit=5)
```

**Current State**: ✅ Working properly

### 3. **Meeting Endpoint Context** (Disabled)
**Location**: `_call_meeting_endpoint()` 
**Status**: Disabled via `_requires_meeting_processing() → return False`

## Meeting Data Access Gaps

### **Gap 1: No Direct TiDB Meeting Access**
**Problem**: Chatbot only accesses meeting data through vector store
**Missing**: Direct queries to `meetings`, `tasks`, `transcript_chunks` tables

**Current Vector Store Schema**:
```sql
CREATE TABLE vector_store (
    id INT PRIMARY KEY AUTO_INCREMENT,
    text TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    metadata JSON,  -- Contains meeting_id, type, category
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Missing Meeting Tables Access**:
```sql
-- These tables exist but chatbot can't query them directly
meetings (id, title, created_at)
tasks (id, meeting_id, title, description, assignee, status)
transcript_chunks (id, meeting_id, transcript_text, timestamp, speaker)
transcripts (id, meeting_id, transcript_text, timestamp)
participants (id, meeting_id, name, platform_id, status)
```

### **Gap 2: Similarity Threshold Too High**
**Current**: `self.similarity_threshold = 0.7`
**Issue**: Meeting queries often score 0.5-0.6 similarity
**Result**: Relevant meeting data filtered out

### **Gap 3: Limited Context Formatting**
**Current**: Only handles `meeting_transcript` metadata type
**Missing**: Proper formatting for `meeting_summary`, `task`, `participant` types

## Solutions for Complete Meeting Data Access

### **Solution 1: Hybrid Context Retrieval**
```python
async def _get_meeting_context(self, message: str, query_embedding: List[float]):
    """Enhanced context retrieval combining vector search + direct DB queries"""
    
    # 1. Vector search (existing)
    vector_results = await self.vector_store.similarity_search(query_embedding, top_k=5)
    
    # 2. Direct meeting data queries for meeting-related keywords
    meeting_context = {}
    if self._is_meeting_query(message):
        meeting_context = await self._query_meeting_data_directly(message)
    
    # 3. Combine contexts
    return self._merge_contexts(vector_results, meeting_context)

def _is_meeting_query(self, message: str) -> bool:
    """Detect meeting-related queries"""
    keywords = ['meeting', 'task', 'recorded', 'transcript', 'participant', 'assigned']
    return any(keyword in message.lower() for keyword in keywords)
```

### **Solution 2: Lower Similarity Threshold**
```python
# In chatbot.py __init__
self.similarity_threshold = 0.4  # Lower from 0.7 to 0.4
```

### **Solution 3: Enhanced Metadata Handling**
```python
def _format_knowledge_context(self, similar_docs: List[Dict]) -> str:
    """Enhanced context formatting for all meeting data types"""
    context_parts = []
    for doc in similar_docs:
        metadata = doc.get('metadata', {})
        doc_type = metadata.get('type', 'general')
        
        if doc_type == 'meeting_summary':
            context_parts.append(f"Meeting {metadata.get('meeting_id')}: {doc['text']}")
        elif doc_type == 'task':
            context_parts.append(f"Task: {doc['text']} (Assignee: {metadata.get('assignee', 'Unknown')})")
        elif doc_type == 'meeting_transcript':
            context_parts.append(f"Transcript: {doc['text']}")
        else:
            context_parts.append(doc['text'])
    
    return "\n\n".join(context_parts)
```

### **Solution 4: Direct TiDB Integration**
```python
class ChatBot:
    def __init__(self, vector_store: TiDBVectorStore, tidb_engine: Engine, ...):
        self.vector_store = vector_store
        self.tidb_engine = tidb_engine  # Direct access to meeting tables
        
    async def _query_meeting_data_directly(self, message: str) -> Dict:
        """Query meeting tables directly for comprehensive data"""
        with self.tidb_engine.connect() as conn:
            # Recent meetings
            meetings = conn.execute(text("""
                SELECT id, title, created_at FROM meetings 
                ORDER BY created_at DESC LIMIT 5
            """)).fetchall()
            
            # Recent tasks
            tasks = conn.execute(text("""
                SELECT t.title, t.description, t.assignee, t.status, m.title as meeting_title
                FROM tasks t JOIN meetings m ON t.meeting_id = m.id
                ORDER BY t.created_at DESC LIMIT 10
            """)).fetchall()
            
            return {
                'meetings': [dict(row._mapping) for row in meetings],
                'tasks': [dict(row._mapping) for row in tasks]
            }
```

## Implementation Priority

### **Phase 1: Quick Fixes** (30 minutes)
1. Lower similarity threshold: 0.7 → 0.4
2. Increase search results: top_k=3 → top_k=5
3. Enhanced metadata formatting

### **Phase 2: Hybrid Context** (2 hours)
1. Add direct TiDB engine to ChatBot
2. Implement meeting-specific queries
3. Merge vector + direct query results

### **Phase 3: Advanced Features** (4 hours)
1. Meeting-aware search (filter by meeting_id)
2. Time-based queries (recent meetings, today's tasks)
3. Participant-specific queries

## Current Vector Store Population Status

### ✅ **Working**: Meeting data is being added to vector store
**Location**: `websocket_server.py._populate_vector_store()`
**Triggered**: During meeting processing after AI summary generation
**Data Added**:
- Meeting summaries with metadata: `{"type": "meeting_summary", "meeting_id": "...", "category": "meeting"}`
- Tasks with metadata: `{"type": "task", "meeting_id": "...", "category": "task", "assignee": "..."}`

### ⚠️ **Issue**: Similarity threshold prevents retrieval
**Test Results**:
- Knowledge successfully added to vector store ✅
- Search finds results ✅  
- Chatbot filters out results due to 0.7 threshold ❌

## Recommended Implementation

### **Immediate Fix** (5 minutes):
```python
# In ai_chatbot/app/chatbot.py line 17
self.similarity_threshold = 0.4  # Change from 0.7
```

### **Enhanced Context** (30 minutes):
```python
# Add to ChatBot.__init__
from sqlalchemy import Engine

def __init__(self, vector_store: TiDBVectorStore, tidb_engine: Engine = None, ...):
    self.tidb_engine = tidb_engine or vector_store.engine

# Add meeting-specific context method
async def _get_enhanced_context(self, message: str, query_embedding: List[float]):
    # Vector search with lower threshold
    vector_docs = await self.vector_store.similarity_search(query_embedding, top_k=5)
    
    # Direct meeting queries for meeting-related questions
    if any(kw in message.lower() for kw in ['meeting', 'task', 'recorded']):
        meeting_data = await self._query_recent_meetings()
        # Format and combine with vector results
    
    return combined_context
```

This analysis shows the chatbot has solid foundation but needs threshold adjustment and enhanced meeting data access for optimal performance.