# src/services/test_musicbrainz_service.py

"""
Unit tests for the MusicBrainz service.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.services.musicbrainz_service import find_best_match

class TestMusicBrainzService(unittest.TestCase):
    """
    Test suite for the MusicBrainz service.
    """

    # --- Mocks for API Data ---
    mock_release_group_search = {
        'release-group-list': [{
            'id': 'rg-id-1', 'title': 'Bohemian Rhapsody', # FIX: Was 'A Night at the Opera'
            'artist-credit-phrase': 'Queen', 'score': 100
        }]
    }
    mock_release_group_details = {
        'release-group': {'release-list': [{'id': 'release-id-1', 'date': '1975-11-21'}]}
    }
    mock_release_details = {
        'release': {
            'artist-credit': [{'artist': {'name': 'Queen'}}],
            'medium-list': [{
                'track-list': [{
                    'recording': {'id': 'rec-id-1', 'title': 'Bohemian Rhapsody'}
                }]
            }]
        }
    }
    mock_recording_search = {
        'recording-list': [{
            'id': 'rec-id-fallback', 'title': 'Bohemian Rhapsody (Fallback)',
            'artist-credit-phrase': 'Queen', 'artist-credit': [{'artist': {'name': 'Queen'}}],
            'release-list': [{'date': '1999-12-31'}]
        }]
    }

    @patch('musicbrainzngs.search_recordings') # Add patch to prevent fallback network call
    @patch('musicbrainzngs.get_release_by_id')
    @patch('musicbrainzngs.get_release_group_by_id')
    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_by_release_group_success(
        self, mock_search_rg, mock_get_rg, mock_get_release, mock_search_rec
    ):
        """
        Tests the primary path: successfully finding a match via release group.
        """
        # --- Setup Mocks ---
        mock_search_rg.return_value = self.mock_release_group_search
        mock_get_rg.return_value = self.mock_release_group_details
        mock_get_release.return_value = self.mock_release_details
        # Ensure fallback search is not used
        mock_search_rec.return_value = {'recording-list': []}

        # --- Call the function ---
        result = find_best_match("Bohemian Rhapsody", "Queen")

        # --- Assertions ---
        self.assertIsNotNone(result)
        self.assertEqual(result['musicbrainz_id'], 'rec-id-1')
        self.assertEqual(result['title'], 'Bohemian Rhapsody')
        self.assertEqual(result['artist'], 'Queen')
        self.assertEqual(result['release_year'], '1975')
        mock_search_rg.assert_called_once()
        mock_get_rg.assert_called_once()
        mock_get_release.assert_called_once()
        mock_search_rec.assert_not_called() # Verify fallback was not triggered

    @patch('musicbrainzngs.search_recordings')
    @patch('musicbrainzngs.search_release_groups')
    def test_find_best_match_fallback_to_recording_search(
        self, mock_search_rg, mock_search_rec
    ):
        """
        Tests the fallback path: release group search fails, recording search succeeds.
        """
        # --- Setup Mocks ---
        mock_search_rg.return_value = {'release-group-list': []} # No release groups found
        mock_search_rec.return_value = self.mock_recording_search

        # --- Call the function ---
        result = find_best_match("Bohemian Rhapsody", "Queen")

        # --- Assertions ---
        self.assertIsNotNone(result)
        self.assertEqual(result['musicbrainz_id'], 'rec-id-fallback')
        self.assertEqual(result['title'], 'Bohemian Rhapsody (Fallback)')
        self.assertEqual(result['release_year'], '1999')
        mock_search_rg.assert_called_once()
        mock_search_rec.assert_called_once()

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
        mock_search_rg.assert_called_once()
        mock_search_rec.assert_called_once()

if __name__ == '__main__':
    unittest.main()
