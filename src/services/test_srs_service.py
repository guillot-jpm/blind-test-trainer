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

    @patch('src.services.srs_service.date')
    def test_subsequent_correct_review_with_speed_bonus(self, mock_date):
        """
        Test a subsequent correct review with a fast reaction time, applying the speed bonus.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        srs_data = (1, 10, 2.5, date(2022, 12, 22))  # 10-day interval, 2.5 ease

        # Act
        # base_new_interval = round(10 * 2.5) = 25
        # reaction_time is < 3.0, so apply 1.2x bonus
        # interval_with_bonus = 25 * 1.2 = 30.0
        # final_interval = round(30.0) = 30
        interval, ease, next_review = srs_service._calculate_srs_for_correct_answer(srs_data, reaction_time=2.5)

        # Assert
        self.assertEqual(interval, 30)
        self.assertEqual(ease, 2.5, "Ease factor should not change")
        self.assertEqual(next_review, date(2023, 1, 31), "Next review date should be today + 30 days")

    @patch('src.services.srs_service.date')
    def test_subsequent_correct_review_with_bonus_and_rounding(self, mock_date):
        """
        Test a case where the speed bonus results in a float that needs rounding.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        srs_data = (1, 5, 2.3, date(2022, 12, 27))  # 5-day interval, 2.3 ease

        # Act
        # base_new_interval = round(5 * 2.3) = round(11.5) = 12
        # reaction_time is < 3.0, so apply 1.2x bonus
        # interval_with_bonus = 12 * 1.2 = 14.4
        # final_interval = round(14.4) = 14
        interval, ease, next_review = srs_service._calculate_srs_for_correct_answer(srs_data, reaction_time=1.8)

        # Assert
        self.assertEqual(interval, 14)
        self.assertEqual(ease, 2.3, "Ease factor should not change")
        self.assertEqual(next_review, date(2023, 1, 15), "Next review date should be today + 14 days")

    @patch('src.services.srs_service.date')
    def test_timeout_reaction_time(self, mock_date):
        """
        Test that a reaction time of -1 (timeout) does not receive a speed bonus.
        """
        # Arrange
        mock_date.today.return_value = date(2023, 1, 1)
        srs_data = (1, 10, 2.5, date(2022, 12, 22))

        # Act
        # base_new_interval = round(10 * 2.5) = 25
        # reaction_time is -1, so no bonus
        # final_interval = round(25) = 25
        interval, ease, next_review = srs_service._calculate_srs_for_correct_answer(srs_data, reaction_time=-1.0)

        # Assert
        self.assertEqual(interval, 25)
        self.assertEqual(ease, 2.5, "Ease factor should not change")
        self.assertEqual(next_review, date(2023, 1, 26), "Next review date should be today + 25 days")
