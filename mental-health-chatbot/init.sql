-- Database initialization script for Mental Health ChatBot

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS mental_health_chatbot;

-- Use the database
\c mental_health_chatbot;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_mood_entries_user_id ON mood_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_mood_entries_created_at ON mood_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_messages_content_fts ON messages USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_mood_entries_notes_fts ON mood_entries USING gin(to_tsvector('english', notes));

-- Create partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_users_active ON users(id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(id) WHERE is_read = false;

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_mood_entries_user_date ON mood_entries(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_session_time ON messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_assessments_user_type ON assessments(user_id, assessment_type);

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON DATABASE mental_health_chatbot TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;