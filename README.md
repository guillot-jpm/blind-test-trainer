# Blind Test Training Application

## Project Overview

A Python application to help users train for blind tests (Guess the Song). This application allows you to build a library of songs, learn them using a Spaced Repetition System (SRS), and test your knowledge in a challenge mode.

## Features

*   **Library Management:** Build and manage your own song library.
*   **SRS Learning:** Learn songs effectively using a Spaced Repetition System.
*   **Challenge Mode:** Test your knowledge with a quiz-style challenge.
*   **Spotify Integration:** Fetch song metadata from Spotify.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2.  **Create and activate a Python virtual environment:**
    *   On Windows:
        ```bash
        python -m venv venv
        .\\venv\\Scripts\\activate
        ```
    *   On macOS and Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Create the configuration file:**
    Copy the `config.ini.template` file and rename it to `config.ini`.

2.  **Edit `config.ini`:**
    Open `config.ini` in a text editor and set the following values:
    *   `music_folder`: The absolute path to the folder containing your music files.
    *   `database_file`: The path where the application's database will be stored. It's recommended to keep the default value (`data/quiz_library.db`).

## How to Run

To launch the application, run the following command from the project's root directory:

```bash
python src/main.py
```
