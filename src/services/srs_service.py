# src/services/srs_service.py

"""
This service is responsible for handling the Spaced Repetition System (SRS) logic.
"""

from datetime import date, timedelta
from src.data import song_library

def calculate_next_srs_review(song_id: int, was_correct: bool):
    """
    Calculates the next review date and other SRS parameters for a song.

    NOTE: This is a placeholder implementation. The actual SM-2 algorithm
    will be implemented in a future user story (Epic 5).

    Args:
        song_id (int): The ID of the song being reviewed.
        was_correct (bool): True if the user correctly identified the song.

    Returns:
        tuple: A tuple containing (new_interval, new_ease_factor, next_review_date).
    """
    srs_data = song_library.get_srs_data(song_id)
    if not srs_data:
        # Should not happen for a song in a quiz, but handle gracefully.
        return 1, 2.5, date.today() + timedelta(days=1)

    # Unpack existing data (though we don't use it in this placeholder)
    _, current_interval, ease_factor, _ = srs_data

    if was_correct:
        # For now, just double the interval
        new_interval = (current_interval or 1) * 2
        next_review_date = date.today() + timedelta(days=new_interval)
        # Keep ease factor the same for now
        new_ease_factor = ease_factor
    else:
        # If wrong, reset the interval to 1 day
        new_interval = 1
        next_review_date = date.today() + timedelta(days=1)
        # Keep ease factor the same for now
        new_ease_factor = ease_factor

    return new_interval, new_ease_factor, next_review_date
