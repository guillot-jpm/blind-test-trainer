import tkinter as tk
from src.gui.library_manager_window import create_library_manager_window

class MainWindow(tk.Tk):
    """
    This class represents the Main window.
    """
    def __init__(self):
        """
        Initializes the Main window.
        """
        super().__init__()
        self.title("Main Window")
        self.geometry("400x300")

        self.launch_button = tk.Button(
            self,
            text="Launch Library Manager",
            command=self.launch_library_manager
        )
        self.launch_button.pack(pady=20)

    def launch_library_manager(self):
        """
        Launches the Library Manager window.
        """
        create_library_manager_window(self)
