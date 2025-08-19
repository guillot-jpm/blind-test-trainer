# src/services/srs_service.py

"""
This service is responsible for handling the Spaced Repetition System (SRS) logic.
"""

from datetime import date, timedelta
from src.data import song_library


def _calculate_srs_for_correct_answer(srs_data: tuple, reaction_time: float):
    """
    Calculates the next SRS parameters for a correctly identified song.

    Args:
        srs_data (tuple): The current SRS data for the song from the database.
                          Expected format: (song_id, current_interval_days, ease_factor, next_review_date)
        reaction_time (float): The user's reaction time in seconds.

    Returns:
        tuple: A tuple containing (new_interval, new_ease_factor, next_review_date).
    """
    _, current_interval_days, ease_factor, _ = srs_data

    # Calculate the new interval based on the rules
    if current_interval_days == 1:
        # First correct review: the new interval is a fixed value of 4 days.
        # The speed bonus is not applied in this case.
        final_new_interval_days = 4
    else:
        # Subsequent correct reviews:
        # 1. Calculate the base new interval.
        base_new_interval = round(current_interval_days * ease_factor)

        # 2. Apply a speed bonus if applicable.
        # A reaction time of <= 0 (e.g., -1 for timeout) does not get a bonus.
        if 0 < reaction_time < 3.0:
            interval_with_bonus = base_new_interval * 1.2
        else:
            interval_with_bonus = float(base_new_interval)

        # 3. The final result must be an integer.
        final_new_interval_days = round(interval_with_bonus)

    # The ease factor is not changed when the answer is correct.
    new_ease_factor = ease_factor

    # The next review date is calculated from today.
    next_review_date = date.today() + timedelta(days=final_new_interval_days)

    return final_new_interval_days, new_ease_factor, next_review_date


def _calculate_srs_for_wrong_answer(srs_data: tuple):
    """
    Calculates the next SRS parameters for a song the user failed to identify.

    Args:
        srs_data (tuple): The current SRS data for the song from the database.
                          Expected format: (song_id, current_interval_days, ease_factor, next_review_date)

    Returns:
        tuple: A tuple containing (new_interval_days, new_ease_factor, next_review_date).
    """
    _, _, ease_factor, _ = srs_data

    # Reset the interval to 1 day.
    new_interval_days = 1

    # Reduce the ease factor, with a minimum clamp.
    new_ease_factor = max(1.3, ease_factor - 0.2)

    # The next review is tomorrow.
    next_review_date = date.today() + timedelta(days=1)

    return new_interval_days, new_ease_factor, next_review_date


def update_srs_data_for_song(song_id: int, was_correct: bool, reaction_time: float):
    """
    Updates the SRS data for a song based on the user's answer in a quiz.

    This function orchestrates the entire process:
    1. Fetches the current SRS data.
    2. Calculates the new SRS parameters based on the answer.
    3. Persists the new data to the database.

    Args:
        song_id (int): The ID of the song being reviewed.
        was_correct (bool): True if the user correctly identified the song.
        reaction_time (float): The user's reaction time in seconds. A value of -1
                             indicates a timeout.
    """
    srs_data = song_library.get_srs_data(song_id)
    if not srs_data:
        # This case should ideally not be reached for a song that's part of a quiz.
        # If it does, we can't proceed with an update. Log or handle error as needed.
        print(f"Warning: No SRS data found for song_id {song_id}. Cannot update.")
        return

    if was_correct:
        new_interval, new_ease_factor, next_review_date = _calculate_srs_for_correct_answer(srs_data, reaction_time)
    else:
        new_interval, new_ease_factor, next_review_date = _calculate_srs_for_wrong_answer(srs_data)

    song_library.update_srs_data(song_id, new_interval, new_ease_factor, next_review_date)
