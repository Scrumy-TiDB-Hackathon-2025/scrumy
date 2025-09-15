# ScrumBot Chatbot Integration Test Script

## Pre-Test Setup
1. Ensure WebSocket server is running on port 8080
2. Ensure chatbot is running on port 8001
3. Open Chrome extension and navigate to Google Meet
4. Open chatbot interface at http://localhost:3000

## Test Script to Recite

### Phase 1: Meeting Start (0-30 seconds)
**Say this clearly into your microphone:**

"Hello everyone, welcome to our ScrumBot integration test meeting. My name is Alex Johnson and I'll be leading today's session. We have three main agenda items to cover today."

**Immediately test chatbot:**
- Ask: "What meeting is currently happening?"
- Expected: Should mention current meeting or say no current meeting data

### Phase 2: Task Assignment (30-60 seconds)
**Continue speaking:**

"First, Sarah needs to complete the user authentication module by Friday. This is a high priority task. Second, Mike will work on the database integration and should finish by Wednesday. Third, Lisa is responsible for writing unit tests for the payment system."

**Test chatbot during recording:**
- Ask: "What tasks have been mentioned so far?"
- Expected: Should mention tasks being discussed in real-time

### Phase 3: Meeting Discussion (60-90 seconds)
**Continue speaking:**

"Let's discuss the current sprint progress. We've completed 8 out of 12 user stories. The main blocker is the API integration with the third-party service. We need to resolve this by tomorrow to stay on track."

**Test chatbot:**
- Ask: "What blockers were mentioned?"
- Expected: Should reference API integration blocker

### Phase 4: Meeting End (90-120 seconds)
**Conclude the meeting:**

"To summarize, we have three action items: Sarah's authentication module, Mike's database work, and Lisa's unit tests. Our next standup is tomorrow at 9 AM. Thank you everyone for attending."

**End the recording in Chrome extension**

## Post-Meeting Tests (Wait 30 seconds after ending)

### Test 1: Meeting Data Access
**Ask chatbot:** "What meetings do I have data for?"
**Expected:** Should list the test meeting with details

### Test 2: Task Retrieval
**Ask chatbot:** "What tasks were assigned to Sarah?"
**Expected:** Should mention user authentication module due Friday

### Test 3: Meeting Summary
**Ask chatbot:** "Summarize the most recent meeting"
**Expected:** Should provide summary with participants, tasks, and blockers

### Test 4: Specific Details
**Ask chatbot:** "What was the main blocker discussed?"
**Expected:** Should mention API integration with third-party service

### Test 5: Participant Information
**Ask chatbot:** "Who attended the meeting?"
**Expected:** Should mention Alex Johnson and other participants

## Success Criteria

✅ **During Recording:**
- Chatbot responds to queries about ongoing meeting
- Real-time transcript chunks are accessible
- Live context is available

✅ **After Recording:**
- Meeting appears in "What meetings do I have data for?"
- All tasks are retrievable with correct assignees
- Meeting summary includes key points and blockers
- Participant information is preserved
- Specific details can be queried accurately

## Troubleshooting

If chatbot says "I don't have data":
1. Check WebSocket server logs for transcript saving
2. Verify chatbot vector store population
3. Check database for meeting records
4. Ensure /meetings/populate-vector-store was called

## Quick Verification Commands

```bash
# Check if meeting was saved to database
curl -s "http://localhost:8001/meetings/verify" | jq '.data_access.recent_meetings[0]'

# Force populate vector store
curl -X POST "http://localhost:8001/meetings/populate-vector-store"

# Test chatbot directly
curl -X POST "http://localhost:8001/chat" -H "Content-Type: application/json" -d '{"message": "What meetings do I have data for?", "session_id": "test"}' | jq -r '.response'
```