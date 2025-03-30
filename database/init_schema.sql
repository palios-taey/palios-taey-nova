-- Basic schema for transcript processing
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    date TIMESTAMP NOT NULL,
    content TEXT NOT NULL,
    processed BOOLEAN DEFAULT 0,
    analysis_complete BOOLEAN DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_transcript_source ON transcripts(source);
CREATE INDEX IF NOT EXISTS idx_transcript_date ON transcripts(date);
CREATE INDEX IF NOT EXISTS idx_transcript_processed ON transcripts(processed);

-- Table for storing extracted patterns
CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER,
    pattern_type TEXT NOT NULL,
    pattern_content TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    FOREIGN KEY(transcript_id) REFERENCES transcripts(id)
);

-- Table for storing agreements
CREATE TABLE IF NOT EXISTS agreements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER,
    agreement_text TEXT NOT NULL,
    parties TEXT NOT NULL,
    date TIMESTAMP NOT NULL,
    FOREIGN KEY(transcript_id) REFERENCES transcripts(id)
);

-- Table for charter elements
CREATE TABLE IF NOT EXISTS charter_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER,
    element_text TEXT NOT NULL,
    category TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    FOREIGN KEY(transcript_id) REFERENCES transcripts(id)
);
