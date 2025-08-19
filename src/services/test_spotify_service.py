# src/services/test_spotify_service.py

"""
Unit tests for the Spotify service.
"""

import unittest
from unittest.mock import patch
from configparser import NoSectionError
from src.services import spotify_service

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
    def test_find_best_match_success(self, mock_spotify_client):
        """
        Tests the successful path where a suitable track is found.
        """
        # Ensure the client is mocked for this test
        spotify_service.spotify = mock_spotify_client
        mock_spotify_client.search.return_value = self.mock_spotify_search_result

        result = spotify_service.find_best_match("Despacito", "Luis Fonsi")

        self.assertIsNotNone(result)
        self.assertEqual(result['spotify_id'], 'track-id-1')
        mock_spotify_client.search.assert_called_once()

    def test_find_best_match_service_not_initialized(self):
        """
        Tests that an error is raised if the service is not initialized.
        """
        spotify_service.spotify = None
        with self.assertRaisesRegex(spotify_service.SpotifyAPIError, "Spotify service is not initialized"):
            spotify_service.find_best_match("Any", "Any")

    @patch('src.services.spotify_service.spotify')
    def test_find_best_match_not_found(self, mock_spotify_client):
        """
        Tests the case where the Spotify API returns no tracks.
        """
        spotify_service.spotify = mock_spotify_client
        mock_spotify_client.search.return_value = {'tracks': {'items': []}}

        result = spotify_service.find_best_match("Unknown Song", "Unknown Artist")
        self.assertIsNone(result)

    @patch('src.services.spotify_service.spotify')
    def test_find_best_match_api_error(self, mock_spotify_client):
        """
        Tests that a SpotifyException is caught and re-raised as SpotifyAPIError.
        """
        spotify_service.spotify = mock_spotify_client
        from spotipy.exceptions import SpotifyException
        mock_spotify_client.search.side_effect = SpotifyException(401, -1, "Unauthorized")

        with self.assertRaises(spotify_service.SpotifyAPIError):
            spotify_service.find_best_match("Any Song", "Any Artist")

if __name__ == '__main__':
    unittest.main()
