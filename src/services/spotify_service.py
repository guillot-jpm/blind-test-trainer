# src/services/spotify_service.py

"""
This service provides an interface for interacting with the Spotify API.
It handles authentication, searching for song metadata, and formatting the results.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from thefuzz import fuzz
from configparser import NoSectionError, NoOptionError
import logging
import requests
from src.utils.config_manager import config


class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors."""
    pass


# --- Service Instance ---
# Will be initialized by the main application entry point.
spotify = None

def initialize_spotify_service():
    """
    Initializes the Spotify API client.
    This must be called after the main configuration is loaded.
    """
    global spotify
    try:
        client_id = config.get('Spotify', 'spotify_client_id')
        client_secret = config.get('Spotify', 'spotify_client_secret')

        if not client_id or 'YOUR_CLIENT_ID' in client_id or \
           not client_secret or 'YOUR_CLIENT_SECRET' in client_secret:
            raise SpotifyAPIError("Spotify credentials are not configured. Please edit config.ini.")

        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        logging.info("Spotify service initialized successfully.")

    except (NoSectionError, NoOptionError, SpotifyAPIError) as e:
        logging.error(
            "Failure to connect to the MusicBrainz API, including the error "
            f"reason: {e}"
        )
        spotify = None


# --- Public Functions ---

def search_by_title(title):
    """
    Finds the most popular track matching the given title.
    """
    if not spotify:
        raise SpotifyAPIError("Spotify service is not initialized.")

    try:
        query = f"track:{title}"
        result = spotify.search(q=query, type='track', limit=10) # Get a few options

        if not result['tracks']['items']:
            return None

        # Find the track with the earliest release date
        best_match_track = _get_track_with_earliest_release(result['tracks']['items'])
        return _format_track(best_match_track) if best_match_track else None

    except spotipy.exceptions.SpotifyException as e:
        logging.error(
            "Failure to connect to the MusicBrainz API, including the error "
            f"reason: {e}"
        )
        raise SpotifyAPIError(f"Spotify API search failed: {e}") from e


def search_by_title_and_artist(title, artist):
    """
    Finds the best fuzzy match for a song given a title and artist.
    """
    if not spotify:
        raise SpotifyAPIError("Spotify service is not initialized.")

    try:
        query = f"track:{title} artist:{artist}"
        result = spotify.search(q=query, type='track', limit=5)

        if not result['tracks']['items']:
            return None

        # Find the track with the earliest release date from the results
        best_match_track = _get_track_with_earliest_release(result['tracks']['items'])
        return _format_track(best_match_track) if best_match_track else None

    except spotipy.exceptions.SpotifyException as e:
        logging.error(
            "Failure to connect to the MusicBrainz API, including the error "
            f"reason: {e}"
        )
        raise SpotifyAPIError(f"Spotify API search failed: {e}") from e


def get_track_by_id(track_id):
    """
    Fetches a single track directly by its Spotify ID.
    """
    if not spotify:
        raise SpotifyAPIError("Spotify service is not initialized.")

    try:
        track = spotify.track(track_id)
        if not track:
            return None
        return _format_track(track)
    except spotipy.exceptions.SpotifyException as e:
        logging.error(
            "Failure to connect to the MusicBrainz API, including the error "
            f"reason: {e}"
        )
        # This can happen if the ID is invalid or not found
        raise SpotifyAPIError(f"Failed to get track by ID '{track_id}': {e}") from e


def fetch_album_art_data(spotify_id):
    """
    Given a Spotify track ID, fetches the album art.

    This function prioritizes a 300x300 resolution image if available.
    It downloads the image and returns its binary content.

    Args:
        spotify_id (str): The Spotify ID of the track.

    Returns:
        bytes: The binary content of the image, or None if an error occurs.
    """
    if not spotify:
        raise SpotifyAPIError("Spotify service is not initialized.")

    try:
        track = spotify.track(spotify_id)
        if not track or not track.get('album') or not track['album'].get('images'):
            logging.warning(f"No album art found for Spotify track ID: {spotify_id}")
            return None

        # Prioritize 300x300 image (index 1), fallback to others
        images = track['album']['images']
        image_url = None
        if len(images) > 1:
            image_url = images[1]['url']  # 300x300
        elif len(images) > 0:
            image_url = images[0]['url']  # 640x640
        else:
            logging.warning(f"No image URLs in album data for track ID: {spotify_id}")
            return None

        response = requests.get(image_url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.content

    except spotipy.exceptions.SpotifyException as e:
        logging.error(f"Spotify API error fetching track '{spotify_id}': {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download album art for track ID '{spotify_id}': {e}")
        return None
    except (KeyError, IndexError) as e:
        logging.error(f"Unexpected data structure for track ID '{spotify_id}': {e}")
        return None


# --- Private Helper Functions ---

def _get_track_with_earliest_release(tracks):
    """
    Finds the track with the earliest release date from a list of tracks.
    Handles 'YYYY', 'YYYY-MM-DD', and 'YYYY-MM' date formats.
    """
    if not tracks:
        return None

    earliest_track = None
    # Initialize with a value that ensures the first valid track becomes the earliest
    earliest_date_str = "9999-99-99"

    for track in tracks:
        release_date = track.get('album', {}).get('release_date')

        # Skip tracks without a release date
        if not release_date:
            continue

        # Direct string comparison works for YYYY, YYYY-MM, YYYY-MM-DD
        if release_date < earliest_date_str:
            earliest_date_str = release_date
            earliest_track = track

    return earliest_track


def _format_track(track):
    """
    Formats a Spotify track object into a simpler dictionary.
    """
    artist_name = ', '.join(a['name'] for a in track['artists'])

    release_year = "Unknown Year"
    if track['album'].get('release_date'):
        release_year = track['album']['release_date'].split('-')[0]

    primary_artist = "Unknown Artist"
    if track['artists']:
        primary_artist = track['artists'][0]['name']

    album_art_url = None
    if track.get('album') and track['album'].get('images'):
        images = track['album']['images']
        if len(images) > 1:
            album_art_url = images[1]['url']  # Typically 300x300
        elif len(images) > 0:
            album_art_url = images[0]['url']  # Fallback to largest

    return {
        'spotify_id': track['id'],
        'title': track['name'],
        'artist': artist_name,
        'primary_artist': primary_artist,
        'release_year': release_year,
        'album_art_url': album_art_url,
    }
