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
from src.data import song_library, database_manager
from src.services import srs_service
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
        self.reaction_time = 0.0
        self.round_state = "idle"  # Can be 'idle', 'playing', 'answering'

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

        # --- Answer Reveal Widgets (initially hidden) ---
        self.answer_reveal_frame = tk.Frame(self.center_region)

        self.answer_label = tk.Label(
            self.answer_reveal_frame,
            text="",
            font=("Arial", 16),
            wraplength=500
        )
        self.answer_label.pack(pady=20)

        buttons_frame = tk.Frame(self.answer_reveal_frame)
        buttons_frame.pack(pady=10)

        self.correct_button = tk.Button(
            buttons_frame,
            text="I Got It Right",
            command=lambda: self.handle_user_response(was_correct=True)
        )
        self.correct_button.pack(side="left", padx=10)

        self.incorrect_button = tk.Button(
            buttons_frame,
            text="I Was Wrong",
            command=lambda: self.handle_user_response(was_correct=False)
        )
        self.incorrect_button.pack(side="right", padx=10)


        # --- Bottom Region Widgets ---
        self.quit_button = tk.Button(
            self.bottom_region,
            text="Quit Session",
            command=self.quit_session
        )
        self.quit_button.pack(side="right")

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

        Args:
            mode (str): The selected quiz mode ('Standard' or 'Challenge').
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
                fallback=20  # Fallback in case the value is missing
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
            # Quiz is finished
            self.show_quiz_results()
            return

        # Update status label
        q_num, total_q = self.session.get_session_progress()
        self.status_label.config(text=f"Question {q_num} of {total_q}")

        # Reset center region for the next question
        self.answer_reveal_frame.grid_forget()
        self.prompt_label.grid_forget()
        self.play_song_button.grid(row=0, column=0, sticky="nsew")

    def handle_user_response(self, was_correct: bool):
        """
        Handles the user's feedback (correct/incorrect), logs the result,
        updates SRS data, and moves to the next song.

        Args:
            was_correct (bool): True if the user's response was correct.
        """
        song_id = self.current_song['song_id']

        # 1. Record play history
        try:
            database_manager.record_play_history(
                song_id=song_id,
                was_correct=was_correct,
                reaction_time=self.reaction_time
            )
        except Exception as e:
            print(f"Error recording play history: {e}")
            messagebox.showerror("Database Error", "Failed to save your progress. Please check the logs.")

        # 2. Record the result in the session
        self.session.record_result(was_correct)

        # 3. Update SRS data
        try:
            # The srs_service now handles fetching, calculating, and updating.
            srs_service.update_srs_data_for_song(
                song_id=song_id,
                was_correct=was_correct,
                reaction_time=self.reaction_time
            )
        except Exception as e:
            print(f"Error updating SRS data: {e}")
            messagebox.showerror("SRS Error", "Failed to update learning data. Please check the logs.")
            return # Don't proceed if there's an error

        # 4. Proceed to the next question
        self.proceed_to_next_song()

    def proceed_to_next_song(self):
        """Advances the session and prepares the next question."""
        self.session.next_song()
        self.prepare_next_question()

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
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except pygame.error as e:
                # Schedule the error to be shown in the main thread
                self.after(0, lambda: messagebox.showerror("Playback Error", f"An error occurred during audio playback:\n\n{e}"))
            finally:
                # This block runs when the music stops for any reason.
                pygame.mixer.music.stop()
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)

        # UI changes
        self.play_song_button.grid_forget()
        self.prompt_label.grid(row=0, column=0, sticky="nsew")

        # Bind spacebar to the handler and update state for the new round
        self.controller.bind("<space>", self.handle_spacebar_press)
        self.round_state = "playing"
        self.focus_set()  # Move focus to the frame to prevent spacebar-clicking buttons

        # Start timer, playback, and status checker
        self.start_time = time.time()
        threading.Thread(target=playback, daemon=True).start()
        self.after(100, self.check_music_status)

    def check_music_status(self):
        """
        Polls the status of the music playback. If the music stops and the
        round is still active, it means the song timed out.
        """
        if self.round_state != "playing":
            return  # Stop polling if the round has ended

        if not pygame.mixer.music.get_busy():
            print("Song finished naturally.")
            self.round_state = "answering"  # End the round
            self.reaction_time = -1  # Indicate timeout
            self.unbind_spacebar()
            self.show_answer_reveal_state()
        else:
            # Music is still playing, check again later.
            self.after(100, self.check_music_status)

    def handle_spacebar_press(self, event=None):
        """
        Handles the spacebar press event.
        Stops the timer, fades out the music, and shows the answer.
        """
        if self.round_state != "playing":
            return

        self.round_state = "answering" # End the round
        self.unbind_spacebar()

        # 1. Stop timer and store reaction time
        reaction_time = time.time() - self.start_time
        self.reaction_time = round(reaction_time, 2)
        print(f"Reaction time: {self.reaction_time} seconds")

        # 2. Fade out music
        pygame.mixer.music.fadeout(500)

        # 3. Transition to the answer reveal state
        self.after(500, self.show_answer_reveal_state)

        return "break"  # Stop the event from propagating to other widgets

    def unbind_spacebar(self):
        """
        Unbinds the spacebar from the controller.
        """
        self.controller.unbind("<space>")

    def show_answer_reveal_state(self):
        """
        Transitions the UI to show the song answer and user response options.
        """
        self.prompt_label.grid_forget()

        # Update status label to show reaction time
        if self.reaction_time != -1:
            self.status_label.config(text=f"Reaction Time: {self.reaction_time}s")
        else:
            self.status_label.config(text="Time's Up!")

        # Update and show the answer label
        song_info = f"{self.current_song['title']} - {self.current_song['artist']}"
        self.answer_label.config(text=song_info)

        # Show the answer frame
        self.answer_reveal_frame.grid(row=0, column=0, sticky="nsew")

    def show_quiz_results(self):
        """
        Displays the results at the end of the quiz based on the mode.
        """
        if self.session.mode == "Challenge":
            score = self.session.score
            total = self.session.total_questions
            message = f"Session Complete! You scored {score}/{total}."
            messagebox.showinfo("Challenge Mode Complete", message)
        else:
            messagebox.showinfo("Session Complete!", "Session Complete!")

        self.controller.show_frame("MainMenuFrame")
