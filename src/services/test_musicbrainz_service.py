# src/services/test_musicbrainz_service.py

"""
Unit tests for the MusicBrainz service.
"""

import unittest
from unittest.mock import patch
from src.services.musicbrainz_service import find_best_match

class TestMusicBrainzService(unittest.TestCase):
    """
    Test suite for the MusicBrainz service.
    """

    @patch('musicbrainzngs.search_recordings')
    def test_find_best_match_success(self, mock_search):
        """
        Tests that find_best_match returns the correct recording
        when the API finds results.
        """
        # --- Mock API Response ---
        mock_search.return_value = {
            'recording-list': [
                {
                    'id': 'rec-id-1',
                    'title': 'Bohemian Rhapsody',
                    'artist-credit-phrase': 'Queen',
                    'artist-credit': [{'artist': {'name': 'Queen'}}],
                    'release-list': [{'date': '1975-10-31'}]
                },
                {
                    'id': 'rec-id-2',
                    'title': 'Bohemian Crapsody', # Intentional typo for testing fuzz
                    'artist-credit-phrase': 'Queene',
                    'artist-credit': [{'artist': {'name': 'Queene'}}],
                    'release-list': [{'date': '1976-01-01'}]
                }
            ]
        }

        # --- Call the function ---
        result = find_best_match("Bohemian Rhapsody", "Queen")

        # --- Assertions ---
        self.assertIsNotNone(result)
        self.assertEqual(result['musicbrainz_id'], 'rec-id-1')
        self.assertEqual(result['title'], 'Bohemian Rhapsody')
        self.assertEqual(result['artist'], 'Queen')
        self.assertEqual(result['release_year'], '1975')

    @patch('musicbrainzngs.search_recordings')
    def test_find_best_match_no_results(self, mock_search):
        """
        Tests that find_best_match returns None when the API finds no results.
        """
        # --- Mock API Response ---
        mock_search.return_value = {'recording-list': []}

        # --- Call the function ---
        result = find_best_match("Non Existent Song", "No Such Artist")

        # --- Assertions ---
        self.assertIsNone(result)

    @patch('musicbrainzngs.search_recordings')
    def test_find_best_match_low_score(self, mock_search):
        """
        Tests that find_best_match returns None when the best match
        has a similarity score below the threshold.
        """
        # --- Mock API Response ---
        mock_search.return_value = {
            'recording-list': [
                {
                    'id': 'rec-id-3',
                    'title': 'A Completely Different Song',
                    'artist-credit-phrase': 'Another Artist',
                    'artist-credit': [{'artist': {'name': 'Another Artist'}}],
                    'release-list': [{'date': '2000-01-01'}]
                }
            ]
        }

        # --- Call the function ---
        result = find_best_match("My Song", "My Artist")

        # --- Assertions ---
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
