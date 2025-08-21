# src/services/test_file_discovery.py

import os
import pytest
from src.services.file_discovery import find_new_songs

@pytest.fixture
def music_folder(tmp_path):
    """Create a temporary music folder structure for testing."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()

    # Create some dummy files
    (music_dir / "song1.mp3").touch()
    (music_dir / "song2.wav").touch()
    (music_dir / "AlreadyExists.flac").touch()
    (music_dir / "document.txt").touch()

    # Create a subdirectory with more files
    sub_dir = music_dir / "artist_album"
    sub_dir.mkdir()
    (sub_dir / "song3.m4a").touch()
    (sub_dir / "song4.ogg").touch()
    (sub_dir / "cover.jpg").touch()

    return str(music_dir)

def test_find_new_songs_basic(music_folder):
    """Test finding new songs in a directory structure."""
    # song1.mp3, song2.wav, song3.m4a, song4.ogg are new
    # AlreadyExists.flac is already in the database
    existing_filenames = {"alreadyexists.flac"}

    new_songs = find_new_songs(music_folder, existing_filenames)

    # Convert to basenames for easier comparison
    new_song_basenames = {os.path.basename(p) for p in new_songs}

    assert len(new_songs) == 4
    assert "song1.mp3" in new_song_basenames
    assert "song2.wav" in new_song_basenames
    assert "song3.m4a" in new_song_basenames
    assert "song4.ogg" in new_song_basenames

def test_find_new_songs_all_exist(music_folder):
    """Test the case where all songs are already in the database."""
    existing_filenames = {
        "song1.mp3",
        "song2.wav",
        "alreadyexists.flac",
        "song3.m4a",
        "song4.ogg",
    }

    new_songs = find_new_songs(music_folder, existing_filenames)
    assert len(new_songs) == 0

def test_find_new_songs_none_exist(music_folder):
    """Test the case where the database is empty."""
    existing_filenames = set()
    new_songs = find_new_songs(music_folder, existing_filenames)
    assert len(new_songs) == 5

def test_find_new_songs_ignores_non_audio_files(music_folder):
    """Ensure non-audio files are ignored."""
    existing_filenames = set()
    new_songs = find_new_songs(music_folder, existing_filenames)
    new_song_basenames = {os.path.basename(p) for p in new_songs}

    assert "document.txt" not in new_song_basenames
    assert "cover.jpg" not in new_song_basenames

def test_find_new_songs_empty_folder(tmp_path):
    """Test with an empty music folder."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    existing_filenames = {"somefile.mp3"}

    new_songs = find_new_songs(str(empty_dir), existing_filenames)
    assert len(new_songs) == 0

def test_find_new_songs_invalid_path():
    """Test with a path that does not exist."""
    invalid_path = "/path/that/does/not/exist"
    existing_filenames = set()

    new_songs = find_new_songs(invalid_path, existing_filenames)
    assert len(new_songs) == 0

def test_find_new_songs_returns_absolute_paths(music_folder):
    """Verify that the returned paths are absolute."""
    existing_filenames = set()
    new_songs = find_new_songs(music_folder, existing_filenames)

    # Check if at least one song is found and if its path is absolute
    assert len(new_songs) > 0
    for path in new_songs:
        assert os.path.isabs(path)
