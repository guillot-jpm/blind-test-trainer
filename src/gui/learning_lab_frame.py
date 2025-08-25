import tkinter as tk
from tkinter import ttk
import pygame
import os
import logging
from src.data import song_library, database_manager
from src.utils.config_manager import config
from src.services import spotify_service
from PIL import Image, ImageTk
import io

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

        # --- Album Art Display ---
        self.album_art_label = ttk.Label(main_container)
        self.album_art_label.grid(row=1, column=0, columnspan=3, pady=20)
        self.placeholder_image = None
        self.album_art_photo = None
        self._load_placeholder_image()

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
                # get_song_by_id now returns a dictionary, which is more robust.
                song_record = song_library.get_song_by_id(song_id)

                # Defensively check that the song record exists and has a local_filename.
                if song_record and song_record.get('local_filename'):
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

    def _load_placeholder_image(self):
        """Loads and prepares the placeholder image."""
        try:
            placeholder_path = os.path.join("src", "assets", "placeholder.png")
            image = Image.open(placeholder_path)
            image = image.resize((300, 300), Image.LANCZOS)
            self.placeholder_image = ImageTk.PhotoImage(image)
        except FileNotFoundError:
            logging.error(f"Placeholder image not found at {placeholder_path}")
            self.placeholder_image = None
        except Exception as e:
            logging.error(f"Failed to load placeholder image: {e}")
            self.placeholder_image = None
        finally:
            self.album_art_label.config(image=self.placeholder_image)

    def update_song_info(self):
        """
        Updates the song title, artist, and album art.
        """
        if self.playlist:
            song = self.playlist[self.current_song_index]
            self.song_title_label.config(text=song.get('title', "Unknown Title"))
            self.artist_name_label.config(text=song.get('artist', "Unknown Artist"))
            self.update_album_art(song)
        else:
            self.song_title_label.config(text="Playlist is empty")
            self.artist_name_label.config(text="")
            if self.placeholder_image:
                self.album_art_label.config(image=self.placeholder_image)
            else:
                self.album_art_label.config(text="No Album Art", image='')

    def update_album_art(self, song):
        """
        Fetches and displays album art for the given song.
        """
        title = song.get('title')
        artist = song.get('artist')

        # Set placeholder immediately
        self.album_art_label.config(image=self.placeholder_image)

        if not title or not artist:
            return # Keep placeholder

        # In a real-world app, this should be offloaded to a background thread
        # to avoid freezing the GUI. For this project, we'll keep it simple.
        image_data = self.get_album_art_for_song(title, artist)

        if image_data:
            try:
                image = Image.open(io.BytesIO(image_data))
                image = image.resize((300, 300), Image.LANCZOS)
                # Keep a reference to avoid garbage collection
                self.album_art_photo = ImageTk.PhotoImage(image)
                self.album_art_label.config(image=self.album_art_photo)
            except Exception as e:
                logging.error(f"Failed to process image for '{title}': {e}")
                # Fallback to placeholder if image processing fails
                self.album_art_label.config(image=self.placeholder_image)

    def get_album_art_for_song(self, title, artist):
        """
        Gets album art for a song by title and artist.

        This function abstracts the two-step process:
        1. Search for the song on Spotify to get an ID.
        2. Fetch the album art using that ID.
        """
        try:
            logging.debug(f"Searching for '{title}' by '{artist}'")
            track_info = spotify_service.search_by_title_and_artist(title, artist)
            if track_info and track_info.get('spotify_id'):
                spotify_id = track_info['spotify_id']
                logging.debug(f"Found Spotify ID: {spotify_id}. Fetching album art.")
                return spotify_service.fetch_album_art_data(spotify_id)
            else:
                logging.warning(f"Could not find a Spotify track for '{title}' by '{artist}'.")
                return None
        except spotify_service.SpotifyAPIError as e:
            logging.error(f"A Spotify API error occurred for '{title}': {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred in get_album_art_for_song for '{title}': {e}")
            return None

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
