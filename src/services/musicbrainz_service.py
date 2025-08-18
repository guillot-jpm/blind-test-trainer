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
    Searches for a song on MusicBrainz and returns the best match.

    Args:
        title (str): The title of the song to search for.
        artist (str): The artist of the song.

    Returns:
        dict: A dictionary containing the metadata of the best match,
              or None if no suitable match is found.
    """
    try:
        # The query includes the artist and title for a more precise search.
        # We limit the results to the top 5 to reduce processing time and
        # API load.
        result = musicbrainzngs.search_recordings(
            query=f"artist:\"{artist}\" recording:\"{title}\"",
            limit=5
        )

        if not result['recording-list']:
            return None

        # Use "thefuzz" to find the best match from the results.
        # We create a combined string for comparison to improve accuracy.
        query_str = f"{title.lower()} {artist.lower()}"

        best_match = None
        highest_score = 0

        for recording in result['recording-list']:
            # Extract artist name from the recording data.
            # MusicBrainz returns a list of artists.
            api_artist = recording['artist-credit-phrase']
            api_title = recording['title']

            # Create a combined string from the API result.
            api_str = f"{api_title.lower()} {api_artist.lower()}"

            # Calculate the similarity score.
            score = fuzz.ratio(query_str, api_str)

            # If the new score is higher, update the best match.
            if score > highest_score:
                highest_score = score
                best_match = recording

        # If the best score is below a certain threshold, we consider it
        # a poor match.
        if highest_score < 70: # Threshold can be adjusted
            return None

        # Format the result into a more usable dictionary.
        return _format_recording(best_match)

    except musicbrainzngs.WebServiceError as exc:
        print(f"Error connecting to MusicBrainz: {exc}")
        return None


# --- Private Helper Functions ---

def _format_recording(recording):
    """
    Formats a MusicBrainz recording object into a simpler dictionary.

    Args:
        recording (dict): The recording object from the MusicBrainz API.

    Returns:
        dict: A dictionary containing the desired song metadata.
    """
    # Extract the primary artist's name.
    artist_name = "Unknown Artist"
    if 'artist-credit' in recording and recording['artist-credit']:
        artist_name = recording['artist-credit'][0]['artist']['name']

    # Extract the release year.
    release_year = "Unknown Year"
    if 'release-list' in recording and recording['release-list']:
        # Releases are sorted by date, so the first one is the earliest.
        first_release = recording['release-list'][0]
        if 'date' in first_release and first_release['date']:
            # Extract the year part from the date string (e.g., "YYYY-MM-DD").
            release_year = first_release['date'].split('-')[0]

    return {
        'musicbrainz_id': recording['id'],
        'title': recording['title'],
        'artist': artist_name,
        'release_year': release_year,
        'genre': recording.get('genre', 'Unknown Genre'),
        'language': recording.get('language', 'Unknown Language')
    }
