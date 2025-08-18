# src/data/test_song_library.py

import pytest
from datetime import date
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
        language="English",
        genre="Pop",
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
    song_library.add_song("Song 1", "Artist A", 2021, "English", "Rock", "song1.mp3")
    song_library.add_song("Song 2", "Artist B", 2022, "Spanish", "Latin", "song2.mp3")

    all_songs = song_library.get_all_songs()
    assert len(all_songs) == 2
    assert all_songs[0][1] == "Song 1"
    assert all_songs[1][1] == "Song 2"

def test_add_duplicate_song_filename(db_connection):
    """Test that adding a song with a duplicate filename raises an error."""
    song_library.add_song("Song 1", "Artist A", 2021, "English", "Rock", "song1.mp3")
    with pytest.raises(song_library.DuplicateSongError):
        song_library.add_song("Another Song", "Another Artist", 2023, "English", "Pop", "song1.mp3")

def test_add_duplicate_song_musicbrainz_id(db_connection):
    """Test that adding a song with a duplicate musicbrainz_id raises an error."""
    song_library.add_song("Song 1", "Artist A", 2021, "English", "Rock", "song1.mp3", "unique-id-1")
    with pytest.raises(song_library.DuplicateSongError):
        song_library.add_song("Song 2", "Artist B", 2022, "Spanish", "Latin", "song2.mp3", "unique-id-1")

def test_get_nonexistent_song(db_connection):
    """Test that retrieving a non-existent song returns None."""
    song = song_library.get_song_by_id(999)
    assert song is None
