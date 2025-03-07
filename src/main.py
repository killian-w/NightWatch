"""
NightWatch helps create a sleep-friendly environment by managing your devices during bedtime.

This script sets up the UI and handles the countdown timer.
"""

import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import sv_ttk
from actions import pause_media, shutdown_system, sleep_system
from timer import CountdownTimer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def resource_path(relative_path):
    """Get absolute path to resource (works for dev and bin)"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
        base_path = os.path.join(sys._MEIPASS, "resources")
    except Exception:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        base_path = os.path.join(current_dir, "resources")
    return os.path.join(base_path, relative_path)


class NightWatch(tk.Tk):
    """
    Main application class (subclass of tk.Tk)

    This class initializes and sets up the main application window and its components.
    """

    def __init__(self):
        super().__init__()
        self.setup_window()

        self.lbf_action = ttk.LabelFrame(self, text="Select Action", padding=5)
        action_options = ["Pause", "Sleep", "Shutdown"]

        self.cmb_actions = ttk.Combobox(
            self.lbf_action, values=action_options, state="readonly"
        )
        self.hour_string = tk.StringVar(value="00")
        self.minute_string = tk.StringVar(value="00")
        self.second_string = tk.StringVar(value="00")
        self.lbf_input_time = ttk.LabelFrame(self, text="Enter Time", padding=5)
        self.lbl_hours = ttk.Label(self.lbf_input_time, text="Hours")
        self.lbl_minutes = ttk.Label(self.lbf_input_time, text="Minutes")
        self.lbl_seconds = ttk.Label(self.lbf_input_time, text="Seconds")
        self.txt_hours = self.create_time_entry(
            self.lbf_input_time, self.hour_string, 0
        )
        self.txt_minutes = self.create_time_entry(
            self.lbf_input_time, self.minute_string, 1
        )
        self.txt_seconds = self.create_time_entry(
            self.lbf_input_time, self.second_string, 2
        )
        self.prg_time_left = ttk.Progressbar(self.lbf_input_time)
        self.btn_start_timer = ttk.Button(
            self, text="Start Timer", command=self.run_timer, padding=5
        )

        self.setup_ui()
        self.timer = None

        try:
            # Attempt to get the EUID
            euid = os.geteuid()
            if euid != 0:
                self.show_error("This program needs root privileges.")
                sys.exit(1)
        except AttributeError:
            # On Windows, os.geteuid() is not defined
            pass

    def setup_window(self):
        """Set up the main application window."""
        self.title("NightWatch")
        self.resizable(height=False, width=False)

        # Calculate the x and y coordinates for the center of the screen
        width, height = 252, 275
        screen_width, screen_height = (
            self.winfo_screenwidth(),
            self.winfo_screenheight(),
        )
        x, y = (screen_width / 2) - (width / 2), (screen_height / 2) - (height / 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        self.iconphoto(True, tk.PhotoImage(file=resource_path("icon.png")))

        if len(sys.argv) > 1 and sys.argv[1].lower() in [
            "--light-theme",
            "--light-mode",
        ]:
            sv_ttk.set_theme("light")
        else:
            sv_ttk.set_theme("dark")

    def setup_ui(self):
        """Set up the user interface elements."""
        # setup action section
        self.lbf_action.grid(row=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.cmb_actions.current(0)
        self.cmb_actions.bind(
            "<<ComboboxSelected>>", lambda _: self.cmb_actions.selection_clear()
        )
        self.cmb_actions.grid(row=0, padx=6, pady=10, sticky="ew")

        # setup time input section
        self.lbf_input_time.grid(row=1, columnspan=3, padx=10, pady=0, sticky="ew")
        self.lbl_hours.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_minutes.grid(column=1, row=0, padx=10, pady=5)
        self.lbl_seconds.grid(column=2, row=0, padx=10, pady=5)
        self.prg_time_left.grid(row=5, columnspan=3, padx=10, pady=10, sticky="ew")

        self.btn_start_timer.grid(row=6, columnspan=3, padx=10, pady=10, sticky="ew")

    def create_time_entry(self, parent, string_var, column):
        """Create a time entry widget."""
        entry = ttk.Entry(parent, width=3, textvariable=string_var, justify="center")
        entry.bind("<FocusIn>", lambda event: event.widget.select_range(0, "end"))
        entry.grid(column=column, row=1, padx=15, pady=5)
        return entry

    def run_timer(self):
        """Start the timer based on user input."""
        try:
            hours = int(self.hour_string.get())
            minutes = int(self.minute_string.get())
            seconds = int(self.second_string.get())
        except ValueError:
            self.show_error("Invalid values")
            return

        if hours <= 0 and minutes <= 0 and seconds <= 0:
            self.show_error("A positive number is required")
            return

        if self.timer:
            self.timer.stop()

        self.timer = CountdownTimer(hours, minutes, seconds, self.update_ui)
        self.timer.start()
        self.btn_start_timer.config(text="Cancel", command=self.reset_timer)

    def show_error(self, message):
        """Display an error message in a message box."""
        logging.error(str(message))
        messagebox.showinfo("NightWatch", "Error: " + message, icon="error")

    def update_ui(self, hours, minutes, seconds, clock_time, action=False):
        """Update the UI with the remaining time or execute action."""
        self.hour_string.set(f"{hours:02d}")
        self.minute_string.set(f"{minutes:02d}")
        self.second_string.set(f"{seconds:02d}")
        self.prg_time_left.configure(value=clock_time, maximum=self.timer.total_time)
        self.update()

        if action:
            self.execute_action()

    def reset_timer(self):
        """Reset the timer to its initial state."""
        if self.timer:
            self.timer.stop()
            self.timer = None

        self.hour_string.set("00")
        self.minute_string.set("00")
        self.second_string.set("00")
        self.prg_time_left.configure(value=0)
        self.update()
        logging.info("Timer has been reset")
        self.btn_start_timer.config(text="Start Timer", command=self.run_timer)

    def execute_action(self):
        """Execute the selected action after the countdown ends."""
        action = self.cmb_actions.get()
        if action == "Pause":
            pause_media()
        elif action == "Sleep":
            sleep_system(self)
        elif action == "Shutdown":
            shutdown_system(self)
        else:
            self.show_error("No action selected")
        self.btn_start_timer.config(text="Start Timer", command=self.run_timer)


if __name__ == "__main__":
    NightWatch().mainloop()
