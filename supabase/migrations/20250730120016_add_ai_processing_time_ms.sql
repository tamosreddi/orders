-- Add ai_processing_time_ms column to messages table
-- This column tracks how long AI processing took for each message

-- Add the new column safely (allows NULL for existing records)
ALTER TABLE messages 
ADD COLUMN ai_processing_time_ms INTEGER DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN messages.ai_processing_time_ms IS 'AI processing time in milliseconds for performance monitoring';

-- Create index for performance monitoring queries
CREATE INDEX idx_messages_ai_processing_time ON messages(ai_processing_time_ms) 
WHERE ai_processing_time_ms IS NOT NULL;