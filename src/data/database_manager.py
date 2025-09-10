# src/data/database_manager.py

"""
This module handles the connection to the SQLite database, ensuring that
a single, consistent connection is used throughout the application.
"""

import sqlite3
import datetime
import logging
from datetime import date, timedelta
from src.data.schema import ALL_TABLES
from src.data.migrations import run_migrations

# This will hold the single, application-wide database connection.
_connection = None


def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 string."""
    return val.isoformat()


def convert_date(val):
    """Convert ISO 8601 string to datetime.date object."""
    return datetime.date.fromisoformat(val.decode())


def connect(db_path):
    """
    Establishes a connection to the SQLite database.

    This function should be called once when the application starts.
    It handles connection errors gracefully by printing an error and
    ensuring the internal connection state is clean.
    """
    global _connection
    if _connection is not None:
        # Avoid creating a new connection if one already exists.
        return

    try:
        # Register the adapter and converter for date objects
        sqlite3.register_adapter(datetime.date, adapt_date_iso)
        sqlite3.register_converter("date", convert_date)

        # Using check_same_thread=False is a common practice for SQLite in
        # multi-threaded applications, like those with a separate GUI thread.
        # The `detect_types` flag allows using the registered converters.
        _connection = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
    except sqlite3.Error as e:
        # In a real application, this should be logged to a file or a
        # dedicated logging service.
        logging.error(f"Database connection error: {e}")
        _connection = None  # Ensure connection is reset on failure.
        raise  # Re-raise the exception to be handled by the caller.


def disconnect():
    """
    Closes the database connection if it's currently open.

    This function should be called when the application is shutting down
    to ensure a clean exit.
    """
    global _connection
    if _connection:
        _connection.close()
        _connection = None


def get_cursor():
    """
    Returns a cursor from the current database connection.

    Raises:
        RuntimeError: If the database connection has not been established
                      by calling `connect()` first.
    """
    if _connection is None:
        raise RuntimeError(
            "Database connection is not established. Call connect() first."
        )
    return _connection.cursor()


def initialize_database():
    """
    Initializes the database by creating all necessary tables if they
    don't already exist.

    This function relies on an existing database connection, so `connect()`
    must be called before this function is invoked.
    """
    try:
        cursor = get_cursor()
        for table_query in ALL_TABLES:
            cursor.execute(table_query)
        _connection.commit()

        # After creating tables, run any pending migrations.
        run_migrations(_connection)
    except (sqlite3.Error, RuntimeError) as e:
        # This will catch both SQL errors and errors from get_cursor()
        # if the connection isn't open.
        logging.error(f"Database initialization error: {e}")
        raise # Re-raise to let the caller know initialization failed.


def record_play_history(song_id, was_correct, reaction_time):
    """
    Records the outcome of a single play instance in the play_history table.

    Args:
        song_id (int): The ID of the song that was played.
        was_correct (bool): Whether the user's guess was correct.
        reaction_time (float): The time in seconds it took the user to react.
    """
    try:
        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO play_history (song_id, play_timestamp, was_correct, reaction_time_seconds)
            VALUES (?, datetime('now'), ?, ?)
        """, (song_id, was_correct, reaction_time))
        cursor.connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Failed to record play history: {e}")
        # Depending on the application's needs, you might want to rollback,
        # but for a single INSERT, it's less critical.
        cursor.connection.rollback()
        raise


def get_total_song_count():
    """
    Retrieves the total number of songs in the library.

    Returns:
        int: The total count of songs, or 0 if an error occurs.
    """
    try:
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) FROM songs")
        # fetchone() will return a tuple, e.g., (15,)
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        logging.error(f"Failed to get total song count: {e}")
        return 0


def get_all_release_years():
    """
    Fetches all non-null release years from the songs table.

    Returns:
        list[int]: A list of release years. Returns an empty list on error.
    """
    try:
        cursor = get_cursor()
        cursor.execute("SELECT release_year FROM songs WHERE release_year IS NOT NULL")
        # fetchall() returns a list of tuples, e.g., [(1990,), (2004,)]
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Failed to get release years: {e}")
        return []


def get_all_srs_intervals():
    """
    Fetches all current SRS interval days from the spaced_repetition table.

    Returns:
        list[int]: A list of interval days. Returns an empty list on error.
    """
    try:
        cursor = get_cursor()
        cursor.execute("SELECT current_interval_days FROM spaced_repetition")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Failed to get SRS intervals: {e}")
        return []


def get_mastery_distribution():
    """
    Calculates the distribution of songs across mastery levels.

    The levels are defined as:
    - Not Yet Learned: SRS interval < 7 days
    - Learning: SRS interval >= 7 and < 30 days
    - Mastered: SRS interval >= 30 days

    Returns:
        dict: A dictionary mapping mastery levels to the count of songs,
              e.g., {'Not Yet Learned': 10, 'Learning': 20, 'Mastered': 5}.
              Returns a dictionary with zero counts on error.
    """
    # Initialize with default values to ensure all keys are present
    distribution = {
        "Not Yet Learned": 0,
        "Learning": 0,
        "Mastered": 0
    }
    try:
        cursor = get_cursor()
        cursor.execute("""
            SELECT
                CASE
                    WHEN current_interval_days < 7 THEN 'Not Yet Learned'
                    WHEN current_interval_days >= 7 AND current_interval_days < 30 THEN 'Learning'
                    ELSE 'Mastered'
                END as mastery_level,
                COUNT(song_id)
            FROM spaced_repetition
            GROUP BY mastery_level
        """)
        rows = cursor.fetchall()
        # The query returns a list of tuples, e.g., [('Learning', 20), ('Mastered', 5)]
        # We update our dictionary with these results.
        for row in rows:
            distribution[row[0]] = row[1]
        return distribution
    except sqlite3.Error as e:
        logging.error(f"Failed to get mastery distribution: {e}")
        # Return the default dictionary in case of an error
        return distribution


def get_practice_history(days=30):
    """
    Retrieves the practice history over a given number of days.

    Args:
        days (int): The number of past days to retrieve history for.

    Returns:
        dict: A dictionary where keys are date strings ('YYYY-MM-DD') and
              values are dicts {'attempts': int, 'correct': int}.
              Returns an empty dictionary on error.
    """
    history = {}
    try:
        cursor = get_cursor()
        # Note: Using DATE() function on play_timestamp to group by day.
        # The '||' is the standard SQL concatenation operator.
        cursor.execute("""
            SELECT
                DATE(play_timestamp) as play_date,
                COUNT(*) as attempts,
                SUM(was_correct) as correct
            FROM play_history
            WHERE play_timestamp >= date('now', '-' || ? || ' days')
            GROUP BY play_date
            ORDER BY play_date
        """, (str(days),)) # Parameter must be a string for concatenation

        rows = cursor.fetchall()
        for row in rows:
            play_date, attempts, correct = row
            # `correct` will be None if no `was_correct` rows were True for that day.
            history[play_date] = {'attempts': attempts, 'correct': correct or 0}
        return history
    except sqlite3.Error as e:
        logging.error(f"Failed to get practice history: {e}")
        return {}


def get_problem_songs(limit: int, min_attempts: int = 3):
    """
    Identifies "problem songs" based on recent loss streaks and overall success rate.

    A "loss streak" is the number of consecutive incorrect answers since the
    most recent correct answer. If a song has never been answered correctly,
    the streak is its total number of plays.

    Args:
        limit (int): The maximum number of problem songs to return.
        min_attempts (int): The minimum number of plays a song must have
                            to be considered.

    Returns:
        list: An ordered list of dictionaries, where each dictionary contains
              'song_id', 'title', 'artist', 'loss_streak', 'success_rate',
              and 'attempts'. The list is sorted primarily by the highest
              loss_streak, and secondarily by the lowest success_rate.
              Returns an empty list on error.
    """
    problem_songs = []
    try:
        cursor = get_cursor()
        # This query uses a Common Table Expression (CTE) with a window function
        # to calculate the loss streak for each song.
        query = """
            WITH SongLossStreaks AS (
                -- Part 1: Using a window function for songs with at least one correct answer
                WITH RankedPlays AS (
                    SELECT
                        song_id,
                        was_correct,
                        ROW_NUMBER() OVER(PARTITION BY song_id ORDER BY play_timestamp DESC) as rn
                    FROM play_history
                )
                SELECT
                    song_id,
                    MIN(rn) - 1 as loss_streak
                FROM RankedPlays
                WHERE was_correct = 1
                GROUP BY song_id

                UNION ALL

                -- Part 2: Handling songs that have never been answered correctly
                SELECT
                    song_id,
                    COUNT(*) as loss_streak
                FROM play_history
                GROUP BY song_id
                HAVING SUM(was_correct) = 0
            )
            SELECT
                s.song_id,
                s.title,
                s.artist,
                sls.loss_streak,
                SUM(ph.was_correct) * 1.0 / COUNT(ph.history_id) as success_rate,
                COUNT(ph.history_id) as attempts
            FROM
                play_history ph
            JOIN
                songs s ON ph.song_id = s.song_id
            JOIN
                SongLossStreaks sls ON ph.song_id = sls.song_id
            GROUP BY
                s.song_id, s.title, s.artist, sls.loss_streak
            HAVING
                COUNT(ph.history_id) >= ?
            ORDER BY
                sls.loss_streak DESC,
                success_rate ASC
            LIMIT ?
        """

        cursor.execute(query, (min_attempts, limit))

        rows = cursor.fetchall()
        # Get column names from the cursor description for easy dict conversion
        column_names = [description[0] for description in cursor.description]
        for row in rows:
            problem_songs.append(dict(zip(column_names, row)))

        return problem_songs
    except sqlite3.Error as e:
        logging.error(f"Failed to get problem songs: {e}")
        return []


# Note: The following function is complex due to the need to simulate SRS changes over time.
# Helper functions are defined first.

def _get_all_song_ids():
    """Fetches all song IDs from the database."""
    try:
        cursor = get_cursor()
        cursor.execute("SELECT song_id FROM songs")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Failed to get all song IDs: {e}")
        return []

def _get_all_play_history():
    """Fetches all play history, ordered by timestamp."""
    try:
        cursor = get_cursor()
        # The play_timestamp needs to be converted to a date object for comparison
        cursor.execute("""
            SELECT song_id, DATE(play_timestamp), was_correct, reaction_time_seconds
            FROM play_history ORDER BY play_timestamp
        """)
        rows = cursor.fetchall()
        # Convert date strings to date objects for correct comparison later
        return [(row[0], date.fromisoformat(row[1]), row[2], row[3]) for row in rows]
    except sqlite3.Error as e:
        logging.error(f"Failed to get all play history: {e}")
        return []

def _recalculate_srs_for_correct_answer(current_interval, ease_factor, reaction_time):
    """Simulates SRS calculation for a correct answer."""
    if current_interval == 1:
        new_interval = 4
    else:
        base_new_interval = round(current_interval * ease_factor)
        if 0 < reaction_time < 3.0:
            interval_with_bonus = base_new_interval * 1.2
        else:
            interval_with_bonus = float(base_new_interval)
        new_interval = round(interval_with_bonus)
    return new_interval, ease_factor # Ease factor doesn't change

def _recalculate_srs_for_wrong_answer(ease_factor):
    """Simulates SRS calculation for a wrong answer."""
    new_interval = 1
    new_ease_factor = max(1.3, ease_factor - 0.2)
    return new_interval, new_ease_factor


def get_mastery_over_time(days=30):
    """
    Reconstructs the daily count of 'Mastered' songs over the last N days.

    This is an estimation based on a simulation of the SRS algorithm over
    the entire play history of all songs. It is computationally intensive.

    Args:
        days (int): The number of past days to reconstruct history for.

    Returns:
        dict: A dictionary mapping date strings ('YYYY-MM-DD') to the
              estimated count of mastered songs on that day.
    """
    # 1. Setup date range and initial data structures
    today = date.today()
    date_range = [today - timedelta(days=i) for i in range(days)]
    date_range.reverse() # Process from oldest to newest

    mastery_over_time = {dt.isoformat(): 0 for dt in date_range}

    # 2. Fetch all necessary data in bulk
    all_song_ids = _get_all_song_ids()
    if not all_song_ids:
        return mastery_over_time # Return zeroed dict if no songs

    all_history = _get_all_play_history()

    # 3. Initialize SRS state for all songs
    # We assume all songs start with the default SRS values.
    srs_states = {
        song_id: {'interval': 1, 'ease': 2.5}
        for song_id in all_song_ids
    }

    # 4. Simulate history chronologically
    history_idx = 0
    for report_date in date_range:
        # Process all history events up to and including the report_date
        while history_idx < len(all_history) and all_history[history_idx][1] <= report_date:
            song_id, _, was_correct, reaction_time = all_history[history_idx]

            state = srs_states.get(song_id)
            if state:
                if was_correct:
                    new_interval, new_ease = _recalculate_srs_for_correct_answer(
                        state['interval'], state['ease'], reaction_time
                    )
                else:
                    new_interval, new_ease = _recalculate_srs_for_wrong_answer(state['ease'])

                srs_states[song_id]['interval'] = new_interval
                srs_states[song_id]['ease'] = new_ease

            history_idx += 1

        # After processing up to the report date, count mastered songs
        mastered_count = 0
        for song_id in all_song_ids:
            if srs_states[song_id]['interval'] >= 30:
                mastered_count += 1

        mastery_over_time[report_date.isoformat()] = mastered_count

    return mastery_over_time
