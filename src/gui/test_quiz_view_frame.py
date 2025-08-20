import pytest
from unittest.mock import MagicMock, patch
from src.gui.quiz_view_frame import QuizView

@pytest.fixture
def mock_controller():
    # The controller needs a `show_frame` method. We create a mock that has it.
    controller = MagicMock()
    controller.show_frame = MagicMock()
    # Mock the style object that the view expects
    controller.style = MagicMock()
    return controller

@pytest.fixture
def quiz_view(mock_controller):
    # Patch all external dependencies of QuizView and the Tk root
    with patch('tkinter.Tk'), \
         patch('src.gui.quiz_view_frame.song_library') as mock_song_lib, \
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
        mock_session_instance.mode = "Challenge"
        mock_session_instance.score = 7
        mock_session_instance.total_questions = 10

        # A mock parent is needed for the widget hierarchy
        mock_parent = MagicMock()

        view = QuizView(parent=mock_parent, controller=mock_controller)

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

    # Act
    quiz_view.handle_user_response(was_correct=was_correct)

    # Assert
    # 1. Check if play history was recorded
    quiz_view.mock_db_manager.record_play_history.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct,
        reaction_time=reaction_time
    )

    # 2. Check that the main SRS service function was called
    quiz_view.mock_srs_service.update_srs_data_for_song.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct,
        reaction_time=reaction_time
    )

    # 3. Check if the result was recorded in the session
    quiz_view.session.record_result.assert_called_once_with(was_correct)

    # 4. Check if it proceeds to the next song
    quiz_view.session.next_song.assert_called_once()


def test_start_new_quiz_passes_shuffled_list(quiz_view):
    """
    Tests if start_new_quiz shuffles the song list before creating a QuizSession.
    """
    # Arrange
    due_songs = [1, 2, 3, 4, 5]
    quiz_view.mock_song_lib.get_due_songs.return_value = due_songs
    test_mode = "Standard"

    # Act
    quiz_view.start_new_quiz(mode=test_mode)

    # Assert
    # Check that QuizSession was called with the correct mode and song IDs,
    # but we can't assume the order of song_ids due to shuffling.
    quiz_view.MockQuizSession.assert_called_once()
    call_args, call_kwargs = quiz_view.MockQuizSession.call_args
    assert "mode" in call_kwargs and call_kwargs["mode"] == test_mode
    assert "song_ids" in call_kwargs
    assert sorted(call_kwargs["song_ids"]) == sorted(due_songs)


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

    # Act
    quiz_view.handle_user_response(was_correct=was_correct)

    # Assert
    # 1. Check if play history was recorded
    quiz_view.mock_db_manager.record_play_history.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct,
        reaction_time=reaction_time
    )

    # 2. Check that the main SRS service function was called
    quiz_view.mock_srs_service.update_srs_data_for_song.assert_called_once_with(
        song_id=song_id,
        was_correct=was_correct,
        reaction_time=reaction_time
    )

    # 3. Check if the result was recorded in the session
    quiz_view.session.record_result.assert_called_once_with(was_correct)

    # 4. Check if it proceeds to the next song
    quiz_view.session.next_song.assert_called_once()
