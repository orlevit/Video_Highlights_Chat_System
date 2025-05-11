-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create videos table if not exists
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    duration FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create highlights table if not exists
CREATE TABLE IF NOT EXISTS highlights (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(id) ON DELETE CASCADE,
    timestamp FLOAT NOT NULL,
    description TEXT NOT NULL,
    summary TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a text search index for efficient searching
CREATE INDEX IF NOT EXISTS highlights_text_search_idx ON highlights USING GIN (
    to_tsvector('english', description || ' ' || summary)
);
