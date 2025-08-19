import tkinter as tk
from src.gui.library_manager_window import create_library_manager_window


class MainMenuFrame(tk.Frame):
    """
    The main menu frame, providing options to start a quiz or manage the library.
    """

    def __init__(self, parent, controller):
        """
        Initializes the MainMenuFrame.

        Args:
            parent (tk.Widget): The parent widget.
            controller (tk.Tk): The main application window (controller).
        """
        super().__init__(parent)
        self.controller = controller

        # --- UI Components ---
        label = tk.Label(self, text="Main Menu", font=("Arial", 18))
        label.pack(pady=20)

        start_quiz_button = tk.Button(
            self,
            text="Start Quiz",
            command=self.start_quiz
        )
        start_quiz_button.pack(pady=10)

        launch_button = tk.Button(
            self,
            text="Launch Library Manager",
            command=self.launch_library_manager
        )
        launch_button.pack(pady=10)

    def start_quiz(self):
        """
        Starts a new quiz.
        """
        quiz_view = self.controller.frames["QuizView"]
        quiz_view.start_new_quiz()
        # The start_new_quiz method will switch to the main menu
        # if there are no songs, so we only switch if it doesn't.
        if quiz_view.session:
            self.controller.show_frame("QuizView")

    def launch_library_manager(self):
        """
        Launches the Library Manager window.
        """
        create_library_manager_window(self.controller)
