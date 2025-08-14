# ScrumBot Integration Testing Guide

## Overview
This guide covers the integration testing phase where all team components are connected and tested together.

## Prerequisites
- All team members have completed their individual epic development
- Docker and Docker Compose installed
- TiDB Serverless cluster configured
- Environment variables set up

## Integration Testing Steps

### Phase 1: Component Integration (Day 6)

#### 1. Environment Setup
```bash
# Ensure all team members are on dev branch
git checkout dev
git pull origin dev

# Set up environment variables
cp integration/.env.example integration/.env
# Edit integration/.env with your actual values
```

#### 2. Start All Services
```bash
cd integration/docker
docker-compose up --build
```

#### 3. Test Individual Components
```bash
# Test AI Backend
curl http://localhost:5167/health

# Test Notion MCP
curl http://localhost:8081/health

# Test Slack MCP  
curl http://localhost:8082/health

# Test Integration API
curl http://localhost:3003/health

# Test Frontend
open http://localhost:3004
```

### Phase 2: End-to-End Testing (Day 6-7)

#### 1. Chrome Extension → AI Backend Flow
1. Install Chrome extension from `chrome_extension/` folder
2. Join a Google Meet call
3. Start recording via extension
4. Verify transcription appears in backend logs
5. Check TiDB for stored transcripts

#### 2. AI Processing → MCP Flow
1. Send sample transcript to AI backend
2. Verify AI processing (speakers, summary, tasks)
3. Check task creation in Notion
4. Verify Slack notifications sent
5. Confirm TiDB task synchronization

#### 3. Frontend Integration
1. Open frontend dashboard
2. View meeting history from TiDB
3. Test real-time transcript display
4. Verify task management interface
5. Check analytics and insights

### Phase 3: Performance Testing

#### Load Testing
```bash
# Test concurrent meetings
for i in {1..5}; do
  curl -X POST http://localhost:5167/process-transcript \
    -H "Content-Type: application/json" \
    -d @../shared/mock-data/sample-meeting.json &
done
```

#### Database Performance
```sql
-- Test TiDB query performance
SELECT COUNT(*) FROM meetings WHERE created_at > NOW() - INTERVAL 1 DAY;
SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority DESC;
```

## Integration Checklist

### ✅ Component Integration
- [ ] AI Backend connects to TiDB
- [ ] Ollama models loaded and responding
- [ ] Notion MCP creates tasks successfully
- [ ] Slack MCP sends notifications
- [ ] Frontend displays data from all services

### ✅ Data Flow Integration
- [ ] Chrome extension → AI backend → TiDB
- [ ] AI processing → Task extraction → MCP servers
- [ ] TiDB → Frontend dashboard display
- [ ] Cross-platform task synchronization

### ✅ Error Handling
- [ ] Service failures handled gracefully
- [ ] Database connection errors managed
- [ ] API rate limits respected
- [ ] User-friendly error messages

### ✅ Performance
- [ ] Response times under 5 seconds
- [ ] Concurrent user support
- [ ] Database queries optimized
- [ ] Memory usage within limits

## Troubleshooting

### Common Issues
1. **TiDB Connection Errors**: Check connection string format
2. **Ollama Model Loading**: Ensure sufficient memory allocated
3. **MCP Authentication**: Verify API tokens and permissions
4. **CORS Issues**: Check frontend-backend communication

### Debug Commands
```bash
# Check service logs
docker-compose logs ai-backend
docker-compose logs notion-mcp
docker-compose logs slack-mcp

# Check TiDB connectivity
mysql -h gateway01.us-west-2.prod.aws.tidbcloud.com -P 4000 -u username -p

# Test API endpoints
curl -v http://localhost:5167/health
```

## Success Criteria
- All services start without errors
- End-to-end flow works: Extension → AI → MCP → Frontend
- Data persists correctly in TiDB
- Tasks appear in Notion and Slack
- Frontend displays real-time updates
- Performance meets requirements (< 5s response time)

## Final Deployment
Once integration testing passes, the system is ready for production deployment to Railway/Vercel.