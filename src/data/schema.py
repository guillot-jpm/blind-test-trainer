# src/data/schema.py

"""
This module defines the database schema for the application.
It includes SQL statements to create the necessary tables and
a function to initialize the database.
"""

# SQL statement to create the 'songs' table
CREATE_SONGS_TABLE = """
CREATE TABLE IF NOT EXISTS songs (
    song_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    release_year INTEGER,
    language TEXT,
    genre TEXT,
    local_filename TEXT NOT NULL UNIQUE,
    spotify_id TEXT UNIQUE
);
"""

# SQL statement to create the 'play_history' table
CREATE_PLAY_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS play_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER,
    play_timestamp DATETIME NOT NULL,
    was_correct BOOLEAN NOT NULL,
    reaction_time_seconds REAL,
    FOREIGN KEY(song_id) REFERENCES songs(song_id)
);
"""

# SQL statement to create the 'spaced_repetition' table
CREATE_SPACED_REPETITION_TABLE = """
CREATE TABLE IF NOT EXISTS spaced_repetition (
    song_id INTEGER PRIMARY KEY,
    current_interval_days INTEGER NOT NULL DEFAULT 1,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    next_review_date DATE NOT NULL,
    FOREIGN KEY(song_id) REFERENCES songs(song_id)
);
"""

# A list of all table creation statements
ALL_TABLES = [
    CREATE_SONGS_TABLE,
    CREATE_PLAY_HISTORY_TABLE,
    CREATE_SPACED_REPETITION_TABLE
]
