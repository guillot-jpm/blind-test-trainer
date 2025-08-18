# src/services/test_musicbrainz_service.py

"""
Unit tests for the MusicBrainz service.
"""

import unittest
from unittest.mock import patch
import musicbrainzngs
from src.services.musicbrainz_service import find_best_match, MusicBrainzAPIError

class TestMusicBrainzService(unittest.TestCase):
    """
    Test suite for the MusicBrainz service.
    """

    # --- Mock for API Data ---
    mock_release_group_search = {
        'release-group-list': [{
            'id': 'rg-id-1',
            'title': 'One Kiss',
            'artist-credit-phrase': 'Calvin Harris and Dua Lipa',
            'artist-credit': [{'artist': {'name': 'Calvin Harris'}}],
            'first-release-date': '2018-04-06',
            'score': 100
        }]
    }

    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_success(self, mock_search_rg):
        """
        Tests the successful path using a release group search.
        """
        # --- Setup Mock ---
        mock_search_rg.return_value = self.mock_release_group_search

        # --- Call the function ---
        result = find_best_match("One Kiss", "Calvin Harris and Dua Lipa")

        # --- Assertions ---
        self.assertIsNotNone(result)
        self.assertEqual(result['release_group_id'], 'rg-id-1')
        self.assertEqual(result['title'], 'One Kiss')
        self.assertEqual(result['artist'], 'Calvin Harris and Dua Lipa')
        self.assertEqual(result['primary_artist'], 'Calvin Harris')
        self.assertEqual(result['release_year'], '2018')

    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_not_found(self, mock_search_rg):
        """
        Tests the failure path where no release group is found.
        """
        # --- Setup Mock ---
        mock_search_rg.return_value = {'release-group-list': []}

        # --- Call the function ---
        result = find_best_match("Unknown Song", "Unknown Artist")

        # --- Assertions ---
        self.assertIsNone(result)

    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_api_error(self, mock_search_rg):
        """
        Tests that a WebServiceError is caught and re-raised as MusicBrainzAPIError.
        """
        # --- Setup Mock to raise an error ---
        mock_search_rg.side_effect = musicbrainzngs.WebServiceError("Service unavailable")

        # --- Call the function and assert exception ---
        with self.assertRaises(MusicBrainzAPIError) as context:
            find_best_match("Any Song", "Any Artist")

        self.assertIn(
            "Could not connect to MusicBrainz",
            str(context.exception)
        )

if __name__ == '__main__':
    unittest.main()
