# src/data/schema.py

"""
This module defines the database schema for the application.
It includes SQL statements to create the necessary tables and
a function to initialize the database.
"""

import os
import sqlite3
from src.utils.config_manager import config

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
    musicbrainz_id TEXT UNIQUE
);
"""

# A list of all table creation statements
ALL_TABLES = [
    CREATE_SONGS_TABLE
]


def initialize_database():
    """
    Initializes the database by creating all necessary tables
    if they don't already exist.
    """
    db_path = config.get('Paths', 'database_file')

    # Ensure the directory for the database file exists.
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for table_query in ALL_TABLES:
            cursor.execute(table_query)
        conn.commit()
    except sqlite3.Error as e:
        # In a real application, this should be logged properly.
        print(f"Database error while initializing: {e}")
    finally:
        if conn:
            conn.close()
