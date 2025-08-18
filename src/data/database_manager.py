# src/data/database_manager.py

"""
This module handles database operations, including initialization
and other database-related tasks.
"""

import sqlite3
from src.data.schema import ALL_TABLES


def initialize_database(db_path):
    """
    Initializes the database by creating all necessary tables
    if they don't already exist.
    """
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
