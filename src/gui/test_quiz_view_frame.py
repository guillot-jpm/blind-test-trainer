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
    # The controller needs a `show_frame` method. We create a mock that has it.
    controller = MagicMock()
    controller.show_frame = MagicMock()
    # The view also expects the controller to be a tkinter widget, so we mock this.
    controller.winfo_toplevel.return_value = root_window
    return controller

@pytest.fixture
def quiz_view(root_window, mock_controller):
    # Patch all external dependencies of QuizView
    with patch('src.gui.quiz_view_frame.song_library') as mock_song_lib, \
         patch('src.gui.quiz_view_frame.database_manager') as mock_db_manager, \
         patch('src.gui.quiz_view_frame.srs_service') as mock_srs_service, \
         patch('src.gui.quiz_view_frame.QuizSession') as MockQuizSession, \
         patch('src.gui.quiz_view_frame.messagebox') as mock_messagebox, \
         patch('src.gui.quiz_view_frame.pygame.mixer') as mock_mixer:

        # Configure the mock session object that will be attached to the view
        mock_session_instance = MockQuizSession.return_value
        mock_session_instance.get_session_progress.return_value = (2, 10)
        mock_session_instance.get_current_song.return_value = {
            'song_id': 456, 'title': 'Next Song', 'artist': 'Next Artist'
        }
        # Add attributes needed for the new tests
        mock_session_instance.mode = "Challenge"
        mock_session_instance.score = 7
        mock_session_instance.total_questions = 10

        # Make the QuizView's parent the root_window to satisfy tkinter
        view = QuizView(parent=root_window, controller=mock_controller)

        # Manually set the session and other attributes for testing internal methods
        view.session = mock_session_instance
        view.current_song = {'song_id': 123, 'title': 'Test Song', 'artist': 'Tester'}
        view.reaction_time = 5.5

        # Attach mocks to the view instance for easy access in tests
        view.mock_song_lib = mock_song_lib
        view.mock_db_manager = mock_db_manager
        view.mock_srs_service = mock_srs_service
        view.MockQuizSession = MockQuizSession  # To check if it was instantiated
        view.mock_messagebox = mock_messagebox

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
        was_correct=was_correct,
        reaction_time=reaction_time
    )

    # 3. Check if SRS data was updated in the database
    quiz_view.mock_song_lib.update_srs_data.assert_called_once_with(
        song_id, 2, 2.6, '2025-01-01'
    )

    # 4. Check if the result was recorded
    quiz_view.session.record_result.assert_called_once_with(was_correct)

    # 5. Check if it proceeds to the next song
    quiz_view.session.next_song.assert_called_once()


def test_start_new_quiz_passes_mode(quiz_view):
    """
    Tests if start_new_quiz creates a QuizSession with the correct mode.
    """
    # Arrange
    quiz_view.mock_song_lib.get_due_songs.return_value = [1, 2, 3]
    test_mode = "Challenge"

    # Act
    quiz_view.start_new_quiz(mode=test_mode)

    # Assert
    quiz_view.MockQuizSession.assert_called_once_with(song_ids=[1, 2, 3], mode=test_mode)


def test_prepare_next_question_shows_results_when_finished(quiz_view):
    """
    Tests that prepare_next_question calls show_quiz_results when the session is over.
    """
    # Arrange
    quiz_view.session.get_current_song.return_value = None
    with patch.object(quiz_view, 'show_quiz_results') as mock_show_results:
        # Act
        quiz_view.prepare_next_question()
        # Assert
        mock_show_results.assert_called_once()


def test_show_quiz_results_challenge_mode(quiz_view):
    """
    Tests the correct message is shown for a completed Challenge mode session.
    """
    # Arrange
    quiz_view.session.mode = "Challenge"
    quiz_view.session.score = 8
    quiz_view.session.total_questions = 10

    # Act
    quiz_view.show_quiz_results()

    # Assert
    expected_message = "Session Complete! You scored 8/10."
    quiz_view.mock_messagebox.showinfo.assert_called_once_with(
        "Challenge Mode Complete", expected_message
    )
    quiz_view.controller.show_frame.assert_called_once_with("MainMenuFrame")


def test_show_quiz_results_standard_mode(quiz_view):
    """
    Tests the correct message is shown for a completed Standard mode session.
    """
    # Arrange
    quiz_view.session.mode = "Standard"

    # Act
    quiz_view.show_quiz_results()

    # Assert
    quiz_view.mock_messagebox.showinfo.assert_called_once_with(
        "Session Complete!", "Session Complete!"
    )
    quiz_view.controller.show_frame.assert_called_once_with("MainMenuFrame")


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
        was_correct=was_correct,
        reaction_time=reaction_time
    )
    quiz_view.mock_song_lib.update_srs_data.assert_called_once_with(
        song_id, 1, 2.4, '2025-01-02'
    )
    quiz_view.session.record_result.assert_called_once_with(was_correct)
    quiz_view.session.next_song.assert_called_once()
