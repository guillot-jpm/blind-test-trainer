# src/services/musicbrainz_service.py

"""
This service provides an interface for interacting with the MusicBrainz API.
It handles setting the User-Agent, rate limiting, and searching for song
metadata.
"""

import musicbrainzngs
from thefuzz import fuzz


class MusicBrainzAPIError(Exception):
    """Custom exception for MusicBrainz API errors."""
    pass


# --- Configuration ---

musicbrainzngs.set_useragent(
    "BlindTestTrainer",
    "0.1.0",
    "https://github.com/your-username/blind-test-trainer"
)

# --- Public Functions ---

def find_best_match(title, artist):
    """
    Finds the best match for a song by searching for its release group.
    """
    print(f"Attempting to find release group for '{title}' by '{artist}'...")
    result = _find_match_by_release_group(title, artist)

    if result:
        print("Found match via release group.")
        return result

    print("No suitable match found.")
    return None


# --- Private Helper Functions ---

def _find_match_by_release_group(title, artist):
    """
    Finds a song's release group.
    """
    try:
        # Use 'artist' and 'releasegroup' fields for a targeted search
        result = musicbrainzngs.search_release_groups(
            query=f"artist:\"{artist}\" releasegroup:\"{title}\"", limit=5
        )

        if not result['release-group-list']:
            return None

        query_str = f"{title.lower()} {artist.lower()}"
        best_match = max(
            result['release-group-list'],
            key=lambda rg: (
                fuzz.ratio(
                    query_str,
                    f"{rg['title'].lower()} {rg['artist-credit-phrase'].lower()}"
                ),
                -len(rg['title'])  # Tie-breaker: shorter title is better
            )
        )

        score = fuzz.ratio(
            query_str,
            f"{best_match['title'].lower()} {best_match['artist-credit-phrase'].lower()}"
        )
        if score < 70:
            return None

        return _format_release_group(best_match)

    except musicbrainzngs.WebServiceError as exc:
        print(f"Error connecting to MusicBrainz: {exc}")
        raise MusicBrainzAPIError(
            "Could not connect to MusicBrainz. Please check your internet connection and try again."
        ) from exc

def _format_release_group(release_group):
    """
    Formats a MusicBrainz release group object into a simpler dictionary.
    """
    artist_name = release_group.get('artist-credit-phrase', "Unknown Artist")

    release_year = "Unknown Year"
    if release_group.get('first-release-date'):
        release_year = release_group['first-release-date'].split('-')[0]

    primary_artist = "Unknown Artist"
    if release_group.get('artist-credit'):
        primary_artist = release_group['artist-credit'][0]['artist']['name']

    return {
        'release_group_id': release_group['id'],
        'title': release_group['title'],
        'artist': artist_name,
        'primary_artist': primary_artist,
        'release_year': release_year,
    }
