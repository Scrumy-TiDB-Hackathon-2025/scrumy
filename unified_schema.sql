-- Add ai_processing tables to existing chatbot database
-- This extends the current vector_store, chat_history, vector_data tables

-- Meetings table
CREATE TABLE IF NOT EXISTS meetings (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tasks table  
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(255) PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    assignee VARCHAR(255),
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id VARCHAR(255) PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    transcript TEXT NOT NULL,
    timestamp VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

-- Update existing vector_store to link with meetings/tasks
ALTER TABLE vector_store ADD COLUMN meeting_id VARCHAR(255);
ALTER TABLE vector_store ADD COLUMN task_id VARCHAR(255);
ALTER TABLE vector_store ADD FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE;
ALTER TABLE vector_store ADD FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE;

-- Update chat_history to link with meetings
ALTER TABLE chat_history ADD COLUMN meeting_id VARCHAR(255);
ALTER TABLE chat_history ADD FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE SET NULL;