import tkinter as tk
from tkinter import ttk
import pygame
import os
import logging
from src.data import song_library, database_manager
from src.utils.config_manager import config

class LearningLabView(ttk.Frame):
    """
    A view dedicated to the Learning Lab for passive listening and song discovery.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.playlist = []
        self.current_song_index = 0
        self.is_playing = False
        self.after_id = None  # To store the ID of the 'after' job

        # --- Main container ---
        main_container = ttk.Frame(self)
        main_container.pack(expand=True, fill="both", padx=20, pady=10)
        main_container.columnconfigure(0, weight=1)

        # --- Title ---
        title_label = ttk.Label(main_container, text="Learning Lab", style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=20)

        # --- Album Art Placeholder ---
        album_art_frame = ttk.Frame(main_container, width=300, height=300, style="TFrame")
        album_art_frame.grid(row=1, column=0, columnspan=3, pady=20)
        # You can add a placeholder label or image here
        placeholder_label = ttk.Label(album_art_frame, text="Album Art", style="TLabel")
        placeholder_label.pack(expand=True)


        # --- Song Info ---
        self.song_title_label = ttk.Label(main_container, text="Song Title", style="Header.TLabel")
        self.song_title_label.grid(row=2, column=0, columnspan=3, pady=(10, 0))

        self.artist_name_label = ttk.Label(main_container, text="Artist Name", style="TLabel")
        self.artist_name_label.grid(row=3, column=0, columnspan=3, pady=(0, 20))

        # --- Controls ---
        controls_frame = ttk.Frame(main_container)
        controls_frame.grid(row=4, column=0, columnspan=3)

        self.prev_button = ttk.Button(controls_frame, text="Previous Track", style="TButton", command=self.play_previous_song)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.play_pause_button = ttk.Button(controls_frame, text="Play/Pause", style="TButton", command=self.toggle_play_pause)
        self.play_pause_button.grid(row=0, column=1, padx=5)

        self.next_button = ttk.Button(controls_frame, text="Next Track", style="TButton", command=self.play_next_song)
        self.next_button.grid(row=0, column=2, padx=5)

        # --- Back Button ---
        back_button = ttk.Button(
            main_container,
            text="Back to Main Menu",
            command=lambda: controller.show_frame("MainMenuFrame"),
            style="Back.TButton"
        )
        back_button.grid(row=5, column=0, columnspan=3, pady=(20, 0))

    def on_show(self):
        """
        Called when the frame is shown. Loads the playlist and starts playback.
        """
        self.load_playlist()
        if self.playlist:
            self.play_song(0)
        else:
            # Handle empty playlist on show
            self.update_song_info()

    def on_hide(self):
        """
        Called when the frame is hidden. Stops playback and the checker.
        """
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        logging.info("Learning Lab hidden, playback stopped.")

    def load_playlist(self):
        """
        Loads the playlist with problem songs.
        """
        logging.info("Loading playlist for Learning Lab.")
        self.playlist.clear()
        try:
            # As per user feedback, use get_problem_songs(limit=10)
            problem_songs = database_manager.get_problem_songs(limit=10)
            if not problem_songs:
                logging.warning("No problem songs found to create a playlist.")
                self.song_title_label.config(text="No problem songs found")
                self.artist_name_label.config(text="")
                return

            for problem_song in problem_songs:
                song_id = problem_song['song_id']
                # We need the full song record to get the local_filename
                song_data = song_library.get_song_by_id(song_id)

                # Defensively check that the song data exists and has a filename
                if song_data and song_data[4]:
                    song_record = {
                        "song_id": song_data[0],
                        "title": song_data[1],
                        "artist": song_data[2],
                        "release_year": song_data[3],
                        "local_filename": song_data[4],
                        "spotify_id": song_data[5],
                        "album_art_blob": song_data[6]
                    }
                    self.playlist.append(song_record)

            if self.playlist:
                logging.info(f"Loaded {len(self.playlist)} songs into the playlist.")
            else:
                 logging.warning("Playlist is empty after filtering problem songs for valid file paths.")
                 self.song_title_label.config(text="No playable problem songs found")
                 self.artist_name_label.config(text="Ensure songs have file paths.")


        except Exception as e:
            logging.error(f"Failed to load playlist: {e}")

    def play_song(self, song_index):
        """
        Loads and plays the song at the given index in the playlist.
        """
        if not self.playlist:
            logging.warning("Play requested but playlist is empty.")
            return

        self.current_song_index = song_index
        song = self.playlist[self.current_song_index]

        song_filename = song.get("local_filename")
        # This check is now defensive, the main filtering is in load_playlist
        if not song_filename:
            logging.error(f"Song '{song.get('title')}' has invalid file path, skipping.")
            self.play_next_song()
            return

        # Load music directory from config
        music_dir = config.get("Paths", "music_folder", fallback="music")
        song_path = os.path.join(music_dir, song_filename)

        if not os.path.exists(song_path):
            logging.error(f"Song file not found: {song_path}")
            # Skip to the next song
            self.play_next_song()
            return

        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.update_song_info()
            self.check_music_status() # Start checking status
        except pygame.error as e:
            logging.error(f"Could not play song {song_path}: {e}")

    def toggle_play_pause(self):
        """
        Toggles playback between play and pause.
        """
        if not self.playlist:
            return
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_pause_button.config(text="Play")
        else:
            if pygame.mixer.music.get_busy(): # It's paused
                 pygame.mixer.music.unpause()
            else: # It was stopped or at the beginning
                 self.play_song(self.current_song_index)
            self.is_playing = True
            self.play_pause_button.config(text="Pause")

    def play_next_song(self):
        """
        Plays the next song in the playlist, looping if at the end.
        """
        if not self.playlist:
            return
        next_index = (self.current_song_index + 1) % len(self.playlist)
        self.play_song(next_index)

    def play_previous_song(self):
        """
        Plays the previous song in the playlist, looping if at the beginning.
        """
        if not self.playlist:
            return
        prev_index = (self.current_song_index - 1 + len(self.playlist)) % len(self.playlist)
        self.play_song(prev_index)

    def update_song_info(self):
        """
        Updates the song title and artist labels.
        """
        if self.playlist:
            song = self.playlist[self.current_song_index]
            self.song_title_label.config(text=song['title'] or "Unknown Title")
            self.artist_name_label.config(text=song['artist'] or "Unknown Artist")
        else:
            self.song_title_label.config(text="Playlist is empty")
            self.artist_name_label.config(text="")

    def check_music_status(self):
        """
        Periodically checks if the current song has finished playing.
        If so, it plays the next song.
        """
        if self.after_id: # Cancel previous job
            self.after_cancel(self.after_id)

        if self.is_playing and not pygame.mixer.music.get_busy():
            # Song finished, play next one
            logging.info("Song finished, playing next.")
            self.play_next_song()
        else:
            # Check again in 250ms
            self.after_id = self.after(250, self.check_music_status)
