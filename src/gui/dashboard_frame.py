import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.data.database_manager import get_mastery_distribution, get_practice_history, get_problem_songs


class DashboardFrame(ttk.Frame):
    """
    A frame dedicated to displaying advanced statistics and visualizations.
    """

    def __init__(self, parent, controller):
        """
        Initializes the DashboardFrame.
        """
        super().__init__(parent, style="TFrame")
        self.controller = controller

        # --- Main Container ---
        main_container = ttk.Frame(self, style="TFrame", padding="20 10")
        main_container.pack(expand=True, fill="both")
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_rowconfigure(2, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        # --- Header ---
        header_frame = ttk.Frame(main_container, style="TFrame")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        title_label = ttk.Label(
            header_frame,
            text="Statistics Dashboard",
            style="Title.TLabel"
        )
        title_label.pack(side="left", fill="x", expand=True)

        back_button = ttk.Button(
            header_frame,
            text="Back to Main Menu",
            command=lambda: self.controller.show_frame("MainMenuFrame"),
            style="Back.TButton"
        )
        back_button.pack(side="right")

        # --- Placeholder Frames for Charts ---
        self.mastery_canvas = None  # To hold the chart widget
        self.history_canvas = None  # To hold the history chart widget

        # Top Row
        self.mastery_chart_frame = ttk.LabelFrame(
            main_container,
            text="Mastery Chart",
            style="TLabelframe"
        )
        self.mastery_chart_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.problem_songs_frame = ttk.LabelFrame(
            main_container,
            text="Problem Songs",
            style="TLabelframe"
        )
        self.problem_songs_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        ttk.Label(self.problem_songs_frame, text="[Problem Songs List Placeholder]").pack(padx=5, pady=5)

        # Bottom Row
        self.history_chart_frame = ttk.LabelFrame(
            main_container,
            text="Practice History",
            style="TLabelframe"
        )
        self.history_chart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        self._create_mastery_chart()
        self._create_history_chart()
        self._create_problem_songs_view()

    def _create_mastery_chart(self):
        """
        Creates and embeds the mastery distribution bar chart.
        """
        # 1. Clear placeholder and any existing chart
        for widget in self.mastery_chart_frame.winfo_children():
            widget.destroy()

        if self.mastery_canvas:
            self.mastery_canvas.get_tk_widget().destroy()

        # 2. Get data
        distribution = get_mastery_distribution()
        labels = ["Not Yet Learned", "Learning", "Mastered"]
        counts = [distribution[label] for label in labels]
        colors = ['salmon', 'skyblue', 'lightgreen']

        # 3. Create Matplotlib Figure and Subplot
        fig = Figure(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#f0f0f0') # Match Tkinter's default bg
        ax = fig.add_subplot(111)

        bars = ax.bar(labels, counts, color=colors)

        # 4. Customize the plot
        ax.set_title("Library Mastery Distribution", fontsize=14)
        ax.set_ylabel("Count of Songs")
        ax.set_ylim(0, max(counts) * 1.15 if any(counts) else 10) # Dynamic Y-axis
        ax.set_xticklabels(labels, rotation=0) # Ensure labels are horizontal

        # 5. Add count labels on top of bars
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval),
                    ha='center', va='bottom')

        fig.tight_layout()

        # 6. Embed the plot in Tkinter
        self.mastery_canvas = FigureCanvasTkAgg(fig, master=self.mastery_chart_frame)
        self.mastery_canvas.draw()
        self.mastery_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_history_chart(self):
        """
        Creates and embeds the practice history combination chart.
        """
        # 1. Clear any existing chart
        for widget in self.history_chart_frame.winfo_children():
            widget.destroy()

        if self.history_canvas:
            self.history_canvas.get_tk_widget().destroy()

        # 2. Get data
        history_data = get_practice_history(days=30)

        # 3. Process data for the last 30 days
        today = date.today()
        all_dates = [today - timedelta(days=i) for i in range(29, -1, -1)]

        labels = [d.strftime('%m-%d') for d in all_dates]
        attempts = []
        success_ratios = []

        for dt in all_dates:
            iso_date = dt.isoformat()
            if iso_date in history_data:
                day_data = history_data[iso_date]
                num_attempts = day_data['attempts']
                num_correct = day_data['correct']
                attempts.append(num_attempts)
                ratio = (num_correct / num_attempts) * 100 if num_attempts > 0 else 0
                success_ratios.append(ratio)
            else:
                attempts.append(0)
                success_ratios.append(0)

        # 4. Create Matplotlib Figure and Subplot
        fig = Figure(figsize=(12, 5), dpi=100)
        fig.patch.set_facecolor('#f0f0f0')
        ax1 = fig.add_subplot(111)

        # 5. Bar chart for attempts (Primary Y-axis)
        bar_color = 'skyblue'
        ax1.set_ylabel('Number of Songs Attempted', color=bar_color)
        ax1.bar(labels, attempts, color=bar_color, label='Songs Attempted')
        ax1.tick_params(axis='y', labelcolor=bar_color)
        ax1.set_ylim(0, max(attempts) * 1.15 if any(attempts) else 10)
        ax1.tick_params(axis='x', rotation=45)

        # 6. Line graph for success ratio (Secondary Y-axis)
        ax2 = ax1.twinx()
        line_color = 'salmon'
        ax2.set_ylabel('Daily Success Ratio (%)', color=line_color)
        ax2.plot(labels, success_ratios, color=line_color, marker='o', linestyle='-', label='Success Ratio (%)')
        ax2.tick_params(axis='y', labelcolor=line_color)
        ax2.set_ylim(0, 105)

        # 7. Customize the plot
        ax1.set_title("Daily Practice History (Last 30 Days)", fontsize=14, pad=20)
        fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
        fig.tight_layout(rect=[0, 0, 1, 0.95]) # Adjust layout to prevent title overlap

        # 8. Embed the plot in Tkinter
        self.history_canvas = FigureCanvasTkAgg(fig, master=self.history_chart_frame)
        self.history_canvas.draw()
        self.history_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def _create_problem_songs_view(self):
        """
        Creates and populates the view for problem songs.
        """
        # 1. Clear any existing widgets
        for widget in self.problem_songs_frame.winfo_children():
            widget.destroy()

        # 2. Get data
        problem_songs = get_problem_songs(limit=5)

        # 3. Handle case with no data
        if not problem_songs:
            no_data_label = ttk.Label(
                self.problem_songs_frame,
                text="Play some songs to see your stats!",
                style="Muted.TLabel",
                anchor="center"
            )
            no_data_label.pack(expand=True, fill="both", padx=10, pady=10)
            return

        # 4. Create and configure Treeview
        columns = ("Title", "Artist", "Success Rate")
        tree = ttk.Treeview(
            self.problem_songs_frame,
            columns=columns,
            show="headings",
            height=5  # Show 5 rows
        )

        # Define headings
        tree.heading("Title", text="Title")
        tree.heading("Artist", text="Artist")
        tree.heading("Success Rate", text="Success Rate")

        # Configure column widths
        tree.column("Title", width=150, stretch=tk.YES)
        tree.column("Artist", width=100, stretch=tk.YES)
        tree.column("Success Rate", width=80, anchor="e")

        # 5. Populate the Treeview
        for song in problem_songs:
            # Format success rate as a percentage string
            success_rate_str = f"{song['success_rate']:.0%}"
            tree.insert(
                "",
                tk.END,
                values=(song['title'], song['artist'], success_rate_str)
            )

        tree.pack(expand=True, fill='both', padx=5, pady=5)

    def refresh_charts(self):
        """
        Public method to refresh all charts in the dashboard.
        """
        self._create_mastery_chart()
        self._create_history_chart()
        self._create_problem_songs_view()
