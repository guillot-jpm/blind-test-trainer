# src/services/musicbrainz_service.py

"""
This service provides an interface for interacting with the MusicBrainz API.
It handles setting the User-Agent, rate limiting, and searching for song
metadata.
"""

import musicbrainzngs
from thefuzz import fuzz

# --- Configuration ---

# Set a descriptive User-Agent as required by the MusicBrainz API policy.
# This helps them identify the application making requests.
musicbrainzngs.set_useragent(
    "BlindTestTrainer",
    "0.1.0",
    "https://github.com/your-username/blind-test-trainer" # Replace with your actual repo URL
)

# --- Public Functions ---

def find_best_match(title, artist):
    """
    Finds the best match for a song, prioritizing the first release.

    This function first attempts to find the song's original release by
    searching for its release group. If that fails, it falls back to a
    general search for the recording.

    Args:
        title (str): The title of the song to search for.
        artist (str): The artist of the song.

    Returns:
        dict: A dictionary containing the metadata of the best match,
              or None if no suitable match is found.
    """
    print(f"Attempting to find first release for '{title}' by '{artist}'...")
    # 1. First, try the precise method by searching for the release group.
    result = _find_match_by_release_group(title, artist)

    if result:
        print("Found match via release group (first release).")
        return result

    # 2. If the first method fails, fall back to the broader recording search.
    print("Could not find release group. Falling back to recording search...")
    result = _find_match_by_recording(title, artist)

    if result:
        print("Found match via recording search.")
        return result

    print("No suitable match found.")
    return None


# --- Private Helper Functions ---

def _find_match_by_release_group(title, artist):
    """
    Finds a song's first release by searching for its release group.
    """
    try:
        result = musicbrainzngs.search_release_groups(
            query=f"artist:\"{artist}\" releasegroup:\"{title}\"", limit=5
        )

        if not result['release-group-list']:
            return None

        query_str = f"{title.lower()} {artist.lower()}"
        best_match_rg = max(
            result['release-group-list'],
            key=lambda rg: fuzz.ratio(
                query_str,
                f"{rg['title'].lower()} {rg['artist-credit-phrase'].lower()}"
            )
        )

        score = fuzz.ratio(
            query_str,
            f"{best_match_rg['title'].lower()} {best_match_rg['artist-credit-phrase'].lower()}"
        )
        if score < 70:
            return None

        rg_id = best_match_rg['id']
        release_group = musicbrainzngs.get_release_group_by_id(
            rg_id, includes=['releases']
        )

        releases = release_group['release-group']['release-list']
        if not releases:
            return None

        earliest_release = min(
            (r for r in releases if 'date' in r and r['date']),
            key=lambda r: r['date'],
            default=None
        )
        if not earliest_release:
            return None

        release_details = musicbrainzngs.get_release_by_id(
            earliest_release['id'], includes=['recordings', 'artists']
        )

        recording = release_details['release']['medium-list'][0]['track-list'][0]['recording']
        recording['artist-credit'] = release_details['release']['artist-credit']
        recording['release-list'] = [earliest_release]

        return _format_recording(recording)

    except musicbrainzngs.WebServiceError as exc:
        print(f"Error connecting to MusicBrainz: {exc}")
        return None


def _find_match_by_recording(title, artist):
    """
    Finds a song by directly searching for recordings.
    """
    try:
        result = musicbrainzngs.search_recordings(
            query=f"artist:\"{artist}\" recording:\"{title}\"", limit=5
        )

        if not result['recording-list']:
            return None

        query_str = f"{title.lower()} {artist.lower()}"
        best_match = max(
            result['recording-list'],
            key=lambda r: fuzz.ratio(
                query_str,
                f"{r['title'].lower()} {r['artist-credit-phrase'].lower()}"
            )
        )

        score = fuzz.ratio(
            query_str,
            f"{best_match['title'].lower()} {best_match['artist-credit-phrase'].lower()}"
        )
        if score < 70:
            return None

        return _format_recording(best_match)

    except musicbrainzngs.WebServiceError as exc:
        print(f"Error connecting to MusicBrainz: {exc}")
        return None

def _format_recording(recording):
    """
    Formats a MusicBrainz recording object into a simpler dictionary.
    """
    artist_name = "Unknown Artist"
    if 'artist-credit' in recording and recording['artist-credit']:
        artist_name = recording['artist-credit'][0]['artist']['name']

    release_year = "Unknown Year"
    if 'release-list' in recording and recording['release-list']:
        first_release = recording['release-list'][0]
        if 'date' in first_release and first_release['date']:
            release_year = first_release['date'].split('-')[0]

    return {
        'musicbrainz_id': recording['id'],
        'title': recording['title'],
        'artist': artist_name,
        'release_year': release_year,
        'genre': recording.get('genre', 'Unknown Genre'),
        'language': recording.get('language', 'Unknown Language')
    }
