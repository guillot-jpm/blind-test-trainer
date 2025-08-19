import unittest
from unittest.mock import patch
from datetime import date

# This allows running the test from the root directory, e.g., using 'python -m unittest discover'
from src.services import srs_service

class TestSrsServiceCorrectAnswer(unittest.TestCase):
    """
    Unit tests for the SRS calculation logic for correct answers.
    Focuses on the internal helper function `_calculate_srs_for_correct_answer`.
    """

    @patch('src.services.srs_service.date')
    def test_first_correct_review(self, mock_date):
        """
        Test the calculation for the very first correct review of a song.
        The interval should be a fixed 4 days, regardless of reaction time.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        # srs_data tuple: (song_id, current_interval_days, ease_factor, next_review_date)
        srs_data = (1, 1, 2.5, date(2023, 1, 1))

        # Act: Test with a fast reaction time (should not affect the result)
        interval, ease, next_review = srs_service._calculate_srs_for_correct_answer(srs_data, reaction_time=1.5)

        # Assert
        self.assertEqual(interval, 4, "Interval should be 4 for the first correct review")
        self.assertEqual(ease, 2.5, "Ease factor should not change")
        self.assertEqual(next_review, date(2023, 1, 5), "Next review date should be today + 4 days")

        # Act: Test with a slow reaction time (should not affect the result)
        interval, ease, next_review = srs_service._calculate_srs_for_correct_answer(srs_data, reaction_time=5.0)

        # Assert
        self.assertEqual(interval, 4, "Interval should still be 4, even with slow reaction")
        self.assertEqual(ease, 2.5, "Ease factor should not change")
        self.assertEqual(next_review, date(2023, 1, 5), "Next review date should be today + 4 days")

    @patch('src.services.srs_service.date')
    def test_subsequent_correct_review_no_bonus(self, mock_date):
        """
        Test a subsequent correct review with a reaction time too slow for a bonus.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        srs_data = (1, 10, 2.5, date(2022, 12, 22))  # 10-day interval, 2.5 ease

        # Act
        # base_new_interval = round(10 * 2.5) = 25
        # reaction_time is > 3.0, so no bonus
        # final_interval = round(25) = 25
        interval, ease, next_review = srs_service._calculate_srs_for_correct_answer(srs_data, reaction_time=4.0)

        # Assert
        self.assertEqual(interval, 25)
        self.assertEqual(ease, 2.5, "Ease factor should not change")
        self.assertEqual(next_review, date(2023, 1, 26), "Next review date should be today + 25 days")


class TestSrsServiceWrongAnswer(unittest.TestCase):
    """
    Unit tests for the SRS calculation logic for wrong answers.
    Focuses on the internal helper function `_calculate_srs_for_wrong_answer`.
    """

    @patch('src.services.srs_service.date')
    def test_wrong_answer_resets_interval_and_reduces_ease(self, mock_date):
        """
        Test that a wrong answer resets the interval to 1 and reduces the ease factor.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        # srs_data tuple: (song_id, current_interval_days, ease_factor, next_review_date)
        srs_data = (1, 10, 2.5, date(2022, 12, 22))

        # Act
        interval, ease, next_review = srs_service._calculate_srs_for_wrong_answer(srs_data)

        # Assert
        self.assertEqual(interval, 1, "Interval should be reset to 1")
        self.assertAlmostEqual(ease, 2.3, "Ease factor should be reduced by 0.2")
        self.assertEqual(next_review, date(2023, 1, 2), "Next review date should be tomorrow")

    @patch('src.services.srs_service.date')
    def test_wrong_answer_clamps_ease_factor(self, mock_date):
        """
        Test that the ease factor does not drop below the minimum value of 1.3.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        # srs_data with an ease factor that will drop to the clamp value
        srs_data = (1, 10, 1.45, date(2022, 12, 22))

        # Act
        interval, ease, next_review = srs_service._calculate_srs_for_wrong_answer(srs_data)

        # Assert
        self.assertEqual(interval, 1)
        self.assertAlmostEqual(ease, 1.3, "Ease factor should be clamped at 1.3")
        self.assertEqual(next_review, date(2023, 1, 2))

    @patch('src.services.srs_service.date')
    def test_wrong_answer_with_ease_factor_already_below_clamp(self, mock_date):
        """
        Test that if the ease factor is already below 1.3, it is set to 1.3.
        This is a defensive test for data consistency.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        # srs_data with an ease factor already below the clamp
        srs_data = (1, 10, 1.2, date(2022, 12, 22))

        # Act
        interval, ease, next_review = srs_service._calculate_srs_for_wrong_answer(srs_data)

        # Assert
        self.assertEqual(interval, 1)
        self.assertAlmostEqual(ease, 1.3, "Ease factor should be raised to the clamp value of 1.3")
        self.assertEqual(next_review, date(2023, 1, 2))


class TestSrsServiceUpdateOrchestration(unittest.TestCase):
    """
    Tests the main service function `update_srs_data_for_song`.
    This ensures that the full orchestration of fetching, calculating, and updating
    works as expected.
    """

    @patch('src.services.srs_service.song_library')
    @patch('src.services.srs_service.date')
    def test_update_flow_for_correct_answer(self, mock_date, mock_song_library):
        """
        Verify that a correct answer fetches data, calculates new values, and calls the update function.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        song_id = 1
        # srs_data tuple: (song_id, current_interval_days, ease_factor, next_review_date)
        initial_srs_data = (song_id, 10, 2.5, date(2022, 12, 22))
        mock_song_library.get_srs_data.return_value = initial_srs_data

        # Expected calculated values
        # base_new_interval = round(10 * 2.5) = 25
        # reaction_time is < 3.0, so bonus is applied: 25 * 1.2 = 30
        # final_interval = round(30) = 30
        expected_new_interval = 30
        expected_new_ease = 2.5  # Unchanged
        expected_next_review = date(2023, 1, 31) # today + 30 days

        # Act
        srs_service.update_srs_data_for_song(song_id, was_correct=True, reaction_time=2.0)

        # Assert
        # Verify that the initial data was fetched
        mock_song_library.get_srs_data.assert_called_once_with(song_id)
        # Verify that the new data was persisted
        mock_song_library.update_srs_data.assert_called_once_with(
            song_id,
            expected_new_interval,
            expected_new_ease,
            expected_next_review
        )

    @patch('src.services.srs_service.song_library')
    @patch('src.services.srs_service.date')
    def test_update_flow_for_wrong_answer(self, mock_date, mock_song_library):
        """
        Verify that a wrong answer fetches data, calculates new values, and calls the update function.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        song_id = 2
        # srs_data tuple: (song_id, current_interval_days, ease_factor, next_review_date)
        initial_srs_data = (song_id, 10, 2.5, date(2022, 12, 22))
        mock_song_library.get_srs_data.return_value = initial_srs_data

        # Expected calculated values
        expected_new_interval = 1
        expected_new_ease = 2.3
        expected_next_review = date(2023, 1, 2) # tomorrow

        # Act
        # reaction_time is irrelevant for a wrong answer
        srs_service.update_srs_data_for_song(song_id, was_correct=False, reaction_time=-1)

        # Assert
        # Verify that the initial data was fetched
        mock_song_library.get_srs_data.assert_called_once_with(song_id)
        # Verify that the new data was persisted
        mock_song_library.update_srs_data.assert_called_once_with(
            song_id,
            expected_new_interval,
            expected_new_ease,
            expected_next_review
        )

    @patch('src.services.srs_service.song_library')
    def test_no_update_if_song_has_no_srs_data(self, mock_song_library):
        """
        Verify that the update function is not called if no initial SRS data is found.
        """
        # Arrange
        song_id = 99
        mock_song_library.get_srs_data.return_value = None

        # Act
        srs_service.update_srs_data_for_song(song_id, was_correct=True, reaction_time=2.0)

        # Assert
        mock_song_library.get_srs_data.assert_called_once_with(song_id)
        # Crucially, assert that the update function was *not* called
        mock_song_library.update_srs_data.assert_not_called()
