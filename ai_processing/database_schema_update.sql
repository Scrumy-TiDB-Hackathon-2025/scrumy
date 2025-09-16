-- Database Schema Update: Support All AI-Extracted Task Fields
-- Compatible with both SQLite (test) and TiDB (production)

-- =====================================================
-- TASKS TABLE SCHEMA UPDATE
-- =====================================================

-- Drop existing tasks table if you want to recreate (CAUTION: This will lose data!)
-- DROP TABLE IF EXISTS tasks;

-- Create enhanced tasks table with all AI-extracted fields
CREATE TABLE IF NOT EXISTS tasks (
    -- Core database fields
    id INT AUTO_INCREMENT PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    
    -- Basic task fields (already supported)
    title VARCHAR(500) NOT NULL,
    description TEXT,
    assignee VARCHAR(255),
    
    -- Date and time fields
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Status and priority (already supported)
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
    
    -- NEW: AI-extracted extended fields
    category VARCHAR(100),                    -- action_item, decision, follow_up, etc.
    business_impact ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    dependencies JSON,                        -- Array of dependent task IDs or descriptions
    mentioned_by VARCHAR(255),               -- Who brought up this task
    context TEXT,                            -- Surrounding discussion context
    explicit_level ENUM('direct', 'implied', 'inferred') DEFAULT 'direct',
    
    -- AI metadata fields
    ai_task_id VARCHAR(100),                 -- Original AI-generated task ID
    ai_extracted_at TIMESTAMP,               -- When AI extracted this task
    ai_confidence_score DECIMAL(3,2),        -- AI confidence in extraction (0.00-1.00)
    
    -- Source and tracking
    source_transcript_segment TEXT,          -- Original transcript segment
    extraction_method VARCHAR(50),           -- explicit, implicit, dependency_analysis, etc.
    
    -- Indexes for performance
    INDEX idx_meeting_id (meeting_id),
    INDEX idx_assignee (assignee),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date),
    INDEX idx_priority (priority),
    INDEX idx_category (category),
    INDEX idx_business_impact (business_impact),
    INDEX idx_ai_task_id (ai_task_id),
    INDEX idx_created_at (created_at)
);

-- =====================================================
-- MIGRATION SCRIPT FOR EXISTING DATA
-- =====================================================

-- If you have existing tasks table, use ALTER TABLE instead:
-- (Uncomment and run these one by one if you have existing data)

/*
-- Add new columns to existing tasks table
ALTER TABLE tasks ADD COLUMN category VARCHAR(100);
ALTER TABLE tasks ADD COLUMN business_impact ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium';
ALTER TABLE tasks ADD COLUMN dependencies JSON;
ALTER TABLE tasks ADD COLUMN mentioned_by VARCHAR(255);
ALTER TABLE tasks ADD COLUMN context TEXT;
ALTER TABLE tasks ADD COLUMN explicit_level ENUM('direct', 'implied', 'inferred') DEFAULT 'direct';
ALTER TABLE tasks ADD COLUMN ai_task_id VARCHAR(100);
ALTER TABLE tasks ADD COLUMN ai_extracted_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN ai_confidence_score DECIMAL(3,2);
ALTER TABLE tasks ADD COLUMN source_transcript_segment TEXT;
ALTER TABLE tasks ADD COLUMN extraction_method VARCHAR(50);

-- Add new indexes
CREATE INDEX idx_category ON tasks (category);
CREATE INDEX idx_business_impact ON tasks (business_impact);
CREATE INDEX idx_ai_task_id ON tasks (ai_task_id);

-- Update priority enum to include 'urgent'
ALTER TABLE tasks MODIFY COLUMN priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium';
*/

-- =====================================================
-- TASK DEPENDENCIES TABLE (Alternative to JSON)
-- =====================================================

-- Optional: If you prefer normalized dependencies over JSON
CREATE TABLE IF NOT EXISTS task_dependencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    depends_on_task_id INT,
    depends_on_description VARCHAR(500),
    dependency_type ENUM('blocks', 'requires', 'follows', 'related') DEFAULT 'blocks',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    
    INDEX idx_task_id (task_id),
    INDEX idx_depends_on (depends_on_task_id),
    INDEX idx_dependency_type (dependency_type)
);

-- =====================================================
-- AI EXTRACTION METADATA TABLE
-- =====================================================

-- Track AI extraction sessions and performance
CREATE TABLE IF NOT EXISTS ai_extraction_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    transcript_length INT,
    extraction_method VARCHAR(50),
    
    -- Extraction results
    total_tasks_found INT DEFAULT 0,
    explicit_tasks INT DEFAULT 0,
    implicit_tasks INT DEFAULT 0,
    dependency_relationships INT DEFAULT 0,
    
    -- Performance metrics
    extraction_duration_ms INT,
    ai_model_used VARCHAR(100),
    confidence_threshold DECIMAL(3,2),
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_meeting_id (meeting_id),
    INDEX idx_extraction_method (extraction_method),
    INDEX idx_completed_at (completed_at)
);

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert sample tasks with all new fields
INSERT INTO tasks (
    meeting_id, title, description, assignee, due_date, priority, status,
    category, business_impact, dependencies, mentioned_by, context,
    explicit_level, ai_task_id, ai_extracted_at, ai_confidence_score,
    source_transcript_segment, extraction_method
) VALUES 
(
    'meeting_001',
    'Update documentation',
    'Update the user documentation with new API endpoints',
    'John Smith',
    '2025-09-06',
    'medium',
    'pending',
    'action_item',
    'medium',
    '[]',
    'Sarah Johnson',
    'Discussion about API changes and user experience',
    'direct',
    'task_1',
    '2025-08-30 07:30:00',
    0.95,
    'Sarah: John, can you update the documentation by Friday?',
    'explicit'
),
(
    'meeting_001', 
    'Deploy staging server',
    'Deploy the updated application to staging environment',
    'Mike Wilson',
    '2025-09-05',
    'high',
    'pending',
    'action_item',
    'high',
    '["Update documentation"]',
    'Sarah Johnson',
    'Deployment discussion for testing new features',
    'direct',
    'task_2',
    '2025-08-30 07:30:00',
    0.88,
    'Sarah: Mike, we need staging deployed by Thursday.',
    'explicit'
),
(
    'meeting_001',
    'Test new features',
    'Comprehensive testing of new features after deployment',
    'Lisa Chen',
    NULL,
    'medium',
    'pending',
    'action_item',
    'medium',
    '["Deploy staging server"]',
    'Lisa Chen',
    'Testing strategy discussion',
    'implied',
    'task_3',
    '2025-08-30 07:30:00',
    0.72,
    'Lisa: I can test everything after the deployment.',
    'implicit'
);

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check the new schema
DESCRIBE tasks;

-- Count tasks by category
SELECT category, COUNT(*) as task_count 
FROM tasks 
GROUP BY category;

-- Show tasks with dependencies
SELECT title, assignee, dependencies 
FROM tasks 
WHERE JSON_LENGTH(dependencies) > 0;

-- Show AI extraction confidence
SELECT title, ai_confidence_score, extraction_method
FROM tasks 
ORDER BY ai_confidence_score DESC;

-- =====================================================
-- PERFORMANCE OPTIMIZATION
-- =====================================================

-- Additional indexes for common queries
CREATE INDEX idx_assignee_status ON tasks (assignee, status);
CREATE INDEX idx_due_date_priority ON tasks (due_date, priority);
CREATE INDEX idx_meeting_category ON tasks (meeting_id, category);
CREATE INDEX idx_business_impact_status ON tasks (business_impact, status);

-- =====================================================
-- TIDB-SPECIFIC OPTIMIZATIONS
-- =====================================================

-- For TiDB production, consider these optimizations:
/*
-- Partition by meeting_id for better performance
ALTER TABLE tasks PARTITION BY HASH(meeting_id) PARTITIONS 8;

-- Use TiDB's JSON functions for dependency queries
-- Example: SELECT * FROM tasks WHERE JSON_CONTAINS(dependencies, '"task_1"');

-- Consider using TiDB's HTAP capabilities for analytics
-- CREATE TABLE tasks_analytics AS SELECT * FROM tasks;
*/