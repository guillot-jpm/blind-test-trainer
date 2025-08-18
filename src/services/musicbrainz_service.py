# src/services/musicbrainz_service.py

"""
This service provides an interface for interacting with the MusicBrainz API.
It handles setting the User-Agent, rate limiting, and searching for song
metadata.
"""

import musicbrainzngs
from thefuzz import fuzz

# --- Configuration ---

musicbrainzngs.set_useragent(
    "BlindTestTrainer",
    "0.1.0",
    "https://github.com/your-username/blind-test-trainer"
)

# --- Public Functions ---

def find_best_match(title, artist):
    """
    Finds the best match for a song, prioritizing the first release.
    """
    print(f"Attempting to find first release for '{title}' by '{artist}'...")
    result = _find_match_by_release_group(title, artist)

    if result:
        print("Found match via release group (first release).")
        return result

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
        # Use 'artist' and 'releasegroup' fields for a targeted search
        result = musicbrainzngs.search_release_groups(
            query=f"artist:\"{artist}\" releasegroup:\"{title}\"", limit=5
        )

        if not result['release-group-list']:
            return None

        query_str = f"{title.lower()} {artist.lower()}"
        best_match_rg = max(
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

        # *** FIX 1: Find the correct track instead of grabbing the first one. ***
        best_recording_match = None
        highest_score = -1
        for medium in release_details['release']['medium-list']:
            for track in medium['track-list']:
                recording = track['recording']
                # Compare the track title with the original query title
                score = fuzz.ratio(title.lower(), recording['title'].lower())

                if score > highest_score:
                    highest_score = score
                    best_recording_match = recording
                elif score == highest_score:
                    # Tie-breaker: prefer shorter title.
                    # This check is safe because best_recording_match will not be None.
                    if len(recording['title']) < len(best_recording_match['title']):
                        best_recording_match = recording

        if not best_recording_match:
            return None

        # Add necessary context for formatting
        best_recording_match['artist-credit-phrase'] = release_details['release']['artist-credit-phrase']
        best_recording_match['artist-credit'] = release_details['release']['artist-credit']
        best_recording_match['release-list'] = [earliest_release]

        # Pass all relevant IDs to the formatter
        return _format_recording(
            best_recording_match,
            release_id=earliest_release['id'],
            release_group_id=rg_id
        )

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
            key=lambda r: (
                fuzz.ratio(
                    query_str,
                    f"{r['title'].lower()} {r['artist-credit-phrase'].lower()}"
                ),
                -len(r['title'])  # Tie-breaker: shorter title is better
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

# *** FIX 2: Update formatter to accept and return more specific IDs. ***
def _format_recording(recording, release_id=None, release_group_id=None):
    """
    Formats a MusicBrainz recording object into a simpler dictionary.
    """
    # This now correctly uses the full artist credit phrase
    artist_name = recording.get('artist-credit-phrase', "Unknown Artist")

    release_year = "Unknown Year"
    if 'release-list' in recording and recording['release-list']:
        first_release = recording['release-list'][0]
        if 'date' in first_release and first_release['date']:
            release_year = first_release['date'].split('-')[0]

    # The 'artist-credit' list gives better individual artist names
    primary_artist = "Unknown Artist"
    if 'artist-credit' in recording and recording['artist-credit']:
        primary_artist = recording['artist-credit'][0]['artist']['name']


    return {
        'recording_id': recording['id'],
        'release_id': release_id,
        'release_group_id': release_group_id,
        'title': recording['title'],
        'artist': artist_name, # Returns "Calvin Harris and Dua Lipa"
        'primary_artist': primary_artist, # Returns "Calvin Harris"
        'release_year': release_year,
    }
