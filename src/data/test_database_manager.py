# src/data/test_database_manager.py

import unittest
import sqlite3
from datetime import date, datetime, timedelta

from src.data import database_manager
from src.data import song_library

class TestDashboardQueries(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary, in-memory database and populate it with test data.
        This method is called before each test function.
        """
        database_manager.connect(':memory:')
        database_manager.initialize_database()

        # Add songs
        song_library.add_song("Song A", "Artist 1", 2000, "a.mp3") # song_id = 1
        song_library.add_song("Song B", "Artist 1", 2001, "b.mp3") # song_id = 2
        song_library.add_song("Song C", "Artist 2", 2002, "c.mp3") # song_id = 3
        song_library.add_song("Song D", "Artist 2", 2003, "d.mp3") # song_id = 4
        song_library.add_song("Song E", "Artist 3", 2004, "e.mp3") # song_id = 5

        cursor = database_manager.get_cursor()

        # Setup SRS data for get_mastery_distribution
        # song 1: Not Yet Learned (interval < 7)
        cursor.execute("UPDATE spaced_repetition SET current_interval_days = 5 WHERE song_id = 1")
        # song 2: Learning (7 <= interval < 30)
        cursor.execute("UPDATE spaced_repetition SET current_interval_days = 10 WHERE song_id = 2")
        # song 3: Learning
        cursor.execute("UPDATE spaced_repetition SET current_interval_days = 29 WHERE song_id = 3")
        # song 4: Mastered (interval >= 30)
        cursor.execute("UPDATE spaced_repetition SET current_interval_days = 35 WHERE song_id = 4")
        # song 5: Not Yet Learned (default)
        cursor.execute("UPDATE spaced_repetition SET current_interval_days = 1 WHERE song_id = 5")

        # Setup play history for get_practice_history and get_problem_songs
        today_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        two_days_ago_str = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

        history_data = [
            # Yesterday: 3 attempts, 2 correct
            (1, yesterday_str, True, 2.5),
            (2, yesterday_str, True, 3.1),
            (3, yesterday_str, False, 4.0),
            # Two days ago: 2 attempts, 1 correct
            (4, two_days_ago_str, True, 1.9),
            (5, two_days_ago_str, False, 5.0),
            # Problem songs data (song 3 is worst, song 5 is second worst)
            (3, today_str, False, 1.0),
            (3, today_str, False, 1.0),
            (3, today_str, True, 1.0), # Song 3: 33% correct
            (5, today_str, False, 1.0), # Song 5: 0% correct (with the one from 2 days ago)
        ]
        cursor.executemany("""
            INSERT INTO play_history (song_id, play_timestamp, was_correct, reaction_time_seconds)
            VALUES (?, ?, ?, ?)
        """, history_data)

        cursor.connection.commit()

    def tearDown(self):
        """
        Disconnect from the in-memory database after each test.
        """
        database_manager.disconnect()

    def test_get_mastery_distribution(self):
        """Test the calculation of mastery distribution."""
        distribution = database_manager.get_mastery_distribution()
        self.assertEqual(distribution['Not Yet Learned'], 2)
        self.assertEqual(distribution['Learning'], 2)
        self.assertEqual(distribution['Mastered'], 1)

    def test_get_practice_history(self):
        """Test the retrieval of daily practice history."""
        # We query for the last 3 days to capture all our test data
        history = database_manager.get_practice_history(days=3)

        yesterday_key = (date.today() - timedelta(days=1)).isoformat()
        two_days_ago_key = (date.today() - timedelta(days=2)).isoformat()

        self.assertIn(yesterday_key, history)
        self.assertEqual(history[yesterday_key]['attempts'], 3)
        self.assertEqual(history[yesterday_key]['correct'], 2)

        self.assertIn(two_days_ago_key, history)
        self.assertEqual(history[two_days_ago_key]['attempts'], 2)
        self.assertEqual(history[two_days_ago_key]['correct'], 1)

    def test_get_problem_songs(self):
        """
        Test the identification of problem songs based on loss streak and success rate.
        """
        cursor = database_manager.get_cursor()
        # Clear existing play history to isolate this test case
        cursor.execute("DELETE FROM play_history")

        # Timestamps to enforce order (W=Correct, L=Wrong)
        # Song A (ID 1): W, L, L, L -> Loss Streak: 3, Success Rate: 25%
        # Song B (ID 2): L, L, L, W -> Loss Streak: 0, Success Rate: 25%
        # Song C (ID 3): L, L       -> Loss Streak: 2, Success Rate: 0%
        # Song D (ID 4): W, L, L    -> Loss Streak: 2, Success Rate: 33%
        history_data = [
            # Song A
            (1, '2023-01-01 10:00:00', True, 1.0),   # W
            (1, '2023-01-01 11:00:00', False, 1.0),  # L
            (1, '2023-01-01 12:00:00', False, 1.0),  # L
            (1, '2023-01-01 13:00:00', False, 1.0),  # L
            # Song B
            (2, '2023-01-01 10:00:00', False, 1.0),  # L
            (2, '2023-01-01 11:00:00', False, 1.0),  # L
            (2, '2023-01-01 12:00:00', False, 1.0),  # L
            (2, '2023-01-01 13:00:00', True, 1.0),   # W
            # Song C
            (3, '2023-01-01 10:00:00', False, 1.0),  # L
            (3, '2023-01-01 11:00:00', False, 1.0),  # L
            # Song D
            (4, '2023-01-01 10:00:00', True, 1.0),   # W
            (4, '2023-01-01 11:00:00', False, 1.0),  # L
            (4, '2023-01-01 12:00:00', False, 1.0),  # L
        ]
        cursor.executemany("""
            INSERT INTO play_history (song_id, play_timestamp, was_correct, reaction_time_seconds)
            VALUES (?, ?, ?, ?)
        """, history_data)
        cursor.connection.commit()

        # We need at least 2 attempts for C, 3 for D, and 4 for A & B
        problem_songs = database_manager.get_problem_songs(limit=4, min_attempts=2)

        self.assertEqual(len(problem_songs), 4)

        # Expected order: A, C, D, B
        # 1. Song A: loss_streak=3, success_rate=0.25
        # 2. Song C: loss_streak=2, success_rate=0.0
        # 3. Song D: loss_streak=2, success_rate=0.333
        # 4. Song B: loss_streak=0, success_rate=0.25

        # Check Song A
        self.assertEqual(problem_songs[0]['song_id'], 1)
        self.assertEqual(problem_songs[0]['loss_streak'], 3)
        self.assertAlmostEqual(problem_songs[0]['success_rate'], 0.25)

        # Check Song C
        self.assertEqual(problem_songs[1]['song_id'], 3)
        self.assertEqual(problem_songs[1]['loss_streak'], 2)
        self.assertAlmostEqual(problem_songs[1]['success_rate'], 0.0)

        # Check Song D
        self.assertEqual(problem_songs[2]['song_id'], 4)
        self.assertEqual(problem_songs[2]['loss_streak'], 2)
        self.assertAlmostEqual(problem_songs[2]['success_rate'], 1.0 / 3.0)

        # Check Song B
        self.assertEqual(problem_songs[3]['song_id'], 2)
        self.assertEqual(problem_songs[3]['loss_streak'], 0)
        self.assertAlmostEqual(problem_songs[3]['success_rate'], 0.25)

    def test_get_mastery_over_time(self):
        """Test the simulation of mastery over time."""
        # This test is complex. We'll simplify the scenario.
        # Let's clear the history and set up a predictable one.
        cursor = database_manager.get_cursor()
        cursor.execute("DELETE FROM play_history")

        # Song 1 will become Mastered tomorrow.
        # Let's assume default ease of 2.5.
        # 1 -> 4 (correct) -> 10 (correct) -> 25 (correct) -> 63 (mastered)
        # This requires 4 correct answers in a row.
        history = [
            # Day -10: first correct answer
            (1, (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'), True, 5.0),
            # Day -5: second correct
            (1, (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'), True, 5.0),
            # Day -2: third correct
            (1, (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), True, 5.0),
             # Day -1: fourth correct -> will push to mastered
            (1, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), True, 5.0),
        ]
        cursor.executemany("""
            INSERT INTO play_history (song_id, play_timestamp, was_correct, reaction_time_seconds)
            VALUES (?, ?, ?, ?)
        """, history)
        cursor.connection.commit()

        mastery_data = database_manager.get_mastery_over_time(days=15)

        yesterday_key = (date.today() - timedelta(days=1)).isoformat()
        two_days_ago_key = (date.today() - timedelta(days=2)).isoformat()

        # On day -2, the song was not yet mastered.
        self.assertEqual(mastery_data[two_days_ago_key], 0)
        # On day -1, the fourth correct answer pushed it to mastered.
        self.assertEqual(mastery_data[yesterday_key], 1)

if __name__ == '__main__':
    unittest.main()
