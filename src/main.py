import logging
from src.gui.main_window import MainWindow
from src.utils.config_manager import load_config
from src.services.spotify_service import initialize_spotify_service

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'  # 'a' for append
)


if __name__ == "__main__":
    # 1. Load application configuration
    new_config_created = load_config()

    # 2. Initialize external services
    initialize_spotify_service()

    # 3. Create and run the main application window
    app = MainWindow(new_config_created=new_config_created)
    app.mainloop()
