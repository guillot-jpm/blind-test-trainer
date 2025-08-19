# src/services/test_spotify_service.py

"""
Unit tests for the Spotify service.
"""

import unittest
from unittest.mock import patch
import importlib
from configparser import NoSectionError

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

    @patch('spotipy.Spotify')
    @patch('src.utils.config_manager.config')
    def test_find_best_match_success(self, mock_config, mock_spotify_class):
        """
        Tests the successful path where a suitable track is found.
        """
        mock_config.get.side_effect = lambda section, option: {
            ('Spotify', 'spotify_client_id'): 'test_id',
            ('Spotify', 'spotify_client_secret'): 'test_secret',
        }[(section, option)]

        mock_spotify_instance = mock_spotify_class.return_value
        mock_spotify_instance.search.return_value = self.mock_spotify_search_result

        from src.services import spotify_service
        importlib.reload(spotify_service)

        result = spotify_service.find_best_match("Despacito", "Luis Fonsi")
        self.assertIsNotNone(result)
        self.assertEqual(result['spotify_id'], 'track-id-1')

    @patch('spotipy.Spotify')
    @patch('src.utils.config_manager.config')
    def test_find_best_match_not_found(self, mock_config, mock_spotify_class):
        """
        Tests the case where the Spotify API returns no tracks.
        """
        mock_config.get.side_effect = lambda section, option: {
            ('Spotify', 'spotify_client_id'): 'test_id',
            ('Spotify', 'spotify_client_secret'): 'test_secret',
        }[(section, option)]

        mock_spotify_instance = mock_spotify_class.return_value
        mock_spotify_instance.search.return_value = {'tracks': {'items': []}}

        from src.services import spotify_service
        importlib.reload(spotify_service)

        result = spotify_service.find_best_match("Unknown Song", "Unknown Artist")
        self.assertIsNone(result)

    @patch('spotipy.Spotify')
    @patch('src.utils.config_manager.config')
    def test_find_best_match_api_error(self, mock_config, mock_spotify_class):
        """
        Tests that a SpotifyException is caught and re-raised as SpotifyAPIError.
        """
        mock_config.get.side_effect = lambda section, option: {
            ('Spotify', 'spotify_client_id'): 'test_id',
            ('Spotify', 'spotify_client_secret'): 'test_secret',
        }[(section, option)]

        from spotipy.exceptions import SpotifyException
        mock_spotify_instance = mock_spotify_class.return_value
        mock_spotify_instance.search.side_effect = SpotifyException(401, -1, "Unauthorized")

        from src.services import spotify_service
        importlib.reload(spotify_service)

        with self.assertRaises(spotify_service.SpotifyAPIError):
            spotify_service.find_best_match("Any Song", "Any Artist")

    @patch('src.utils.config_manager.config')
    def test_initialization_no_credentials(self, mock_config):
        """
        Tests that the service handles missing credentials gracefully.
        """
        mock_config.get.side_effect = NoSectionError('Spotify')

        from src.services import spotify_service
        importlib.reload(spotify_service)

        self.assertIsNone(spotify_service.spotify)
        with self.assertRaisesRegex(spotify_service.SpotifyAPIError, "Spotify service is not initialized"):
            spotify_service.find_best_match("Any", "Any")

if __name__ == '__main__':
    unittest.main()
