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

    # --- Mocks for API Data ---
    mock_release_group_search = {
        'release-group-list': [{
            'id': 'rg-id-1', 'title': 'One Kiss',
            'artist-credit-phrase': 'Calvin Harris and Dua Lipa', 'score': 100
        }]
    }
    mock_release_group_details = {
        'release-group': {'release-list': [{'id': 'release-id-1', 'date': '2018-04-06'}]}
    }
    mock_release_details = {
        'release': {
            'id': 'release-id-1',
            'artist-credit': [{'artist': {'name': 'Calvin Harris'}}, {'artist': {'name': 'Dua Lipa'}}],
            'artist-credit-phrase': 'Calvin Harris and Dua Lipa',
            'medium-list': [{
                'track-list': [
                    {'recording': {'id': 'rec-id-wrong', 'title': 'Some Other Song'}},
                    {'recording': {'id': 'rec-id-correct', 'title': 'One Kiss'}},
                    {'recording': {'id': 'rec-id-remix', 'title': 'One Kiss (Remix)'}},
                ]
            }]
        }
    }
    mock_recording_search = {
        'recording-list': [{
            'id': 'rec-id-fallback', 'title': 'One Kiss (Fallback)',
            'artist-credit-phrase': 'Calvin Harris and Dua Lipa',
            'artist-credit': [{'artist': {'name': 'Calvin Harris'}}],
            'release-list': [{'date': '2018-04-06'}]
        }]
    }

    @patch('musicbrainzngs.search_recordings')
    @patch('musicbrainzngs.get_release_by_id')
    @patch('musicbrainzngs.get_release_group_by_id')
    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_by_release_group_success(
        self, mock_search_rg, mock_get_rg, mock_get_release, mock_search_rec
    ):
        """
        Tests the primary path, ensuring the correct track is selected from a release.
        """
        # --- Setup Mocks ---
        mock_search_rg.return_value = self.mock_release_group_search
        mock_get_rg.return_value = self.mock_release_group_details
        mock_get_release.return_value = self.mock_release_details
        mock_search_rec.return_value = {'recording-list': []}

        # --- Call the function ---
        result = find_best_match("One Kiss", "Calvin Harris and Dua Lipa")

        # --- Assertions ---
        self.assertIsNotNone(result)
        # Check that it found the correct track and not the first one
        self.assertEqual(result['recording_id'], 'rec-id-correct')
        self.assertEqual(result['title'], 'One Kiss')
        # Check for the new ID and artist fields
        self.assertEqual(result['release_id'], 'release-id-1')
        self.assertEqual(result['release_group_id'], 'rg-id-1')
        self.assertEqual(result['artist'], 'Calvin Harris and Dua Lipa')
        self.assertEqual(result['primary_artist'], 'Calvin Harris')
        self.assertEqual(result['release_year'], '2018')
        # Check that the fallback was not used
        mock_search_rec.assert_not_called()

    @patch('musicbrainzngs.search_recordings')
    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_fallback_to_recording_search(
        self, mock_search_rg, mock_search_rec
    ):
        """
        Tests the fallback path: release group search fails, recording search succeeds.
        """
        # --- Setup Mocks ---
        mock_search_rg.return_value = {'release-group-list': []}
        mock_search_rec.return_value = self.mock_recording_search

        # --- Call the function ---
        result = find_best_match("One Kiss", "Calvin Harris and Dua Lipa")

        # --- Assertions ---
        self.assertIsNotNone(result)
        self.assertEqual(result['recording_id'], 'rec-id-fallback')
        # Fallback doesn't have release/rg IDs
        self.assertIsNone(result['release_id'])
        self.assertIsNone(result['release_group_id'])

    @patch('musicbrainzngs.search_recordings')
    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_all_fail(self, mock_search_rg, mock_search_rec):
        """
        Tests the failure path: both search methods find no results.
        """
        # --- Setup Mocks ---
        mock_search_rg.return_value = {'release-group-list': []}
        mock_search_rec.return_value = {'recording-list': []}

        # --- Call the function ---
        result = find_best_match("Unknown Song", "Unknown Artist")

        # --- Assertions ---
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
