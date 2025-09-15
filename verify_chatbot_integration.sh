#!/bin/bash

echo "🔍 ScrumBot Chatbot Integration Verification"
echo "=========================================="

# Test 1: Check if chatbot is running
echo "1. Testing chatbot health..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Chatbot is running on port 8001"
else
    echo "❌ Chatbot is not running on port 8001"
    exit 1
fi

# Test 2: Check database access
echo "2. Testing database access..."
MEETING_COUNT=$(curl -s "http://localhost:8001/meetings/verify" | jq -r '.data_access.meetings_count // 0')
echo "📊 Database has $MEETING_COUNT meetings"

# Test 3: Force populate vector store
echo "3. Populating vector store..."
POPULATE_RESULT=$(curl -s -X POST "http://localhost:8001/meetings/populate-vector-store")
POPULATE_STATUS=$(echo "$POPULATE_RESULT" | jq -r '.status // "error"')
if [ "$POPULATE_STATUS" = "success" ]; then
    ITEMS_ADDED=$(echo "$POPULATE_RESULT" | jq -r '.details.total_items // 0')
    echo "✅ Vector store populated with $ITEMS_ADDED items"
else
    ERROR_MSG=$(echo "$POPULATE_RESULT" | jq -r '.error // "Unknown error"')
    echo "❌ Failed to populate vector store: $ERROR_MSG"
fi

# Test 4: Test chatbot query
echo "4. Testing chatbot query..."
CHATBOT_RESPONSE=$(curl -s -X POST "http://localhost:8001/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "What meetings do I have data for?", "session_id": "verification_test"}')

RESPONSE_TEXT=$(echo "$CHATBOT_RESPONSE" | jq -r '.response // "No response"')
CONTEXT_USED=$(echo "$CHATBOT_RESPONSE" | jq -r '.metadata.context_used // false')

if [ "$CONTEXT_USED" = "true" ]; then
    echo "✅ Chatbot has access to meeting data"
    echo "📝 Response preview: ${RESPONSE_TEXT:0:100}..."
else
    echo "❌ Chatbot does not have access to meeting data"
    echo "📝 Response: $RESPONSE_TEXT"
fi

# Test 5: Check WebSocket server
echo "5. Testing WebSocket server..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ WebSocket server is running on port 8080"
else
    echo "❌ WebSocket server is not running on port 8080"
fi

echo ""
echo "🎯 Integration Status Summary:"
echo "- Chatbot Service: $(curl -s http://localhost:8001/health > /dev/null && echo "✅ Running" || echo "❌ Down")"
echo "- WebSocket Server: $(curl -s http://localhost:8080/health > /dev/null && echo "✅ Running" || echo "❌ Down")"
echo "- Database Access: $([ "$MEETING_COUNT" -gt 0 ] && echo "✅ $MEETING_COUNT meetings" || echo "❌ No meetings")"
echo "- Vector Store: $([ "$POPULATE_STATUS" = "success" ] && echo "✅ Populated" || echo "❌ Failed")"
echo "- Chatbot Context: $([ "$CONTEXT_USED" = "true" ] && echo "✅ Has Data" || echo "❌ No Data")"

echo ""
echo "🚀 Ready for test recording!"