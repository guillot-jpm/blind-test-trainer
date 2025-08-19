import random
from src.data import song_library


class QuizSession:
    """
    Manages the state of a single quiz session.
    """

    def __init__(self, song_ids: list[int]):
        """
        Initializes a new quiz session.

        Args:
            song_ids (list[int]): A list of song IDs to be included in the quiz.
        """
        if not song_ids:
            raise ValueError("Cannot start a quiz with no songs.")

        self.song_ids = song_ids
        random.shuffle(self.song_ids)
        self.total_questions = len(self.song_ids)
        self.current_question_index = 0
        self.score = 0

    def get_current_song(self):
        """
        Retrieves the full data for the current song in the quiz.

        Returns:
            dict: The song data as a dictionary, or None if the quiz is over.
        """
        if self.is_finished():
            return None

        song_id = self.song_ids[self.current_question_index]
        song_data = song_library.get_song_by_id(song_id)

        # DEBUG: Print the raw tuple from the database
        print(f"DEBUG: song_data tuple from DB: {song_data}")

        # Convert tuple to a more usable dictionary
        if song_data:
            return {
                "song_id": song_data[0],
                "title": song_data[1],
                "artist": song_data[2],
                "release_year": song_data[3],
                "language": song_data[4],
                "genre": song_data[5],
                "local_filename": song_data[6],
                "spotify_id": song_data[7],
            }
        return None

    def get_session_progress(self) -> (int, int):
        """
        Gets the current progress of the quiz.

        Returns:
            tuple: A tuple containing (current_question_number, total_questions).
        """
        return self.current_question_index + 1, self.total_questions

    def next_song(self):
        """
        Advances the quiz to the next song.
        """
        if not self.is_finished():
            self.current_question_index += 1

    def is_finished(self) -> bool:
        """
        Checks if the quiz has ended.

        Returns:
            bool: True if all questions have been presented, False otherwise.
        """
        return self.current_question_index >= self.total_questions
