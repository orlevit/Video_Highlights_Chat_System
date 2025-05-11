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

-- Insert sample video
INSERT INTO videos (filename, duration) VALUES
('sample_office_visit.mp4', 240.0)
ON CONFLICT DO NOTHING;

-- Insert sample highlights data for testing
INSERT INTO highlights (video_id, timestamp, description, summary, embedding) 
SELECT 
    1, -- video_id (assumes the sample video was inserted with id=1)
    timestamp,
    description,
    summary,
    NULL -- embedding (will be filled by vector embedding process)
FROM (
    VALUES
    (10.5, 'A person gets out of a red car and walks toward the building', 'Person exits a car'),
    (25.7, 'The person enters the building through the glass doors', 'Person enters the building'),
    (40.2, 'Inside, the person speaks with a receptionist at the front desk', 'Person talks to receptionist'),
    (60.4, 'The person is given a visitor badge and directed to the elevator', 'Person receives visitor badge'),
    (80.6, 'The person enters the elevator and presses the button for the 5th floor', 'Person takes elevator to 5th floor'),
    (100.8, 'On the 5th floor, the person walks down a hallway with meeting rooms', 'Person walks through office hallway'),
    (125.9, 'The person enters a meeting room where several people are waiting', 'Person joins meeting'),
    (145.5, 'The person shakes hands with everyone and takes a seat at the table', 'Person greets meeting attendees'),
    (165.3, 'The person opens a laptop and begins presenting a slideshow', 'Person presents slides to the group'),
    (195.2, 'After the presentation, there is a discussion among all attendees', 'Group discusses the presentation')
) AS sample_data(timestamp, description, summary)
ON CONFLICT DO NOTHING;
