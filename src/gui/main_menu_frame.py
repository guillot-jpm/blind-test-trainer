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
        self.quiz_mode = tk.StringVar(value="Challenge")

        # --- UI Components ---
        label = tk.Label(self, text="Main Menu", font=("Arial", 18))
        label.pack(pady=20)

        # --- Mode Selection ---
        mode_frame = tk.LabelFrame(self, text="Quiz Mode", padx=10, pady=10)
        mode_frame.pack(pady=10, padx=20, fill="x")

        challenge_radio = tk.Radiobutton(
            mode_frame,
            text="Challenge Mode (Score is tracked)",
            variable=self.quiz_mode,
            value="Challenge"
        )
        challenge_radio.pack(anchor="w")

        standard_radio = tk.Radiobutton(
            mode_frame,
            text="Standard Mode (Simple practice)",
            variable=self.quiz_mode,
            value="Standard"
        )
        standard_radio.pack(anchor="w")

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
        Starts a new quiz with the selected mode.
        """
        quiz_view = self.controller.frames["QuizView"]
        selected_mode = self.quiz_mode.get()
        quiz_view.start_new_quiz(mode=selected_mode)

        # The start_new_quiz method will handle showing the main menu
        # if there are no songs due.
        if quiz_view.session:
            self.controller.show_frame("QuizView")

    def launch_library_manager(self):
        """
        Launches the Library Manager window.
        """
        create_library_manager_window(self.controller)
