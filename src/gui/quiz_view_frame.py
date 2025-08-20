import logging
import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import time

import tempfile
import os
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import pygame

from src.services.quiz_session import QuizSession
from src.data import song_library, database_manager
from src.services import srs_service
from src.utils.config_manager import config


class QuizView(ttk.Frame):
    """
    The quiz view frame, where the main quiz gameplay occurs.
    """

    def __init__(self, parent, controller):
        """
        Initializes the QuizViewFrame.
        """
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self.session = None
        self.current_song = None
        self.start_time = 0
        self.reaction_time = 0.0
        self.round_state = "idle"  # Can be 'idle', 'playing', 'answering'

        # Initialize pygame mixer
        pygame.mixer.init()

        # --- Style for transient messages ---
        self.controller.style.configure("Warning.TLabel",
                                        foreground="orange",
                                        font=self.controller.body_font)
        self.controller.style.configure("Prompt.TLabel",
                                        font=self.controller.header_font)
        self.controller.style.configure("Answer.TLabel",
                                        font=self.controller.title_font,
                                        wraplength=500)


        # --- Main layout frames ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_bar = ttk.Frame(self, style="TFrame", padding="0 0 0 5")
        top_bar.grid(row=0, column=0, sticky="ew")

        self.center_region = ttk.Frame(self, style="TFrame")
        self.center_region.grid(row=1, column=0, sticky="nsew")
        self.center_region.grid_rowconfigure(0, weight=1)
        self.center_region.grid_columnconfigure(0, weight=1)

        # --- Top Bar Widgets ---
        self.quit_button = ttk.Button(
            top_bar,
            text="< Quit Session",
            command=self.quit_session,
            style="Back.TButton"
        )
        self.quit_button.pack(side="left", pady=(5, 0))

        self.status_label = ttk.Label(top_bar, text="Welcome!", anchor="center")
        self.status_label.pack(side="top", fill="x", expand=True, pady=5)


        # --- Center Region Widgets ---
        self.prompt_label = ttk.Label(
            self.center_region,
            text="Press Spacebar when you know it!",
            style="Prompt.TLabel",
            anchor="center"
        )

        self.skip_message_label = ttk.Label(
            self.center_region,
            text="Could not find song file. Skipping.",
            style="Warning.TLabel",
            anchor="center"
        )

        self.play_song_button = ttk.Button(
            self.center_region,
            text="Play Song",
            command=self.play_song_and_start_round,
            style="TButton"
        )
        self.play_song_button.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)

        # --- Answer Reveal Widgets (initially hidden) ---
        self.answer_reveal_frame = ttk.Frame(self.center_region, style="TFrame")
        self.answer_reveal_frame.grid_columnconfigure(0, weight=1)


        self.answer_label = ttk.Label(
            self.answer_reveal_frame,
            text="",
            style="Answer.TLabel",
            anchor="center"
        )
        self.answer_label.grid(row=0, column=0, sticky="ew", pady=(20,10))

        buttons_frame = ttk.Frame(self.answer_reveal_frame, style="TFrame")
        buttons_frame.grid(row=1, column=0, pady=10)

        self.correct_button = ttk.Button(
            buttons_frame,
            text="I Got It Right",
            command=lambda: self.handle_user_response(was_correct=True),
            style="TButton"
        )
        self.correct_button.pack(side="left", padx=10)

        self.incorrect_button = ttk.Button(
            buttons_frame,
            text="I Was Wrong",
            command=lambda: self.handle_user_response(was_correct=False),
            style="TButton"
        )
        self.incorrect_button.pack(side="right", padx=10)


    def quit_session(self):
        """
        Safely quits the current quiz session and returns to the main menu.
        """
        # Stop any ongoing processes
        self.round_state = "idle"
        pygame.mixer.music.stop()
        self.unbind_spacebar()

        # Navigate back to the main menu
        self.controller.show_frame("MainMenuFrame")

    def start_new_quiz(self, mode: str):
        """
        Starts a new quiz session based on the selected mode.
        """
        self.session = None  # Reset session
        song_ids_for_quiz = []

        if mode == "Standard":
            song_ids_for_quiz = song_library.get_due_songs()
            if not song_ids_for_quiz:
                messagebox.showinfo(
                    "No Songs Due",
                    "No songs are due for review today. Great job!"
                )
                return
            random.shuffle(song_ids_for_quiz)

        elif mode == "Challenge":
            all_song_ids = song_library.get_all_song_ids()
            total_songs = len(all_song_ids)

            if total_songs == 0:
                messagebox.showinfo(
                    "Empty Library",
                    "Your library is empty. Please add songs before starting a challenge."
                )
                return

            song_count_config = config.getint(
                'Settings',
                'CHALLENGE_MODE_SONG_COUNT',
                fallback=20
            )

            num_to_select = min(song_count_config, total_songs)
            song_ids_for_quiz = random.sample(all_song_ids, num_to_select)

        self.session = QuizSession(song_ids=song_ids_for_quiz, mode=mode)
        self.prepare_next_question()

    def prepare_next_question(self):
        """
        Sets up the GUI for the next question in the session.
        """
        self.current_song = self.session.get_current_song()
        if self.current_song is None:
            self.show_quiz_results()
            return

        q_num, total_q = self.session.get_session_progress()
        self.status_label.config(text=f"Question {q_num} of {total_q}")

        self.answer_reveal_frame.grid_forget()
        self.prompt_label.grid_forget()
        self.skip_message_label.grid_forget()
        self.play_song_button.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)

    def handle_user_response(self, was_correct: bool):
        """
        Handles the user's feedback (correct/incorrect), logs the result,
        updates SRS data, and moves to the next song.
        """
        song_id = self.current_song['song_id']

        try:
            database_manager.record_play_history(
                song_id=song_id,
                was_correct=was_correct,
                reaction_time=self.reaction_time
            )
        except Exception as e:
            logging.error(f"Error recording play history: {e}")
            messagebox.showerror("Database Error", "Failed to save your progress. Please check the logs.")

        self.session.record_result(was_correct)

        try:
            srs_service.update_srs_data_for_song(
                song_id=song_id,
                was_correct=was_correct,
                reaction_time=self.reaction_time
            )
        except Exception as e:
            logging.error(f"Error updating SRS data: {e}")
            messagebox.showerror("SRS Error", "Failed to update learning data. Please check the logs.")
            return

        self.proceed_to_next_song()

    def proceed_to_next_song(self):
        """Advances the session and prepares the next question."""
        self.session.next_song()
        self.prepare_next_question()

    def show_skip_message(self):
        """
        Displays a temporary message when a song is skipped.
        """
        self.play_song_button.grid_forget()
        self.prompt_label.grid_forget()
        self.answer_reveal_frame.grid_forget()

        self.skip_message_label.grid(row=0, column=0, sticky="nsew")
        self.after(3500, self.skip_message_label.grid_forget)

    def play_song_and_start_round(self):
        """
        Handles the 'Play Song' button click.
        """
        music_folder = config.get("Paths", "music_folder")
        file_path = f"{music_folder}/{self.current_song['local_filename']}"

        try:
            song_audio = AudioSegment.from_file(file_path)
        except (FileNotFoundError, CouldntDecodeError):
            logging.warning(
                "Skipped a quiz question due to a missing audio file "
                f"'{self.current_song['local_filename']}'."
            )
            self.show_skip_message()
            self.after(50, self.proceed_to_next_song)
            return

        if len(song_audio) < 15000:
            messagebox.showerror("Error", "Song is too short to play.")
            return

        snippet_length = random.randint(10000, 15000)
        max_start = len(song_audio) - snippet_length
        start_time_ms = random.randint(0, max_start)
        snippet = song_audio[start_time_ms:start_time_ms + snippet_length]
        snippet = snippet.fade_in(1000).fade_out(2000)

        def playback():
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_filename = f.name
            snippet.export(temp_filename, format="wav")
            try:
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except pygame.error as e:
                self.after(0, lambda: messagebox.showerror("Playback Error", f"An error occurred during audio playback:\n\n{e}"))
            finally:
                pygame.mixer.music.stop()
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)

        self.play_song_button.grid_forget()
        self.prompt_label.grid(row=0, column=0, sticky="nsew")

        self.controller.bind("<space>", self.handle_spacebar_press)
        self.round_state = "playing"
        self.focus_set()

        self.start_time = time.time()
        threading.Thread(target=playback, daemon=True).start()
        self.after(100, self.check_music_status)

    def check_music_status(self):
        """
        Polls the status of music playback.
        """
        if self.round_state != "playing":
            return

        if not pygame.mixer.music.get_busy():
            self.round_state = "answering"
            self.reaction_time = -1
            self.unbind_spacebar()
            self.show_answer_reveal_state()
        else:
            self.after(100, self.check_music_status)

    def handle_spacebar_press(self, event=None):
        """
        Handles the spacebar press event.
        """
        if self.round_state != "playing":
            return

        self.round_state = "answering"
        self.unbind_spacebar()

        reaction_time = time.time() - self.start_time
        self.reaction_time = round(reaction_time, 2)
        pygame.mixer.music.fadeout(500)
        self.after(500, self.show_answer_reveal_state)

        return "break"

    def unbind_spacebar(self):
        """
        Unbinds the spacebar from the controller.
        """
        self.controller.unbind("<space>")

    def show_answer_reveal_state(self):
        """
        Transitions the UI to show the song answer.
        """
        self.prompt_label.grid_forget()

        if self.reaction_time != -1:
            self.status_label.config(text=f"Reaction Time: {self.reaction_time}s")
        else:
            self.status_label.config(text="Time's Up!")

        song_info = f"{self.current_song['title']} - {self.current_song['artist']}"
        self.answer_label.config(text=song_info)
        self.answer_reveal_frame.grid(row=0, column=0, sticky="nsew")

    def show_quiz_results(self):
        """
        Displays the results at the end of the quiz.
        """
        if self.session.mode == "Challenge":
            score = self.session.score
            total = self.session.total_questions
            message = f"Session Complete! You scored {score}/{total}."
            messagebox.showinfo("Challenge Mode Complete", message)
        else:
            messagebox.showinfo("Session Complete!", "Session Complete!")

        self.controller.show_frame("MainMenuFrame")
