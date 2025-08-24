# src/data/test_song_library_extended.py

import pytest
from datetime import date
from unittest.mock import patch
from src.data import database_manager
from src.data import song_library
from src.services import spotify_service

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

def test_update_song_details(db_connection_extended):
    """Test updating a song's details."""
    song_id = song_library.add_song("Old Title", "Old Artist", 2000, "update.mp3", spotify_id="old_id")

    new_title = "New Title"
    new_artist = "New Artist"
    new_year = 2024
    new_spotify_id = "new_id_456"

    song_library.update_song_details(song_id, new_title, new_artist, new_year, new_spotify_id)

    updated_song = song_library.get_song_by_id(song_id)
    assert updated_song is not None
    assert updated_song[1] == new_title
    assert updated_song[2] == new_artist
    assert updated_song[3] == new_year
    assert updated_song[7] == new_spotify_id

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


# Using patch to mock the spotify_service dependency
@patch('src.data.song_library.spotify_service')
def test_get_album_art_for_song_cached(mock_spotify_service, db_connection_extended):
    """
    Test that album art is returned from the cache if available and that
    the Spotify service is not called.
    """
    fake_art = b'cached_art_data'
    song_id = song_library.add_song("Cached Song", "Art", 2023, "cache.mp3")
    song_library.update_album_art(song_id, fake_art)

    # Act
    result = song_library.get_album_art_for_song(song_id)

    # Assert
    assert result == fake_art
    mock_spotify_service.fetch_album_art_data.assert_not_called()


@patch('src.data.song_library.spotify_service')
def test_get_album_art_for_song_fetch_from_spotify(mock_spotify_service, db_connection_extended):
    """
    Test that album art is fetched from Spotify if not in the cache, and
    is then saved to the cache.
    """
    spotify_id = "spotify_art_id"
    expected_art = b'fetched_art_data'
    mock_spotify_service.fetch_album_art_data.return_value = expected_art

    song_id = song_library.add_song("Fetch Song", "Art", 2023, "fetch.mp3", spotify_id=spotify_id)

    # Act
    result = song_library.get_album_art_for_song(song_id)

    # Assert
    assert result == expected_art
    mock_spotify_service.fetch_album_art_data.assert_called_once_with(spotify_id)

    # Verify that the art was cached
    cached_art = song_library.get_album_art(song_id)
    assert cached_art == expected_art


@patch('src.data.song_library.spotify_service')
def test_get_album_art_for_song_spotify_fails(mock_spotify_service, db_connection_extended):
    """
    Test that None is returned if Spotify fails to find the album art.
    """
    spotify_id = "spotify_fail_id"
    mock_spotify_service.fetch_album_art_data.return_value = None

    song_id = song_library.add_song("Fail Song", "Art", 2023, "fail.mp3", spotify_id=spotify_id)

    # Act
    result = song_library.get_album_art_for_song(song_id)

    # Assert
    assert result is None
    mock_spotify_service.fetch_album_art_data.assert_called_once_with(spotify_id)

    # Verify that the art is still None in the cache
    cached_art = song_library.get_album_art(song_id)
    assert cached_art is None


@patch('src.data.song_library.spotify_service')
def test_get_album_art_for_song_no_spotify_id(mock_spotify_service, db_connection_extended):
    """
    Test that None is returned and Spotify is not called if the song has no
    Spotify ID.
    """
    song_id = song_library.add_song("No ID Song", "Art", 2023, "noid.mp3", spotify_id=None)

    # Act
    result = song_library.get_album_art_for_song(song_id)

    # Assert
    assert result is None
    mock_spotify_service.fetch_album_art_data.assert_not_called()
