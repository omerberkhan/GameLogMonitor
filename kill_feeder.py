import os
import re
import time
import tkinter as tk
from tkinter import filedialog, Menu
from pathlib import Path
import threading
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as Item

# Define paths for log file and output file
appdata_dir = os.getenv("APPDATA")
log_file_path = None
output_dir = Path(appdata_dir) / "Event Pulse_SC Edition"
output_file_path = output_dir / "killfeed.txt"
path_file_path = output_dir / "path.txt"

# Ensure the directories exist
os.makedirs(output_dir, exist_ok=True)
output_file_path.touch(exist_ok=True)

if path_file_path.exists():
    with open(path_file_path, "r") as f:
        saved_path = f.read().strip()
        if saved_path:
            log_file_path = Path(saved_path)

def create_icon():
    """Create a system tray icon."""
    img = Image.new("RGBA", (64, 64), "black")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    text = "EP"
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    text_x = (64 - text_width) // 2
    text_y = (64 - text_height) // 2
    draw.text((text_x, text_y), text, font=font, fill="cyan")
    return img

class EventPulseApp:
    def __init__(self, root, log_file_path, output_file_path, keywords, interval=0.5):
        self.root = root
        self.log_file_path = log_file_path
        self.output_file_path = output_file_path
        self.keywords = keywords
        self.interval = interval
        self.lines_to_display = []
        self.stop_monitoring = False
        self.overlay_locked = True

        # Check for log file existence
        if not self.log_file_path or not self.log_file_path.exists():
            self.prompt_for_log_file()

        # Configure the root window
        self.root.geometry("500x170+400+10")
        self.update_overlay_appearance()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        # Create UI components
        self.text_widget = tk.Text(self.root, font=("Arial", 12), fg="cyan", bg="black", wrap="word", state="disabled", borderwidth=0, highlightthickness=0)
        self.text_widget.pack(expand=True, fill="both", padx=10, pady=10)
        self.text_widget.tag_configure("cyan", foreground="cyan")
        self.text_widget.tag_configure("red", foreground="red")
        self.text_widget.tag_configure("white_centered", foreground="white", font=("Arial", 14, "bold"), justify="center")
        self.text_widget.tag_configure("exit_splash", foreground="white", font=("Arial", 72, "bold"), justify="center")

        # Enable dragging if unlocked
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.do_drag)

        # Set up system tray icon
        self.create_tray_icon()

        # Show about screen at startup
        self.show_about()

        # Start monitoring and GUI updates
        self.start_monitoring()
        self.start_displaying_log_data()

    def prompt_for_log_file(self):
        """Prompt the user to select the log file location."""
        file_path = filedialog.askopenfilename(title="Select game.log File", filetypes=[("Log Files", "*.log"), ("All Files", "*.*")])
        if file_path:
            self.log_file_path = Path(file_path)
            with open(path_file_path, "w") as f:
                f.write(file_path)
        else:
            self.exit_application()

    def create_tray_icon(self):
        menu = pystray.Menu(
            Item("Lock Position", self.toggle_lock, checked=lambda item: self.overlay_locked),
            Item("Exit", self.exit_application)
        )
        icon_image = create_icon()
        self.tray_icon = pystray.Icon("Event Pulse", icon_image, "Event Pulse", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def toggle_lock(self):
        self.overlay_locked = not self.overlay_locked
        self.update_overlay_appearance()

    def update_overlay_appearance(self):
        if self.overlay_locked:
            self.root.configure(background="black")
            self.root.wm_attributes("-transparentcolor", "black")
        else:
            self.root.configure(background="black")
            self.root.wm_attributes("-transparentcolor", None)

    def show_about(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - 250
        y = (screen_height // 2) - 85
        self.root.geometry(f"500x170+{x}+{y}")

        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", "Event Pulse: Star Citizen Edition\n\nMade by ChatGPT with human interaction\nby hank_sy (2025)", "white_centered")
        self.text_widget.config(state="disabled")

        self.root.after(7000, self.restore_overlay_position)

    def restore_overlay_position(self):
        self.root.geometry("500x170+400+10")
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.config(state="disabled")

    def show_exit_splash(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - 250
        y = (screen_height // 2) - 85
        self.root.geometry(f"500x170+{x}+{y}")

        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", "o7", "exit_splash")
        self.text_widget.config(state="disabled")
        self.root.update()

        time.sleep(7)

    def start_drag(self, event):
        if not self.overlay_locked:
            self.start_x = event.x
            self.start_y = event.y

    def do_drag(self, event):
        if not self.overlay_locked:
            x = self.root.winfo_x() + event.x - self.start_x
            y = self.root.winfo_y() + event.y - self.start_y
            self.root.geometry(f"500x170+{x}+{y}")

    def start_monitoring(self):
        self.stop_monitoring = False
        self.monitor_thread = threading.Thread(target=self.monitor_log_file, daemon=True)
        self.monitor_thread.start()

    def monitor_log_file(self):
        previous_lines = []

        while not self.stop_monitoring:
            try:
                with open(self.log_file_path, "r") as log_file:
                    current_lines = log_file.readlines()

                filtered_lines = [line for line in current_lines if any(keyword in line for keyword in self.keywords)]

                with open(self.output_file_path, "a") as output_file:
                    for line in filtered_lines:
                        if line not in previous_lines:
                            output_file.write(line)
                            self.lines_to_display.append(line)

                with open(self.output_file_path, "r") as file:
                    non_empty_lines = [l for l in file if l.strip()]
                with open(self.output_file_path, "w") as file:
                    file.writelines(non_empty_lines)

                previous_lines = current_lines

            except FileNotFoundError:
                self.text_widget.config(state="normal")
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", "Log file not found.", "cyan")
                self.text_widget.config(state="disabled")
                self.root.update()
                time.sleep(1)

            time.sleep(self.interval)

    def start_displaying_log_data(self):
        self.display_thread = threading.Thread(target=self.display_lines, daemon=True)
        self.display_thread.start()

    def display_lines(self):
        while not self.stop_monitoring:
            if self.lines_to_display:
                line = self.lines_to_display.pop(0)
                parsed_data = self.parse_line(line)

                if parsed_data:
                    self.text_widget.config(state="normal")
                    self.text_widget.delete("1.0", "end")
                    for key, value in parsed_data.items():
                        if value:
                            color = "red" if key == "Killed By" else "cyan"
                            self.text_widget.insert("end", f"{key}: {value}\n", color)
                    self.text_widget.config(state="disabled")

                self.root.update()
                time.sleep(2)
            else:
                time.sleep(0.1)

    def parse_line(self, line):
        if "<Vehicle Destruction>" in line:
            vehicle_match = re.search(r"Vehicle '([^']+)", line)
            location_match = re.search(r"in zone '([^']+)", line)
            caused_by_match = re.search(r"caused by '([^']+)", line)

            vehicle = self.truncate_data(vehicle_match.group(1).replace("_", " ")) if vehicle_match else "Unknown Vehicle"
            location = self.truncate_data(re.sub(r"_+|\b\d{6,}\b", " ", location_match.group(1))) if location_match else "Unknown Location"
            caused_by = self.truncate_data(caused_by_match.group(1)) if caused_by_match else "Unknown Cause"

            if killed_by.lower() in filtered_users.map(str.lower):
                return {"Actor": vehicle, "Killed By": caused_by, "Location": location}            

        elif "<Actor Death>" in line:
            actor_match = re.search(r"'([^']+)' \[\d+\] in zone '([^']+)", line)
            killed_by_match = re.search(r"killed by '([^']+)", line)
            cause_match = re.search(r"with damage type '([^']+)", line)

            actor = self.truncate_data(actor_match.group(1)) if actor_match else "Unknown Actor"
            location = self.truncate_data(re.sub(r"_+|\b\d{6,}\b", " ", actor_match.group(2))) if actor_match else "Unknown Location"
            killed_by = self.truncate_data(killed_by_match.group(1).replace("_", " ")) if killed_by_match else "Unknown Cause"
            cause = self.truncate_data(cause_match.group(1)) if cause_match else "Unknown Cause"

            if killed_by.lower() in filtered_users.map(str.lower):
                return {"Actor": actor, "Killed By": killed_by, "Cause": cause, "Location": location}
        
        return None

    def truncate_data(self, data):
        return data[:35] + "..." if len(data) > 35 else data

    def exit_application(self):
        self.stop_monitoring = True
        self.show_exit_splash()
        self.tray_icon.stop()
        self.root.destroy()

# Define keywords to search for in the log file
keywords = ['<Vehicle Destruction>', '<Actor Death>']

filtered_users = ['Voisys', 'TanilX', 'BYP0STMAN']

if __name__ == "__main__":
    root = tk.Tk()
    app = EventPulseApp(root, log_file_path, output_file_path, keywords)
    root.mainloop()