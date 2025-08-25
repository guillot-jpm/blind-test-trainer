import random
from src.data import song_library


class QuizSession:
    """
    Manages the state of a single quiz session.
    """

    def __init__(self, song_ids: list[int], mode: str = "Standard"):
        """
        Initializes a new quiz session.

        Args:
            song_ids (list[int]): A list of song IDs for the quiz.
            mode (str): The quiz mode ('Standard' or 'Challenge').
        """
        if not song_ids:
            raise ValueError("Cannot start a quiz with no songs.")

        self.song_ids = song_ids
        random.shuffle(self.song_ids)
        self.total_questions = len(self.song_ids)
        self.current_question_index = 0
        self.score = 0
        self.mode = mode
        self.failed_songs = []

    def get_current_song(self):
        """
        Retrieves the full data for the current song in the quiz.

        Returns:
            dict: The song data as a dictionary, or None if the quiz is over.
        """
        if self.is_finished():
            return None

        song_id = self.song_ids[self.current_question_index]
        # get_song_by_id now returns a dictionary directly.
        song_data = song_library.get_song_by_id(song_id)
        return song_data

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

    def record_result(self, was_correct: bool, song_data: dict = None):
        """
        Records the result of a question and updates the score.

        Args:
            was_correct (bool): True if the user answered correctly.
            song_data (dict, optional): The full data of the song answered.
                                        Required for Gauntlet mode.
        """
        if was_correct:
            self.score += 1
        elif self.mode == "Gauntlet" and song_data:
            self.failed_songs.append(song_data)
