import tkinter as tk
from tkinter import messagebox
import random
import threading
import time

import tempfile
import os
from pydub import AudioSegment
import pygame

from src.services.quiz_session import QuizSession
from src.data import song_library
from src.utils.config_manager import config


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
        self.session = None
        self.current_song = None
        self.start_time = 0

        # Initialize pygame mixer
        pygame.mixer.init()

        # --- Main layout frames ---
        self.top_region = tk.Frame(self)
        self.center_region = tk.Frame(self)
        self.bottom_region = tk.Frame(self)

        self.top_region.pack(side="top", fill="x", padx=10, pady=5)
        self.center_region.pack(expand=True, fill="both", padx=10, pady=10)
        self.bottom_region.pack(side="bottom", fill="x", padx=10, pady=10)

        self.center_region.grid_rowconfigure(0, weight=1)
        self.center_region.grid_columnconfigure(0, weight=1)

        # --- Top Region Widgets ---
        self.status_label = tk.Label(self.top_region, text="Welcome!")
        self.status_label.pack()

        # --- Center Region Widgets ---
        # This label will be shown/hidden as needed
        self.prompt_label = tk.Label(self.center_region, text="Press Spacebar when you know it!")

        self.play_song_button = tk.Button(
            self.center_region,
            text="Play Song",
            command=self.play_song_and_start_round
        )
        self.play_song_button.grid(row=0, column=0, sticky="nsew")


        # --- Bottom Region Widgets ---
        self.quit_button = tk.Button(
            self.bottom_region,
            text="Quit Session",
            command=lambda: controller.show_frame("MainMenuFrame")
        )
        self.quit_button.pack(side="right")

    def start_new_quiz(self):
        """
        Starts a new quiz session.
        This method is called by the main menu before switching to this frame.
        """
        due_songs = song_library.get_due_songs()
        if not due_songs:
            messagebox.showinfo("No Songs Due", "There are no songs due for review today!")
            self.controller.show_frame("MainMenuFrame")
            return

        self.session = QuizSession(song_ids=due_songs)
        self.prepare_next_question()

    def prepare_next_question(self):
        """
        Sets up the GUI for the next question in the session.
        """
        self.current_song = self.session.get_current_song()
        if self.current_song is None:
            # Quiz is finished
            self.show_quiz_results()
            return

        # Update status label
        q_num, total_q = self.session.get_session_progress()
        self.status_label.config(text=f"Question {q_num} of {total_q}")

        # Reset center region
        self.prompt_label.grid_forget()
        self.play_song_button.grid(row=0, column=0, sticky="nsew")

    def play_song_and_start_round(self):
        """
        Handles the 'Play Song' button click.
        It plays a snippet of the song and starts the timer.
        """
        music_folder = config.get("Paths", "music_folder")
        file_path = f"{music_folder}/{self.current_song['local_filename']}"

        try:
            song_audio = AudioSegment.from_file(file_path)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Song file not found: {file_path}")
            return

        # Ensure song is long enough for a snippet
        if len(song_audio) < 15000:
            messagebox.showerror("Error", "Song is too short to play.")
            return

        # Select a random 10-15 second snippet
        snippet_length = random.randint(10000, 15000)
        max_start = len(song_audio) - snippet_length
        start_time_ms = random.randint(0, max_start)
        snippet = song_audio[start_time_ms:start_time_ms + snippet_length]

        # Fade in and out
        snippet = snippet.fade_in(1000).fade_out(2000)

        def playback():
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_filename = f.name
            snippet.export(temp_filename, format="wav")
            try:
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
            except pygame.error as e:
                # Use after() to ensure messagebox is shown from the main thread
                self.after(0, lambda: messagebox.showerror("Playback Error", f"An error occurred during audio playback:\n\n{e}"))
            finally:
                # Stop music to release the file before deleting
                pygame.mixer.music.stop()
                os.remove(temp_filename)

        # UI changes
        self.play_song_button.grid_forget()
        self.prompt_label.grid(row=0, column=0, sticky="nsew")

        # Start timer and playback
        self.start_time = time.time()
        threading.Thread(target=playback, daemon=True).start()

    def show_quiz_results(self):
        """
        Displays the results at the end of the quiz.
        """
        # Placeholder for showing results.
        messagebox.showinfo("Quiz Finished", f"You completed the quiz! Your score: {self.session.score}")
        self.controller.show_frame("MainMenuFrame")
