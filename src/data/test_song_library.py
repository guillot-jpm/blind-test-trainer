# src/data/test_song_library.py

import pytest
from datetime import date, timedelta
from src.data import database_manager
from src.data import song_library

@pytest.fixture
def db_connection():
    """Fixture to set up and tear down an in-memory database for each test."""
    database_manager.connect(":memory:")
    database_manager.initialize_database()
    yield
    database_manager.disconnect()

def test_add_and_get_song(db_connection):
    """Test adding a song and retrieving it by ID."""
    song_id = song_library.add_song(
        title="Test Song",
        artist="Test Artist",
        release_year=2023,
        local_filename="test.mp3",
        musicbrainz_id="1234-5678"
    )
    assert isinstance(song_id, int)

    song = song_library.get_song_by_id(song_id)
    assert song is not None
    assert song[1] == "Test Song"
    assert song[6] == "test.mp3"

    # Verify that spaced repetition data was created
    cursor = database_manager.get_cursor()
    cursor.execute("SELECT * FROM spaced_repetition WHERE song_id = ?", (song_id,))
    sr_data = cursor.fetchone()
    assert sr_data is not None
    assert sr_data[0] == song_id
    assert sr_data[3] == date.today()

def test_get_all_songs(db_connection):
    """Test retrieving all songs from the library."""
    song_library.add_song("Song 1", "Artist A", 2021, "song1.mp3")
    song_library.add_song("Song 2", "Artist B", 2022, "song2.mp3")

    all_songs = song_library.get_all_songs()
    assert len(all_songs) == 2
    assert all_songs[0][1] == "Song 1"
    assert all_songs[1][1] == "Song 2"

def test_add_duplicate_song_filename(db_connection):
    """Test that adding a song with a duplicate filename raises an error."""
    song_library.add_song("Song 1", "Artist A", 2021, "song1.mp3")
    with pytest.raises(song_library.DuplicateSongError):
        song_library.add_song("Another Song", "Another Artist", 2023, "song1.mp3")

def test_add_duplicate_song_musicbrainz_id(db_connection):
    """Test that adding a song with a duplicate musicbrainz_id raises an error."""
    song_library.add_song("Song 1", "Artist A", 2021, "song1.mp3", "unique-id-1")
    with pytest.raises(song_library.DuplicateSongError):
        song_library.add_song("Song 2", "Artist B", 2022, "song2.mp3", "unique-id-1")

def test_get_nonexistent_song(db_connection):
    """Test that retrieving a non-existent song returns None."""
    song = song_library.get_song_by_id(999)
    assert song is None


def test_get_srs_data(db_connection):
    """Test retrieving SRS data for a song."""
    song_id = song_library.add_song("Test Song", "Test Artist", 2023, "test.mp3")
    srs_data = song_library.get_srs_data(song_id)
    assert srs_data is not None
    assert srs_data[0] == song_id
    assert srs_data[1] == 1  # Default interval
    assert srs_data[2] == 2.5  # Default ease factor
    assert srs_data[3] == date.today()


def test_update_srs_data(db_connection):
    """Test updating SRS data for a song."""
    song_id = song_library.add_song("Test Song", "Test Artist", 2023, "test.mp3")

    new_interval = 5
    new_ease = 2.6
    new_date = date.today()

    song_library.update_srs_data(song_id, new_interval, new_ease, new_date)

    srs_data = song_library.get_srs_data(song_id)
    assert srs_data is not None
    assert srs_data[1] == new_interval
    assert srs_data[2] == new_ease
    assert srs_data[3] == new_date


def test_get_due_songs(db_connection):
    """Test retrieving songs that are due for review."""
    # This song will be due today by default
    song_id1 = song_library.add_song("Due Song", "Artist", 2023, "due.mp3")

    # This song will be set to be due tomorrow
    song_id2 = song_library.add_song("Future Song", "Artist", 2023, "future.mp3")
    tomorrow = date.today() + timedelta(days=1)
    song_library.update_srs_data(song_id2, 1, 2.5, tomorrow)

    # Check that only the first song is due
    due_songs = song_library.get_due_songs()
    assert song_id1 in due_songs
    assert song_id2 not in due_songs

    # Update the second song to be due in the past
    past_date = date.today() - timedelta(days=1)
    song_library.update_srs_data(song_id2, 1, 2.5, past_date)

    # Check that both songs are now due
    due_songs = song_library.get_due_songs()
    assert song_id1 in due_songs
    assert song_id2 in due_songs
