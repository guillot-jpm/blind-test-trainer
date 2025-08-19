import tkinter as tk


class QuizView(tk.Frame):
    """
    The quiz view frame, where the main quiz gameplay occurs.
    """

    def __init__(self, parent, controller):
        """
        Initializes the QuizViewFrame.

        Args:
            parent (tk.Widget): The parent widget.
            controller (tk.Tk): The main application window (controller).
        """
        super().__init__(parent)
        self.controller = controller

        # --- Main layout frames ---
        self.top_region = tk.Frame(self)
        self.center_region = tk.Frame(self)
        self.bottom_region = tk.Frame(self)

        self.top_region.pack(side="top", fill="x", padx=10, pady=5)
        self.center_region.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        self.bottom_region.pack(side="bottom", fill="x", padx=10, pady=10)

        # --- Top Region Widgets ---
        self.status_label = tk.Label(self.top_region, text="Question 1/20 | Time: 00:30")
        self.status_label.pack()

        # --- Center Region Widgets ---
        self.play_song_button = tk.Button(self.center_region, text="Play Song")
        self.play_song_button.pack(pady=20)

        # --- Bottom Region Widgets ---
        self.quit_button = tk.Button(
            self.bottom_region,
            text="Quit Session",
            command=lambda: controller.show_frame("MainMenuFrame")
        )
        self.quit_button.pack(side="right")
