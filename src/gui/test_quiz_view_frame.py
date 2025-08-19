import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from src.gui.quiz_view_frame import QuizView

# Since this is a GUI component, we need a root window for it to exist
@pytest.fixture(scope="module")
def root_window():
    root = tk.Tk()
    # Prevent the window from showing up during tests
    root.withdraw()
    yield root
    root.destroy()

@pytest.fixture
def mock_controller(root_window):
    controller = MagicMock(spec=tk.Tk)
    # The controller is also the parent in this app's structure
    controller.winfo_toplevel.return_value = root_window
    return controller

@pytest.fixture
def quiz_view(root_window, mock_controller):
    # Patch the services that are imported and used by QuizView
    with patch('src.gui.quiz_view_frame.song_library') as mock_song_lib, \
         patch('src.gui.quiz_view_frame.database_manager') as mock_db_manager, \
         patch('src.gui.quiz_view_frame.srs_service') as mock_srs_service, \
         patch('src.gui.quiz_view_frame.QuizSession') as mock_quiz_session:

        # Make the QuizView's parent the root_window to satisfy tkinter
        view = QuizView(parent=root_window, controller=mock_controller)

        # Set up mocks
        view.session = mock_quiz_session.return_value
        view.current_song = {'song_id': 123, 'title': 'Test Song', 'artist': 'Tester'}
        view.reaction_time = 5.5

        # Attach mocks to the instance for access in tests
        view.mock_song_lib = mock_song_lib
        view.mock_db_manager = mock_db_manager
        view.mock_srs_service = mock_srs_service

        yield view

def test_handle_user_response_correct(quiz_view):
    """
    Tests if handle_user_response calls the correct functions when the user is correct.
    """
    # Arrange
    was_correct = True
    song_id = quiz_view.current_song['song_id']
    reaction_time = quiz_view.reaction_time

    # Mock the return value for the SRS calculation
    quiz_view.mock_srs_service.calculate_next_srs_review.return_value = (2, 2.6, '2025-01-01')

    # Act
    quiz_view.handle_user_response(was_correct=was_correct)

    # Assert
    # 1. Check if play history was recorded
    quiz_view.mock_db_manager.record_play_history.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct,
        reaction_time=reaction_time
    )

    # 2. Check if SRS calculation was called
    quiz_view.mock_srs_service.calculate_next_srs_review.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct
    )

    # 3. Check if SRS data was updated in the database
    quiz_view.mock_song_lib.update_srs_data.assert_called_once_with(
        song_id, 2, 2.6, '2025-01-01'
    )

    # 4. Check if it proceeds to the next song
    quiz_view.session.next_song.assert_called_once()


def test_handle_user_response_incorrect(quiz_view):
    """
    Tests if handle_user_response calls the correct functions when the user is incorrect.
    """
    # Arrange
    was_correct = False
    song_id = quiz_view.current_song['song_id']
    reaction_time = quiz_view.reaction_time
    quiz_view.mock_srs_service.calculate_next_srs_review.return_value = (1, 2.4, '2025-01-02')

    # Act
    quiz_view.handle_user_response(was_correct=was_correct)

    # Assert
    quiz_view.mock_db_manager.record_play_history.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct,
        reaction_time=reaction_time
    )
    quiz_view.mock_srs_service.calculate_next_srs_review.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct
    )
    quiz_view.mock_song_lib.update_srs_data.assert_called_once_with(
        song_id, 1, 2.4, '2025-01-02'
    )
    quiz_view.session.next_song.assert_called_once()
