# src/services/spotify_service.py

"""
This service provides an interface for interacting with the Spotify API.
It handles authentication, searching for song metadata, and formatting the results.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from thefuzz import fuzz
from configparser import NoSectionError, NoOptionError
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
        print("Spotify service initialized successfully.")

    except (NoSectionError, NoOptionError, SpotifyAPIError) as e:
        print(f"Spotify service could not be initialized: {e}")
        spotify = None


# --- Public Functions ---

def find_best_match(title, artist):
    """
    Finds the best match for a song by searching on Spotify.
    """
    if not spotify:
        raise SpotifyAPIError("Spotify service is not initialized. Check credentials in config.ini.")

    print(f"Attempting to find track for '{title}' by '{artist}' on Spotify...")

    try:
        query = f"track:{title} artist:{artist}"
        result = spotify.search(q=query, type='track', limit=5)

        if not result['tracks']['items']:
            print("No tracks found on Spotify.")
            return None

        query_str = f"{title.lower()} {artist.lower()}"

        def get_track_artist_str(track):
            return ', '.join(a['name'] for a in track['artists'])

        best_match_track = max(
            result['tracks']['items'],
            key=lambda track: (
                fuzz.ratio(
                    query_str,
                    f"{track['name'].lower()} {get_track_artist_str(track).lower()}"
                ),
                # Tie-breaker: prefer tracks that are not explicit
                track.get('explicit', False) == False,
                # Tie-breaker: prefer tracks with higher popularity
                track.get('popularity', 0)
            )
        )

        score = fuzz.ratio(
            query_str,
            f"{best_match_track['name'].lower()} {get_track_artist_str(best_match_track).lower()}"
        )

        if score < 70:
            print(f"No suitable match found. Best match '{best_match_track['name']}' had score {score}.")
            return None

        print(f"Found best match: '{best_match_track['name']}' by {get_track_artist_str(best_match_track)}")
        return _format_track(best_match_track)

    except spotipy.exceptions.SpotifyException as e:
        print(f"Error connecting to Spotify: {e}")
        raise SpotifyAPIError(
            "Could not connect to Spotify. Please check your internet connection and credentials."
        ) from e


# --- Private Helper Functions ---

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

    return {
        'spotify_id': track['id'],
        'title': track['name'],
        'artist': artist_name,
        'primary_artist': primary_artist,
        'release_year': release_year,
    }
