import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.data.database_manager import get_mastery_distribution


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

        # Top Row
        self.mastery_chart_frame = ttk.LabelFrame(
            main_container,
            text="Mastery Chart",
            style="TLabelframe"
        )
        self.mastery_chart_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        ttk.Label(self.mastery_chart_frame, text="[Mastery Chart Placeholder]").pack(padx=5, pady=5)

        problem_songs_frame = ttk.LabelFrame(
            main_container,
            text="Problem Songs",
            style="TLabelframe"
        )
        problem_songs_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        ttk.Label(problem_songs_frame, text="[Problem Songs List Placeholder]").pack(padx=5, pady=5)

        # Bottom Row
        history_chart_frame = ttk.LabelFrame(
            main_container,
            text="Practice History",
            style="TLabelframe"
        )
        history_chart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        ttk.Label(history_chart_frame, text="[Practice History Chart Placeholder]").pack(padx=5, pady=5)

        self._create_mastery_chart()

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

    def refresh_charts(self):
        """
        Public method to refresh all charts in the dashboard.
        """
        self._create_mastery_chart()
