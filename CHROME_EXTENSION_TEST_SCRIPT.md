# Chrome Extension Test Script

## 🎯 **Test Objective**
Validate end-to-end Chrome extension integration with real meeting audio capture and task creation.

## ✅ **Pre-Test Checklist**
- [ ] Backend server running (`./clean_start_backend.sh`)
- [ ] WebSocket server running (`python start_websocket_server.py`)
- [ ] Chrome extension loaded in browser
- [ ] Test meeting URL ready (Google Meet/Zoom)

## 📝 **Test Script to Recite**

### **Meeting Setup (30 seconds)**
*"This is a test meeting for ScrumBot Chrome extension integration on [DATE]. We're testing the complete audio-to-task pipeline with real-time processing."*

### **Sprint Planning Simulation (2-3 minutes)**

**Speaker 1 (You as Product Manager):**
*"Alright team, let's review our sprint goals for this week. We have three main priorities: user authentication, API documentation, and staging deployment."*

**Speaker 2 (You as Developer - John):**
*"I can take the user authentication implementation. I'll need to update the login API and ensure proper session management. I should have this completed by Wednesday."*

**Speaker 3 (You as DevOps - Mike):**  
*"I'll handle the staging deployment. We need to get the new environment configured with proper SSL certificates and load balancing. Target completion is Thursday."*

**Speaker 4 (You as QA - Lisa):**
*"Once staging is ready, I'll run the comprehensive test suite. This includes security testing, performance validation, and user acceptance testing. Critical for our Friday release."*

**Speaker 1 (Product Manager):**
*"Great assignments everyone. John, can you also investigate those database performance issues we've been seeing in production? The slow query reports are concerning."*

**Speaker 2 (Developer - John):**
*"Absolutely. I'll look into optimizing the database indexes as well. That should help with the query performance we've been tracking."*

**Speaker 3 (DevOps - Mike):**
*"I should follow up on the staging deployment to make sure everything is running smoothly after the initial setup. I'll monitor for 24 hours post-deployment."*

**Speaker 1 (Product Manager):**
*"Perfect. Let's also make sure someone researches the database performance issues more thoroughly for our next sprint planning. We need a comprehensive analysis."*

**Meeting Conclusion:**
*"This concludes our test meeting. Thank you everyone. ScrumBot should now process this audio and create tasks in our integrated systems."*

## 🔍 **Expected Results**

### **Tasks to be Created:**
1. **Implement user authentication** (John, due Wednesday)
2. **Configure staging deployment** (Mike, due Thursday)  
3. **Run comprehensive test suite** (Lisa, after staging)
4. **Investigate database performance issues** (John)
5. **Optimize database indexes** (John)
6. **Follow up on staging deployment** (Mike)
7. **Research database performance issues** (Unassigned, next sprint)

### **Integration Platforms:**
- **Notion**: 7 tasks created with proper assignees and descriptions
- **ClickUp**: 7 tasks created with priority and status
- **Slack**: Notifications sent to configured channels

## 📊 **Success Criteria**

### **Chrome Extension:**
- [ ] Audio capture starts/stops correctly
- [ ] Real-time WebSocket connection maintained
- [ ] No browser console errors
- [ ] Extension popup shows recording status

### **Backend Processing:**
- [ ] Audio chunks received via WebSocket
- [ ] Whisper transcription working
- [ ] Speaker identification functional
- [ ] Groq API calls optimized (batched)

### **Task Creation:**
- [ ] 7 tasks extracted from meeting
- [ ] Tasks created in Notion with URLs
- [ ] Tasks created in ClickUp with URLs
- [ ] Slack notifications sent
- [ ] All assignees properly mapped

### **Performance Metrics:**
- [ ] Processing time < 30 seconds after meeting ends
- [ ] Memory usage stable during processing
- [ ] No API rate limit errors
- [ ] WebSocket connection stable throughout

## 🐛 **Troubleshooting**

### **If Extension Doesn't Start Recording:**
1. Check microphone permissions in Chrome
2. Verify extension is loaded and enabled
3. Check browser console for errors
4. Ensure WebSocket server is running on port 8080

### **If No Tasks Are Created:**
1. Check backend logs for errors
2. Verify Groq API key is valid
3. Check integration credentials (Notion, ClickUp)
4. Ensure audio was properly transcribed

### **If WebSocket Disconnects:**
1. Check network connectivity
2. Verify WebSocket server is running
3. Check for firewall blocking port 8080
4. Restart WebSocket server if needed

## 📋 **Post-Test Verification**

### **Check Created Tasks:**
1. **Notion**: Visit workspace and verify 7 tasks created
2. **ClickUp**: Check list for new tasks with proper details
3. **Slack**: Confirm notifications were sent

### **Verify Task Details:**
- [ ] Task titles match meeting discussion
- [ ] Assignees correctly identified
- [ ] Due dates captured where mentioned
- [ ] Descriptions include relevant context

### **Performance Review:**
- [ ] Check backend logs for processing time
- [ ] Verify memory usage remained stable
- [ ] Confirm no API errors occurred
- [ ] Review WebSocket connection stability

## 🎉 **Success Confirmation**

**Test PASSES if:**
- Chrome extension captures audio successfully
- 7 tasks created across all platforms
- Task details match meeting content
- Processing completes within 30 seconds
- No critical errors in logs

**Ready for production deployment!** 🚀