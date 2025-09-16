-- TiDB Compatible Queries for ScrumBot Meeting Data
-- Copy and paste each query individually into TiDB SQL Editor

-- QUERY 1: Summary of all data (run this first)
SELECT 'meetings' as table_name, COUNT(*) as record_count FROM meetings
UNION ALL
SELECT 'transcript_chunks' as table_name, COUNT(*) as record_count FROM transcript_chunks
UNION ALL
SELECT 'transcripts' as table_name, COUNT(*) as record_count FROM transcripts
UNION ALL
SELECT 'participants' as table_name, COUNT(*) as record_count FROM participants
UNION ALL
SELECT 'tasks' as table_name, COUNT(*) as record_count FROM tasks;

-- QUERY 2: Latest meetings
SELECT id, title, created_at FROM meetings ORDER BY created_at DESC LIMIT 10;

-- QUERY 3: Recent transcript chunks
SELECT meeting_id, SUBSTRING(transcript_text, 1, 50) as preview, timestamp, speaker FROM transcript_chunks ORDER BY timestamp DESC LIMIT 15;

-- QUERY 4: Full transcripts
SELECT meeting_id, SUBSTRING(transcript_text, 1, 100) as preview, timestamp FROM transcripts ORDER BY timestamp DESC LIMIT 10;

-- QUERY 5: Participants
SELECT meeting_id, name, platform_id, status, is_host FROM participants ORDER BY created_at DESC LIMIT 15;

-- QUERY 6: Tasks from meetings
SELECT meeting_id, title, assignee, status, priority, created_at FROM tasks ORDER BY created_at DESC LIMIT 10;

-- QUERY 7: Meeting activity (meetings with transcript counts)
SELECT m.id, m.title, COUNT(tc.id) as transcript_count FROM meetings m LEFT JOIN transcript_chunks tc ON m.id = tc.meeting_id GROUP BY m.id, m.title ORDER BY transcript_count DESC LIMIT 5;