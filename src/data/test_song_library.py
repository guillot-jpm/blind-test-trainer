# src/data/test_song_library.py

import unittest
import sqlite3
from datetime import date
from src.data import database_manager
from src.data import song_library

class TestSongLibrary(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database for testing."""
        # Connect to an in-memory database
        database_manager.connect(":memory:")
        # Initialize the database schema
        database_manager.initialize_database()

    def tearDown(self):
        """Disconnect from the database after tests."""
        database_manager.disconnect()

    def test_add_and_get_song(self):
        """Test adding a song and retrieving it by ID."""
        song_id = song_library.add_song(
            title="Test Song",
            artist="Test Artist",
            release_year=2023,
            language="English",
            genre="Pop",
            local_filename="test.mp3",
            musicbrainz_id="1234-5678"
        )
        self.assertIsInstance(song_id, int)

        song = song_library.get_song_by_id(song_id)
        self.assertIsNotNone(song)
        self.assertEqual(song[1], "Test Song")
        self.assertEqual(song[6], "test.mp3")

        # Verify that spaced repetition data was created
        cursor = database_manager.get_cursor()
        cursor.execute("SELECT * FROM spaced_repetition WHERE song_id = ?", (song_id,))
        sr_data = cursor.fetchone()
        self.assertIsNotNone(sr_data)
        self.assertEqual(sr_data[0], song_id)
        self.assertEqual(sr_data[3], date.today())


    def test_get_all_songs(self):
        """Test retrieving all songs from the library."""
        song_library.add_song("Song 1", "Artist A", 2021, "English", "Rock", "song1.mp3")
        song_library.add_song("Song 2", "Artist B", 2022, "Spanish", "Latin", "song2.mp3")

        all_songs = song_library.get_all_songs()
        self.assertEqual(len(all_songs), 2)
        self.assertEqual(all_songs[0][1], "Song 1")
        self.assertEqual(all_songs[1][1], "Song 2")

    def test_add_duplicate_song_filename(self):
        """Test that adding a song with a duplicate filename raises an error."""
        song_library.add_song("Song 1", "Artist A", 2021, "English", "Rock", "song1.mp3")
        with self.assertRaises(song_library.DuplicateSongError):
            song_library.add_song("Another Song", "Another Artist", 2023, "English", "Pop", "song1.mp3")

    def test_add_duplicate_song_musicbrainz_id(self):
        """Test that adding a song with a duplicate musicbrainz_id raises an error."""
        song_library.add_song("Song 1", "Artist A", 2021, "English", "Rock", "song1.mp3", "unique-id-1")
        with self.assertRaises(song_library.DuplicateSongError):
            song_library.add_song("Song 2", "Artist B", 2022, "Spanish", "Latin", "song2.mp3", "unique-id-1")

    def test_get_nonexistent_song(self):
        """Test that retrieving a non-existent song returns None."""
        song = song_library.get_song_by_id(999)
        self.assertIsNone(song)

if __name__ == '__main__':
    unittest.main()
