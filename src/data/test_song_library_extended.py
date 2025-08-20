# src/data/test_song_library_extended.py

import pytest
from datetime import date
from src.data import database_manager
from src.data import song_library

@pytest.fixture
def db_connection_extended():
    """Fixture to set up and tear down an in-memory database for each test."""
    database_manager.connect(":memory:")
    database_manager.initialize_database()
    yield
    database_manager.disconnect()

def test_get_all_songs_for_view(db_connection_extended):
    """Test retrieving all songs for the detailed library view."""
    song_id = song_library.add_song("View Song", "View Artist", 2023, "view.mp3")

    songs_for_view = song_library.get_all_songs_for_view()

    assert len(songs_for_view) == 1
    song_view = songs_for_view[0]

    assert isinstance(song_view, dict)
    assert song_view['song_id'] == song_id
    assert song_view['title'] == "View Song"
    assert song_view['artist'] == "View Artist"
    assert song_view['release_year'] == 2023
    assert song_view['next_review_date'] == date.today()

def test_update_song_spotify_id(db_connection_extended):
    """Test updating a song's Spotify ID."""
    song_id = song_library.add_song("Update Song", "Update Artist", 2023, "update.mp3", spotify_id="old_id")

    new_id = "new_spotify_id_123"
    song_library.update_song_spotify_id(song_id, new_id)

    updated_song = song_library.get_song_by_id(song_id)
    assert updated_song is not None
    assert updated_song[7] == new_id # spotify_id is the 8th column (index 7)

def test_delete_songs_by_id(db_connection_extended):
    """Test deleting songs by their IDs."""
    song_id1 = song_library.add_song("Delete Song 1", "Del Artist", 2023, "del1.mp3")
    song_id2 = song_library.add_song("Delete Song 2", "Del Artist", 2023, "del2.mp3")

    # Add a dummy play history record for song1
    cursor = database_manager.get_cursor()
    cursor.execute("INSERT INTO play_history (song_id, play_timestamp, was_correct) VALUES (?, ?, ?)",
                   (song_id1, date.today(), True))
    cursor.connection.commit()

    # Ensure everything is there before deletion
    assert song_library.get_song_by_id(song_id1) is not None
    assert song_library.get_srs_data(song_id1) is not None
    cursor.execute("SELECT * FROM play_history WHERE song_id = ?", (song_id1,))
    assert cursor.fetchone() is not None

    # Delete song 1
    song_library.delete_songs_by_id([song_id1])

    # Check that song 1 is gone from all tables
    assert song_library.get_song_by_id(song_id1) is None
    assert song_library.get_srs_data(song_id1) is None
    cursor.execute("SELECT * FROM play_history WHERE song_id = ?", (song_id1,))
    assert cursor.fetchone() is None

    # Check that song 2 is still present
    assert song_library.get_song_by_id(song_id2) is not None
