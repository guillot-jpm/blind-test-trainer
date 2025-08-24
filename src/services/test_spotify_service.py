# src/services/test_spotify_service.py

"""
Unit tests for the Spotify service.
"""

import unittest
from unittest.mock import patch, Mock
from configparser import NoSectionError
from src.services import spotify_service
import requests

class TestSpotifyService(unittest.TestCase):
    """
    Test suite for the Spotify service.
    """

    # --- Mock for API Data ---
    mock_spotify_search_result = {
        'tracks': {
            'items': [
                {
                    'id': 'track-id-1',
                    'name': 'Despacito',
                    'artists': [{'name': 'Luis Fonsi'}, {'name': 'Daddy Yankee'}],
                    'album': {'release_date': '2017-01-13'},
                    'popularity': 80,
                    'explicit': False
                }
            ]
        }
    }

    @patch('src.services.spotify_service.spotipy.Spotify')
    @patch('src.services.spotify_service.config')
    def test_initialization_success(self, mock_config, mock_spotify_class):
        """
        Tests that the service initializes correctly with valid credentials.
        """
        mock_config.get.side_effect = lambda section, option: {
            ('Spotify', 'spotify_client_id'): 'test_id',
            ('Spotify', 'spotify_client_secret'): 'test_secret',
        }[(section, option)]

        spotify_service.initialize_spotify_service()
        self.assertIsNotNone(spotify_service.spotify)
        mock_spotify_class.assert_called_once()

    @patch('src.services.spotify_service.config')
    def test_initialization_failure(self, mock_config):
        """
        Tests that the service remains uninitialized if credentials are bad.
        """
        mock_config.get.side_effect = NoSectionError('Spotify')
        spotify_service.initialize_spotify_service()
        self.assertIsNone(spotify_service.spotify)

    @patch('src.services.spotify_service.spotify')
    def test_search_by_title_success(self, mock_spotify_client):
        """Tests finding a song by title, selecting the most popular one."""
        spotify_service.spotify = mock_spotify_client
        mock_spotify_client.search.return_value = {
            'tracks': {
                'items': [
                    {'name': 'Test Song', 'popularity': 50, 'id': 'less-popular', 'artists': [{'name': 'Artist A'}], 'album': {'release_date': '2020'}},
                    {'name': 'Test Song', 'popularity': 80, 'id': 'more-popular', 'artists': [{'name': 'Artist B'}], 'album': {'release_date': '2021'}},
                ]
            }
        }
        result = spotify_service.search_by_title("Test Song")
        self.assertIsNotNone(result)
        self.assertEqual(result['spotify_id'], 'more-popular')

    @patch('src.services.spotify_service.spotify')
    def test_search_by_title_and_artist_success(self, mock_spotify_client):
        """Tests the successful path for finding a song by title and artist."""
        spotify_service.spotify = mock_spotify_client
        mock_spotify_client.search.return_value = self.mock_spotify_search_result
        result = spotify_service.search_by_title_and_artist("Despacito", "Luis Fonsi")
        self.assertIsNotNone(result)
        self.assertEqual(result['spotify_id'], 'track-id-1')
        mock_spotify_client.search.assert_called_once()

    @patch('src.services.spotify_service.spotify')
    def test_get_track_by_id_success(self, mock_spotify_client):
        """Tests fetching a track directly by its ID."""
        spotify_service.spotify = mock_spotify_client
        # The track method returns a single item, not a search result list
        mock_track = self.mock_spotify_search_result['tracks']['items'][0]
        mock_spotify_client.track.return_value = mock_track

        result = spotify_service.get_track_by_id('track-id-1')
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Despacito')
        mock_spotify_client.track.assert_called_with('track-id-1')

    def test_search_service_not_initialized(self):
        """Tests that an error is raised if the service is not initialized."""
        spotify_service.spotify = None
        with self.assertRaisesRegex(spotify_service.SpotifyAPIError, "Spotify service is not initialized"):
            spotify_service.search_by_title("Any")
        with self.assertRaisesRegex(spotify_service.SpotifyAPIError, "Spotify service is not initialized"):
            spotify_service.search_by_title_and_artist("Any", "Any")
        with self.assertRaisesRegex(spotify_service.SpotifyAPIError, "Spotify service is not initialized"):
            spotify_service.get_track_by_id("any-id")
        with self.assertRaisesRegex(spotify_service.SpotifyAPIError, "Spotify service is not initialized"):
            spotify_service.fetch_album_art_data("any-id")

    @patch('requests.get')
    @patch('src.services.spotify_service.spotify')
    def test_fetch_album_art_success(self, mock_spotify_client, mock_requests_get):
        """Tests the successful fetching and downloading of album art."""
        spotify_service.spotify = mock_spotify_client
        mock_spotify_client.track.return_value = {
            'album': {
                'images': [
                    {'url': 'http://example.com/large.jpg', 'height': 640, 'width': 640},
                    {'url': 'http://example.com/medium.jpg', 'height': 300, 'width': 300},
                    {'url': 'http://example.com/small.jpg', 'height': 64, 'width': 64}
                ]
            }
        }

        # Mock the download response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'image_data'
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        result = spotify_service.fetch_album_art_data('some-id')

        self.assertEqual(result, b'image_data')
        mock_spotify_client.track.assert_called_with('some-id')
        mock_requests_get.assert_called_with('http://example.com/medium.jpg', timeout=10)

    @patch('src.services.spotify_service.spotify')
    def test_fetch_album_art_no_images(self, mock_spotify_client):
        """Tests that None is returned when a track has no album images."""
        spotify_service.spotify = mock_spotify_client
        mock_spotify_client.track.return_value = {'album': {'images': []}}
        result = spotify_service.fetch_album_art_data('some-id')
        self.assertIsNone(result)

    @patch('requests.get')
    @patch('src.services.spotify_service.spotify')
    def test_fetch_album_art_download_error(self, mock_spotify_client, mock_requests_get):
        """Tests that None is returned if downloading the image fails."""
        spotify_service.spotify = mock_spotify_client
        mock_spotify_client.track.return_value = {
            'album': {'images': [{'url': 'http://example.com/image.jpg'}]}
        }
        mock_requests_get.side_effect = requests.exceptions.RequestException("Connection error")
        result = spotify_service.fetch_album_art_data('some-id')
        self.assertIsNone(result)

    @patch('src.services.spotify_service.spotify')
    def test_search_api_error(self, mock_spotify_client):
        """Tests that a SpotifyException is caught and re-raised as SpotifyAPIError."""
        spotify_service.spotify = mock_spotify_client
        from spotipy.exceptions import SpotifyException
        mock_spotify_client.search.side_effect = SpotifyException(401, -1, "Unauthorized")
        mock_spotify_client.track.side_effect = SpotifyException(401, -1, "Unauthorized")

        with self.assertRaises(spotify_service.SpotifyAPIError):
            spotify_service.search_by_title("Any Song")
        with self.assertRaises(spotify_service.SpotifyAPIError):
            spotify_service.search_by_title_and_artist("Any Song", "Any Artist")
        with self.assertRaises(spotify_service.SpotifyAPIError):
            spotify_service.get_track_by_id("any-id")

        # For fetch_album_art_data, it should return None, not raise an error
        result = spotify_service.fetch_album_art_data("any-id")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
