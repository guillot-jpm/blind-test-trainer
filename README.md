# Blind Test Training Application

## Project Overview

A Python desktop application designed to help users improve their song recognition skills for "Guess the Song" style quizzes (blind tests). Users can build a personalized library of songs, learn them efficiently using a Spaced Repetition System (SRS), and test their knowledge across various game modes. The application features Spotify integration for metadata retrieval and a detailed statistics dashboard to track progress.

## Features

*   **Library Management:** Easily import your local music files. The application can automatically fetch metadata like title, artist, and release year from Spotify.
*   **SRS Learning (Standard Mode):** Uses a Spaced Repetition System to schedule review sessions. Songs you are less familiar with will appear more frequently, optimizing your learning time.
*   **Challenge Mode:** Test your knowledge with a random selection of songs from your entire library.
*   **Gauntlet Mode:** A high-stakes mode that quizzes you on your 10 most problematic songs.
*   **Learning Lab:** A passive listening mode designed to help you get more familiar with your problem songs without the pressure of a quiz.
*   **Statistics Dashboard:** Visualize your learning progress with charts showing your library's mastery distribution and daily practice history.
*   **Spotify Integration:** Automatically fetches song metadata and album art, saving you manual data entry.

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
    Open `config.ini` in a text editor and set the values in the `[Paths]`, `[Settings]`, and `[Spotify]` sections.

    *   **`music_folder`**: The absolute path to the folder containing your music files.
    *   **`database_file`**: The path where the application's database will be stored. It's recommended to keep the default value.
    *   **`snippet_duration_seconds`**: (Optional) The default duration of the audio snippet played during a standard quiz. Defaults to 15 seconds.
    *   **`CHALLENGE_MODE_SONG_COUNT`**: (Optional) The number of songs to include in a Challenge Mode session. Defaults to 20.

### Spotify Integration (Required for Metadata)

To use the Spotify metadata and album art fetching features, you must provide your own API credentials.

1.  **Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)** and log in.
2.  **Create a new App.** You can name it anything you like.
3.  Once created, you will see your **Client ID** and **Client Secret**.
4.  Copy these values into the `spotify_client_id` and `spotify_client_secret` fields in your `config.ini` file.

## How to Run

To launch the application, run the following command from the project's root directory:

```bash
python src/main.py
```
