# src/data/migrations.py

"""
This module handles database schema migrations.
Migrations are used to alter the database schema after it has been created,
for example, to add new columns to existing tables.
"""

import sqlite3
import logging

def _add_album_art_blob_to_songs(cursor):
    """
    Adds the 'album_art_blob' column to the 'songs' table if it doesn't exist.

    Args:
        cursor: The database cursor to use for the operation.
    """
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(songs)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'album_art_blob' not in columns:
            cursor.execute("ALTER TABLE songs ADD COLUMN album_art_blob BLOB")
            logging.info("Column 'album_art_blob' added to 'songs' table.")
        else:
            logging.info("Column 'album_art_blob' already exists in 'songs' table.")
    except sqlite3.Error as e:
        logging.error(f"Error adding 'album_art_blob' column to 'songs' table: {e}")
        raise

def run_migrations(connection):
    """
    Runs all pending database migrations.

    Args:
        connection: The database connection object.
    """
    try:
        cursor = connection.cursor()
        _add_album_art_blob_to_songs(cursor)
        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Database migration failed: {e}")
        connection.rollback()
        raise
