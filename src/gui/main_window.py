from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from src.gui.library_manager_window import LibraryManagerWindow

class MainWindow(QWidget):
    """
    This class represents the Main window.
    """
    def __init__(self):
        """
        Initializes the Main window.
        """
        super().__init__()
        self.setWindowTitle("Main Window")
        self.resize(400, 300)

        self.library_manager_window = None

        layout = QVBoxLayout()

        self.launch_button = QPushButton("Launch Library Manager")
        self.launch_button.clicked.connect(self.launch_library_manager)
        layout.addWidget(self.launch_button)

        self.setLayout(layout)

    def launch_library_manager(self):
        """
        Launches the Library Manager window.
        """
        if self.library_manager_window is None or not self.library_manager_window.isVisible():
            self.library_manager_window = LibraryManagerWindow()
            self.library_manager_window.show()
