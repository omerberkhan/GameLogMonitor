import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
from pathlib import Path
import pystray
from PIL import Image, ImageDraw, ImageFont
import queue
import re
from datetime import datetime, timezone
import configparser
import json

# Load weapon IDs globally
WEAPON_IDS = {}
try:
    weapon_ids_path = Path("weapon_ids.json")
    if weapon_ids_path.exists():
        with open(weapon_ids_path, 'r', encoding='utf-8') as file:
            WEAPON_IDS = json.load(file)
        print(f"Loaded {len(WEAPON_IDS)} weapon IDs from weapon_ids.json")
    else:
        print("weapon_ids.json not found")
except Exception as e:
    print(f"Error loading weapon IDs: {e}")

# Load location IDs globally
LOCATION_IDS = {}
try:
    location_ids_path = Path("location_ids.json")
    if location_ids_path.exists():
        with open(location_ids_path, 'r', encoding='utf-8') as file:
            LOCATION_IDS = json.load(file)
        print(f"Loaded {len(LOCATION_IDS)} location IDs from location_ids.json")
    else:
        print("location_ids.json not found")
except Exception as e:
    print(f"Error loading location IDs: {e}")

class LogMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Log Monitor")
        self.root.geometry("500x180")
        self.root.resizable(False, False)
        
        # Config file path
        self.config_dir = Path.home() / "AppData" / "Local" / "GameLogMonitor"
        self.config_file = self.config_dir / "settings.ini"
        self.config_dir.mkdir(exist_ok=True)
        
        # Variables for application state
        self.monitoring = False
        self.log_file_path = None
        self.death_lines = []
        self.line_queue = queue.Queue()
        self.overlay_window = None
        self.overlay_locked = True
        self.monitor_thread = None
        
        # Use the statically loaded weapon IDs and location IDs
        self.weapon_ids = WEAPON_IDS
        self.location_ids = LOCATION_IDS
        
        # Overlay appearance settings with defaults
        self.overlay_settings = {
            "bg_color": "#000000",
            "text_color": "#FF0000",
            "font_size": 10,
            "opacity": 0.3,  # Set default to 0 for transparent background
            "width": 500,
            "height": 200,
            "position_x": 100,
            "position_y": 100,
            "max_lines": 5,  # Default number of lines to display
        }
        
        # Default game log paths to check
        self.default_game_log_paths = [
            Path(os.getenv('LOCALAPPDATA')) / "Star Citizen" / "Game.log",
            Path(os.getenv('PROGRAMFILES')) / "Roberts Space Industries" / "StarCitizen" / "LIVE" / "Game.log",
            Path.home() / "AppData" / "Local" / "Star Citizen" / "Game.log"
        ]
        
        # Load settings
        self.load_settings()
        
        # Setup UI
        self.setup_main_ui()
        
        # Setup system tray
        self.setup_system_tray()
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Check for Game.log file
        self.find_game_log()

    def load_settings(self):
        """Load settings from config file"""
        if self.config_file.exists():
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file)
                
                # Load log file path
                if 'General' in config and 'log_file_path' in config['General']:
                    path = config['General']['log_file_path']
                    if path and Path(path).exists():
                        self.log_file_path = Path(path)
                
                # Load overlay settings
                if 'Overlay' in config:
                    for key in self.overlay_settings:
                        if key in config['Overlay']:
                            # Convert values to appropriate types
                            if key in ['font_size', 'width', 'height', 'position_x', 'position_y', 'max_lines']:
                                self.overlay_settings[key] = int(config['Overlay'][key])
                            elif key == 'opacity':
                                self.overlay_settings[key] = float(config['Overlay'][key])
                            else:
                                self.overlay_settings[key] = config['Overlay'][key]
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save settings to config file"""
        try:
            config = configparser.ConfigParser()
            
            # General settings
            config['General'] = {
                'log_file_path': str(self.log_file_path) if self.log_file_path else ''
            }
            
            # Overlay settings
            config['Overlay'] = {k: str(v) for k, v in self.overlay_settings.items()}
            
            # Save to file
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def setup_main_ui(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(main_frame, text="Game Log Monitor", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="Game.log not found. Please select file location.")
        self.status_label.pack(pady=5, fill=tk.X)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10, fill=tk.X)
        
        # Toggle button for start/stop monitoring
        self.toggle_button = ttk.Button(buttons_frame, text="Start Monitoring", width=20, command=self.toggle_monitoring)
        self.toggle_button.pack(side=tk.LEFT, padx=5)
        
        # Select log file button
        self.select_button = ttk.Button(buttons_frame, text="Select Log File", width=20, command=self.select_log_file)
        self.select_button.pack(side=tk.LEFT, padx=5)
        
        # Settings button
        self.settings_button = ttk.Button(buttons_frame, text="Overlay Settings", width=20, command=self.show_settings)
        self.settings_button.pack(side=tk.LEFT, padx=5)
        
        # Display loaded weapon and location count
        weapon_count = len(self.weapon_ids)
        location_count = len(self.location_ids)
        
        status_text = ""
        if weapon_count > 0:
            status_text += f"Loaded {weapon_count} weapon IDs"
        if location_count > 0:
            if status_text:
                status_text += f", {location_count} location IDs"
            else:
                status_text += f"Loaded {location_count} location IDs"
                
        if status_text:
            self.status_label.config(text=status_text)

    def show_settings(self):
        """Show the settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Overlay Settings")
        settings_window.geometry("400x520")  # Increased height for additional settings
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create settings frame
        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text color
        ttk.Label(settings_frame, text="Text Color:").grid(row=0, column=0, sticky=tk.W, pady=5)
        text_color_frame = ttk.Frame(settings_frame)
        text_color_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        text_color_preview = tk.Label(text_color_frame, bg=self.overlay_settings["text_color"], width=3, height=1)
        text_color_preview.pack(side=tk.LEFT)
        
        ttk.Button(text_color_frame, text="Change", command=lambda: self.choose_color("text_color", text_color_preview)).pack(side=tk.LEFT, padx=5)
        
        # Background color
        ttk.Label(settings_frame, text="Background Color:").grid(row=1, column=0, sticky=tk.W, pady=5)
        bg_color_frame = ttk.Frame(settings_frame)
        bg_color_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        bg_color_preview = tk.Label(bg_color_frame, bg=self.overlay_settings["bg_color"], width=3, height=1)
        bg_color_preview.pack(side=tk.LEFT)
        
        ttk.Button(bg_color_frame, text="Change", command=lambda: self.choose_color("bg_color", bg_color_preview)).pack(side=tk.LEFT, padx=5)
        
        # Font size
        ttk.Label(settings_frame, text="Font Size:").grid(row=2, column=0, sticky=tk.W, pady=5)
        font_size_var = tk.IntVar(value=self.overlay_settings["font_size"])
        font_size_spinner = ttk.Spinbox(settings_frame, from_=8, to=20, textvariable=font_size_var, width=5)
        font_size_spinner.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Opacity
        ttk.Label(settings_frame, text="Opacity:").grid(row=3, column=0, sticky=tk.W, pady=5)
        opacity_frame = ttk.Frame(settings_frame)
        opacity_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        opacity_var = tk.DoubleVar(value=self.overlay_settings["opacity"])
        opacity_scale = ttk.Scale(opacity_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, 
                                 variable=opacity_var, length=150)
        opacity_scale.pack(side=tk.LEFT)
        
        opacity_label = ttk.Label(opacity_frame, text=f"{self.overlay_settings['opacity']:.1f}")
        opacity_label.pack(side=tk.LEFT, padx=5)
        
        # Update opacity label when scale changes
        def update_opacity_label(event):
            opacity_label.config(text=f"{opacity_var.get():.1f}")
        
        opacity_scale.bind("<Motion>", update_opacity_label)
        
        # Transparent background checkbox
        ttk.Label(settings_frame, text="Transparent Background:").grid(row=4, column=0, sticky=tk.W, pady=5)
        transparent_frame = ttk.Frame(settings_frame)
        transparent_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        transparent_var = tk.BooleanVar(value=(self.overlay_settings["opacity"] == 0))
        transparent_check = ttk.Checkbutton(transparent_frame, variable=transparent_var)
        transparent_check.pack(side=tk.LEFT)
        
        # Help info
        help_label = ttk.Label(settings_frame, 
                              text="Note: With transparent background, make sure\ntext color differs from background color.",
                              font=("Arial", 8), foreground="gray")
        help_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Link transparent checkbox with opacity slider
        def update_transparency():
            if transparent_var.get():
                opacity_var.set(0.0)
                opacity_label.config(text="0.0")
                opacity_scale.state(['disabled'])
                help_label.configure(foreground="black")
            else:
                if opacity_var.get() == 0.0:
                    opacity_var.set(0.8)
                    opacity_label.config(text="0.8")
                opacity_scale.state(['!disabled'])
                help_label.configure(foreground="gray")
        
        transparent_check.config(command=update_transparency)
        
        # Initialize state based on current opacity
        if transparent_var.get():
            opacity_scale.state(['disabled'])
            help_label.configure(foreground="black")
        
        # Width and height
        ttk.Label(settings_frame, text="Width:").grid(row=6, column=0, sticky=tk.W, pady=5)
        width_var = tk.IntVar(value=self.overlay_settings["width"])
        width_spinner = ttk.Spinbox(settings_frame, from_=200, to=800, textvariable=width_var, width=5)
        width_spinner.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(settings_frame, text="Height:").grid(row=7, column=0, sticky=tk.W, pady=5)
        height_var = tk.IntVar(value=self.overlay_settings["height"])
        height_spinner = ttk.Spinbox(settings_frame, from_=100, to=600, textvariable=height_var, width=5)
        height_spinner.grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Maximum lines to display
        ttk.Label(settings_frame, text="Max Death Lines:").grid(row=8, column=0, sticky=tk.W, pady=5)
        max_lines_var = tk.IntVar(value=self.overlay_settings["max_lines"])
        max_lines_spinner = ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=max_lines_var, width=5)
        max_lines_spinner.grid(row=8, column=1, sticky=tk.W, pady=5)
                
        # Buttons
        buttons_frame = ttk.Frame(settings_window)
        buttons_frame.pack(pady=10)
        
        # Save button
        def save_settings():
            # Update settings
            self.overlay_settings["font_size"] = font_size_var.get()
            
            # Handle transparent background
            if transparent_var.get():
                self.overlay_settings["opacity"] = 0.0
                # Make sure text color is different from background
                self.ensure_different_colors()
            else:
                self.overlay_settings["opacity"] = opacity_var.get()
                
            self.overlay_settings["width"] = width_var.get()
            self.overlay_settings["height"] = height_var.get()
            self.overlay_settings["max_lines"] = max_lines_var.get()
            
            # Apply settings to overlay if it exists
            if self.overlay_window:
                self.apply_overlay_settings()
            
            # Save settings
            self.save_settings()
            
            # Close settings window
            settings_window.destroy()
        
        ttk.Button(buttons_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)

    def ensure_different_colors(self):
        """Ensure text and background colors are different to prevent text from disappearing with transparency"""
        if self.overlay_settings["text_color"] == self.overlay_settings["bg_color"]:
            # Default to bright red text if text and background colors are the same
            self.overlay_settings["text_color"] = "#FF0000"
            
    def choose_color(self, setting_name, preview_label):
        """Show color chooser dialog and update settings"""
        color = colorchooser.askcolor(initialcolor=self.overlay_settings[setting_name])[1]
        if color:
            self.overlay_settings[setting_name] = color
            preview_label.config(bg=color)
            
            # If we're selecting background color and transparency is enabled, 
            # make sure text is a different color
            if setting_name == "bg_color" and self.overlay_settings["opacity"] == 0:
                self.ensure_different_colors()
                
            # If we're selecting text color, make sure it's different from background 
            # if transparency is enabled
            if setting_name == "text_color" and self.overlay_settings["opacity"] == 0:
                self.ensure_different_colors()

    def apply_overlay_settings(self):
        """Apply overlay settings to the window"""
        if not self.overlay_window:
            return
            
        # Remember if the window was visible
        was_visible = self.overlay_window.winfo_viewable()
            
        # Apply settings
        self.overlay_window.configure(bg=self.overlay_settings["bg_color"])
        
        # Set window transparency
        self.overlay_window.attributes("-alpha", 1.0 if self.overlay_settings["opacity"] == 0 else self.overlay_settings["opacity"])
        
        # Make background transparent if opacity is set to 0
        if self.overlay_settings["opacity"] == 0:
            # On Windows, we can use transparentcolor to make the background transparent
            # But we need to ensure text color is different from background color
            if self.overlay_settings["text_color"] == self.overlay_settings["bg_color"]:
                # If colors are the same, slightly modify the background color
                bg_color = self.overlay_settings["bg_color"]
                # Parse the hex color and modify it slightly
                r = int(bg_color[1:3], 16)
                g = int(bg_color[3:5], 16)
                b = int(bg_color[5:7], 16)
                # Adjust one component to make it different
                r = max(0, r - 1) if r > 0 else 1
                adjusted_bg = f"#{r:02x}{g:02x}{b:02x}"
                self.overlay_window.configure(bg=adjusted_bg)
                
            # Set the transparentcolor attribute
            self.overlay_window.attributes("-transparentcolor", self.overlay_settings["bg_color"])
        else:
            # Remove transparent color attribute if not needed
            self.overlay_window.attributes("-transparentcolor", "")
        
        # Update geometry
        width = self.overlay_settings["width"]
        height = self.overlay_settings["height"]
        x = self.overlay_settings["position_x"]
        y = self.overlay_settings["position_y"]
        self.overlay_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Update text widget with improved font settings
        self.death_text.configure(
            bg=self.overlay_settings["bg_color"],
            fg=self.overlay_settings["text_color"],
            font=("Consolas", self.overlay_settings["font_size"], "bold"),
            insertbackground=self.overlay_settings["text_color"]
        )
        
        # Get base font
        text_color = self.overlay_settings["text_color"]
        base_font = ("Consolas", self.overlay_settings["font_size"])
        
        # Update all the text tags with new font sizes and colors
        self.death_text.tag_configure("death_line", 
                                     foreground=text_color,
                                     font=(base_font[0], base_font[1], "bold"))
        
        # Update component tags 
        self.death_text.tag_configure("time_tag", 
                                     foreground="#AAAAAA",
                                     font=base_font)
        
        self.death_text.tag_configure("player_tag", 
                                     foreground="#00CCFF",
                                     font=(base_font[0], base_font[1], "bold"))
        
        self.death_text.tag_configure("symbol_tag", 
                                     foreground="#FFFFFF",
                                     font=base_font)
        
        self.death_text.tag_configure("killer_tag", 
                                     foreground="#FF3333", 
                                     font=(base_font[0], base_font[1], "bold"))
        
        self.death_text.tag_configure("weapon_tag", 
                                     foreground="#FFCC00",
                                     font=base_font)
        
        self.death_text.tag_configure("damage_tag", 
                                     foreground="#FF9900",
                                     font=base_font)
                                     
        self.death_text.tag_configure("location_tag", 
                                     foreground="#33CC33",
                                     font=base_font)
        
        # Preserve border based on lock state
        if not self.overlay_locked:
            self.overlay_window.configure(highlightbackground="#00FF00", highlightthickness=5)
        else:
            self.overlay_window.configure(highlightbackground="#000000", highlightthickness=0)
        
        # Make sure window state is preserved
        if was_visible and not self.overlay_window.winfo_viewable():
            self.overlay_window.deiconify()
            self.root.update()

    def setup_system_tray(self):
        # Create icon image
        icon_image = self.create_icon_image()
        
        # Create system tray menu
        menu = pystray.Menu(
            pystray.MenuItem('Show', self.show_app, default=True),
            pystray.MenuItem('Toggle Monitoring', self.toggle_monitoring),
            pystray.MenuItem('Toggle Overlay Lock', self.toggle_overlay_lock, checked=lambda _: self.overlay_locked),
            pystray.MenuItem('Exit', self.exit_app)
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon("GameLogMonitor", icon_image, "Game Log Monitor", menu)
        
        # Start tray icon in a separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def create_icon_image(self):
        # Try to load existing icon file
        icon_path = Path("app_icon.png")
        if icon_path.exists():
            try:
                return Image.open(icon_path)
            except Exception:
                pass
                
        # If loading fails, create a simple icon
        image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw icon background
        draw.rectangle([0, 0, 63, 63], fill=(50, 50, 100, 200), outline=(200, 200, 200))
        
        # Add text
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            
        draw.text((15, 15), "GLM", fill=(200, 200, 200), font=font)
        
        return image
        
    def find_game_log(self):
        # If we already have a path from settings and it exists, use it
        if self.log_file_path and self.log_file_path.exists():
            self.status_label.config(text=f"Found Game.log: {self.log_file_path}")
            self.toggle_button.config(state=tk.NORMAL)
            return
            
        # Check common locations for Game.log
        for path in self.default_game_log_paths:
            if path.exists():
                self.log_file_path = path
                self.status_label.config(text=f"Found Game.log: {path}")
                self.toggle_button.config(state=tk.NORMAL)
                # Save the found path
                self.save_settings()
                return
                
        # If not found, prompt the user
        self.status_label.config(text="Game.log not found. Please select file location.")
        self.toggle_button.config(state=tk.DISABLED)

    def select_log_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Game.log File",
            filetypes=[("Log Files", "*.log"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.log_file_path = Path(file_path)
            self.status_label.config(text=f"Selected: {self.log_file_path}")
            self.toggle_button.config(state=tk.NORMAL)
            # Save the selected path
            self.save_settings()

    def toggle_monitoring(self):
        if self.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        if not self.log_file_path or not self.log_file_path.exists():
            messagebox.showerror("Error", "Game.log file not found. Please select a valid file.")
            return
            
        self.monitoring = True
        self.toggle_button.config(text="Stop Monitoring")
        self.status_label.config(text=f"Monitoring: {self.log_file_path}")
        
        
        # Create overlay window if it doesn't exist
        if not self.overlay_window:
            self.create_overlay_window()
        
        # Make sure overlay is visible
        if self.overlay_window:
            self.overlay_window.deiconify()
            self.apply_overlay_settings()
            # Process events to ensure window is shown
            self.root.update()
            
            # Schedule visibility check
            self.root.after(500, self.check_overlay_visibility)
            
        # Start monitoring thread if not already running
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self.monitor_log_file, daemon=True)
            self.monitor_thread.start()
            
        # Start processing queue in a separate thread
        threading.Thread(target=self.process_queue, daemon=True).start()

    def stop_monitoring(self):
        self.monitoring = False
        self.toggle_button.config(text="Start Monitoring")
        self.status_label.config(text=f"Monitoring stopped. Log file: {self.log_file_path}")
        
        # Hide overlay window
        if self.overlay_window:
            # Save current position before hiding
            self.overlay_settings["position_x"] = self.overlay_window.winfo_x()
            self.overlay_settings["position_y"] = self.overlay_window.winfo_y()
            self.save_settings()
            
            # Hide window
            self.overlay_window.withdraw()

    def create_overlay_window(self):
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.title("Death Feed Overlay")
        
        # Set initial position using settings values
        width = self.overlay_settings["width"]
        height = self.overlay_settings["height"]
        x = self.overlay_settings["position_x"]
        y = self.overlay_settings["position_y"]
        self.overlay_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Always on top and remove window decorations
        self.overlay_window.attributes("-topmost", True)
        self.overlay_window.overrideredirect(True)
        
        # Set initial alpha to 1 to ensure text is visible
        # We'll set proper transparency in apply_overlay_settings
        self.overlay_window.attributes("-alpha", 1.0)
        
        # Ensure text color is different from background color if using transparency
        if self.overlay_settings["opacity"] == 0 and self.overlay_settings["text_color"] == self.overlay_settings["bg_color"]:
            # Default to bright red text if colors match
            self.overlay_settings["text_color"] = "#FF0000"
        
        # Create text widget for displaying death messages
        self.death_text = tk.Text(
            self.overlay_window, 
            height=5, 
            width=60, 
            wrap=tk.WORD,
            bg=self.overlay_settings["bg_color"], 
            fg=self.overlay_settings["text_color"], 
            font=("Consolas", self.overlay_settings["font_size"], "bold"),  # Add bold for better visibility
            borderwidth=0,  # Remove text widget border
            highlightthickness=0,  # Remove highlight border
            padx=5,  # Add small padding for text
            pady=5,  # Add small padding for text
            relief=tk.FLAT,  # Flat appearance
            insertbackground=self.overlay_settings["text_color"]  # Cursor color
        )
        
        # Configure text tags with improved appearance
        text_color = self.overlay_settings["text_color"]
        base_font = ("Consolas", self.overlay_settings["font_size"])
        
        # Standard death line tag (for backward compatibility)
        self.death_text.tag_configure("death_line", 
                                     foreground=text_color,
                                     font=(base_font[0], base_font[1], "bold"))
        
        # Configure component tags for better styling
        self.death_text.tag_configure("time_tag", 
                                     foreground="#AAAAAA",  # Gray for timestamps
                                     font=base_font)
        
        self.death_text.tag_configure("player_tag", 
                                     foreground="#00CCFF",  # Cyan for player
                                     font=(base_font[0], base_font[1], "bold"))
        
        self.death_text.tag_configure("symbol_tag", 
                                     foreground="#FFFFFF",  # White for symbols
                                     font=base_font)
        
        self.death_text.tag_configure("killer_tag", 
                                     foreground="#FF3333",  # Red for killer
                                     font=(base_font[0], base_font[1], "bold"))
        
        self.death_text.tag_configure("weapon_tag", 
                                     foreground="#FFCC00",  # Gold for weapon
                                     font=base_font)
        
        self.death_text.tag_configure("damage_tag", 
                                     foreground="#FF9900",  # Orange for damage type
                                     font=base_font)
                                     
        self.death_text.tag_configure("location_tag", 
                                     foreground="#33CC33",
                                     font=base_font)
        
        self.death_text.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)  # Remove padding
        self.death_text.config(state=tk.DISABLED)
        
        # Apply all settings (which will handle transparency properly)
        self.apply_overlay_settings()
        
        # Set up initial border based on lock state
        if not self.overlay_locked:
            self.overlay_window.configure(highlightbackground="#00FF00", highlightthickness=5)
        else:
            self.overlay_window.configure(highlightbackground="#000000", highlightthickness=0)
        
        # Mouse events for dragging
        self.overlay_window.bind("<ButtonPress-1>", self.start_drag)
        self.overlay_window.bind("<ButtonRelease-1>", self.stop_drag)
        self.overlay_window.bind("<B1-Motion>", self.do_drag)
        
        # Show initial message
        self.death_text.config(state=tk.NORMAL)
        self.death_text.insert(tk.END, "Waiting for death events...\n", "death_line")
        self.death_text.config(state=tk.DISABLED)
        
        # Initially hide the window
        # We'll show it in start_monitoring instead
        self.overlay_window.withdraw()

    def start_drag(self, event):
        if not self.overlay_locked:
            self.x = event.x
            self.y = event.y

    def stop_drag(self, event):
        if not self.overlay_locked:
            self.x = None
            self.y = None
            
            # Save position when drag stops
            self.overlay_settings["position_x"] = self.overlay_window.winfo_x()
            self.overlay_settings["position_y"] = self.overlay_window.winfo_y()
            self.save_settings()

    def do_drag(self, event):
        if not self.overlay_locked and self.x is not None and self.y is not None:
            dx = event.x - self.x
            dy = event.y - self.y
            x = self.overlay_window.winfo_x() + dx
            y = self.overlay_window.winfo_y() + dy
            self.overlay_window.geometry(f"+{x}+{y}")

    def toggle_overlay_lock(self):
        self.overlay_locked = not self.overlay_locked
        
        # Update status label to show locked/unlocked state
        if self.overlay_window:
            locked_status = "locked" if self.overlay_locked else "unlocked"
            self.status_label.config(text=f"Overlay {locked_status} - {'not draggable' if self.overlay_locked else 'draggable'}")
            
            # Add border when locked, remove when unlocked
            if not self.overlay_locked:
                self.overlay_window.configure(highlightbackground="#00FF00", highlightthickness=5)
            else:
                self.overlay_window.configure(highlightbackground="#000000", highlightthickness=0)

    def monitor_log_file(self):
        # Initial file position
        file_position = 0
        
        if self.log_file_path.exists():
            file_position = self.log_file_path.stat().st_size
        
        # Monitor loop
        while self.monitoring:
            try:
                if not self.log_file_path.exists():
                    self.status_label.config(text=f"Warning: Log file not found. Waiting for file to appear.")
                    time.sleep(1)
                    continue
                    
                # Check if file size has increased
                current_size = self.log_file_path.stat().st_size
                
                # Handle file truncation (e.g. if the file has been reset)
                if current_size < file_position:
                    file_position = 0
                
                if current_size > file_position:
                    try:
                        with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                            file.seek(file_position)
                            new_lines = file.readlines()
                            
                            # Filter lines containing Actor Death
                            # Both old and new formats are supported:
                            # Old: <Actor Death> at start of line
                            # New: Contains [Notice] <Actor Death> in the line
                            for line in new_lines:
                                if line.strip().startswith("<Actor Death>") or "<Actor Death>" in line:
                                    # Add to queue for processing
                                    self.line_queue.put(line.strip())
                                    
                        # Update file position
                        file_position = current_size
                    except PermissionError:
                        self.status_label.config(text=f"Permission denied while reading log file. Retrying...")
                        time.sleep(1)
                    except Exception as e:
                        self.status_label.config(text=f"Error reading log file: {e}")
                        time.sleep(1)
                    
                time.sleep(0.5)
                
            except Exception as e:
                self.status_label.config(text=f"Error monitoring log file: {e}")
                time.sleep(1)

    def process_queue(self):
        while self.monitoring:
            try:
                # Process any new items in the queue
                if not self.line_queue.empty():
                    line = self.line_queue.get(block=False)
                    
                    # Add to death lines list (keep only the specified number of lines)
                    self.death_lines.append(line)
                    if len(self.death_lines) > self.overlay_settings["max_lines"]:
                        self.death_lines.pop(0)
                        
                    # Update overlay text
                    self.update_overlay_text()                    
                
                time.sleep(0.1)
                
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing queue: {e}")
                time.sleep(0.1)

    def parse_death_line(self, line):
        """Parse a death line to extract useful information"""
        # Example of the new format:
        # <2025-04-25T18:02:17.301Z> [Notice] <Actor Death> CActor::Kill: 'Voisys' [201996731201] in zone 'AEGS_Gladius_2984839923201' 
        # killed by 'Lsync' [201964490332] using 'KLWE_LaserRepeater_S3_2984839923407' [Class unknown] with damage type 'VehicleDestruction' 
        # from direction x: 0.000000, y: 0.000000, z: 0.000000 [Team_ActorTech][Actor]
        
        # Extract timestamp if present
        timestamp_match = re.search(r"<(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)>", line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        # Extract actor (who died)
        actor_match = re.search(r"'([^']+)'\s+\[\d+\]", line)
        actor = actor_match.group(1) if actor_match else "Unknown"
        
        # Extract killed by
        killed_by_match = re.search(r"killed by '([^']+)'", line)
        killer = killed_by_match.group(1) if killed_by_match else "Unknown"
        
        # Extract weapon used (if available)
        weapon_match = re.search(r"using '([^']+)'", line)
        weapon = weapon_match.group(1) if weapon_match else None
        
        # Extract damage type
        damage_match = re.search(r"damage type '([^']+)'", line)
        damage = damage_match.group(1) if damage_match else "Unknown"
        
        # Extract location/zone
        location_match = re.search(r"in zone '([^']+)'", line)
        location = location_match.group(1) if location_match else "Unknown"
        
        return {
            "timestamp": timestamp,
            "actor": actor, 
            "killer": killer,
            "weapon": weapon,
            "damage": damage, 
            "location": location
        }

    def update_overlay_text(self):
        if not self.overlay_window:
            return
            
        # Update text widget with latest death lines
        self.death_text.config(state=tk.NORMAL)
        self.death_text.delete(1.0, tk.END)
        
        if not self.death_lines:
            # Show waiting message if no death lines are present
            self.death_text.insert(tk.END, "Waiting for death events...\n", "death_line")
        else:
            for line in self.death_lines:
                try:
                    # Try to parse the death line
                    data = self.parse_death_line(line)
                    
                    # Format timestamp for display
                    if data['timestamp']:
                        # Parse the ISO timestamp (which is in UTC)
                        utc_time = datetime.strptime(data['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        # Set the timezone to UTC
                        utc_time = utc_time.replace(tzinfo=timezone.utc)
                        # Convert to local timezone
                        system_tz = datetime.now().astimezone().tzinfo
                        local_time = utc_time.astimezone(system_tz)
                        # Format for display
                        display_time = local_time.strftime("%H:%M:%S")
                    else:
                        display_time = datetime.now().strftime("%H:%M:%S")
                                        
                    # Format the location info
                    location_name = self.get_location_name(data['location'])
                    
                    # Create a nicely formatted line with all available information
                    # Format: [TIME] PLAYER ☠ by KILLER (WEAPON) - DAMAGE_TYPE @ LOCATION
                    killer_text = f"{data['killer']}"
                    damage_text = f"{data['damage']}"
                    
                    # First insert timestamp in a neutral color
                    self.death_text.insert(tk.END, f"[{display_time}] ", "time_tag")
                    
                    # Insert player name
                    self.death_text.insert(tk.END, f"{data['actor']} ", "player_tag")
                    
                    # Insert killed by symbol
                    self.death_text.insert(tk.END, "☠ by ", "symbol_tag")
                    
                    # Insert killer name
                    self.death_text.insert(tk.END, f"{killer_text}", "killer_tag")
                    
                    # Insert weapon if available
                    if data['weapon']:
                        self.death_text.insert(tk.END, f" ({self.get_weapon_name(data['weapon'])})", "weapon_tag")
                    
                    # Insert damage type
                    self.death_text.insert(tk.END, f" - {damage_text}", "damage_tag")
                    
                    # Insert location if available and has a friendly name
                    if location_name and location_name != data['location']:
                        self.death_text.insert(tk.END, f" @ {location_name}", "location_tag")
                    
                    self.death_text.insert(tk.END, "\n")
                    
                except Exception as e:
                    # If parsing fails, just show the raw line with current timestamp
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.death_text.insert(tk.END, f"[{timestamp}] {line}\n", "death_line")
            
        self.death_text.config(state=tk.DISABLED)

    def show_app(self):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def on_close(self):
        # Hide main window instead of closing
        self.root.withdraw()

    def exit_app(self):
        # Stop monitoring before exit
        self.monitoring = False
        
        # Save settings
        if self.overlay_window and self.overlay_window.winfo_exists():
            # Save current position
            self.overlay_settings["position_x"] = self.overlay_window.winfo_x()
            self.overlay_settings["position_y"] = self.overlay_window.winfo_y()
        self.save_settings()
        
        # Stop tray icon
        self.tray_icon.stop()
        
        # Destroy windows
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
        self.root.destroy()
        
        # Exit application
        sys.exit(0)

    def check_overlay_visibility(self):
        """Periodically check if overlay window should be visible and is actually visible"""
        if self.monitoring and self.overlay_window:
            # If should be visible but isn't, force it to be visible
            if not self.overlay_window.winfo_viewable():
                self.overlay_window.deiconify()
                self.apply_overlay_settings()
                self.root.update()
                
            # Continue checking while monitoring is active
            if self.monitoring:
                self.root.after(2000, self.check_overlay_visibility)

    def get_weapon_name(self, weapon_id):
        """Get friendly weapon name from ID"""
        if not weapon_id:
            return None
            
        # Try direct match
        if weapon_id in self.weapon_ids:
            return self.weapon_ids[weapon_id]
            
        # Normalize ID for matching
        weapon_id_lower = weapon_id.lower()
        
        # Try lowercase match
        if weapon_id_lower in self.weapon_ids:
            return self.weapon_ids[weapon_id_lower]

        # Remove numeric suffix (e.g., '_200000056755', '_3013639860880')
        base_id = re.sub(r'_\d+$', '', weapon_id)
        if base_id in self.weapon_ids:
            return self.weapon_ids[base_id]
        
        return weapon_id
        
    def get_location_name(self, location_id):
        """Get friendly location name from ID"""
        if not location_id:
            return None
            
        # Try to match by exact ID first
        if location_id in self.location_ids:
            return self.location_ids[location_id]
            
        # Try to match by lowercase ID
        location_id_lower = location_id.lower()
        if location_id_lower in self.location_ids:
            return self.location_ids[location_id_lower]
        
        # Remove the numeric ID at the end (e.g., '2984839923407')
        clean_id = re.sub(r'_\d+$', '', location_id_lower)
        if clean_id in self.location_ids:
            return self.location_ids[clean_id]
            
        # Try to match by partial match (keywords in the ID)
        if len(self.location_ids) > 0:
            # Extract manufacturer prefix if present (AEGS_, DRAK_, MISC_, etc.)
            manufacturer_match = re.match(r'^([a-zA-Z]+)_', location_id_lower)
            if manufacturer_match:
                manufacturer = manufacturer_match.group(1).upper()
                # Look for keys with this manufacturer code
                for key, value in self.location_ids.items():
                    if key.upper().startswith(manufacturer):
                        # Check if the rest of the key matches parts of the location ID
                        key_parts = key.lower().split('_')[1:]  # Skip manufacturer
                        loc_parts = location_id_lower.split('_')[1:]  # Skip manufacturer
                        
                        if any(part in loc_parts for part in key_parts):
                            return value
            
            # Extract words from the location ID
            words = re.findall(r'[a-z]+', location_id_lower)
            
            # Look for location IDs that contain these words
            for key, value in self.location_ids.items():
                # Check if any meaningful words from the ID appear in the key
                for word in words:
                    # Skip very short words or common prefixes
                    if len(word) < 4 or word in ['the', 'and', 'ship', 'area', 'zone']:
                        continue
                    
                    # Make sure we don't skip important manufacturer names
                    if word in ['aegs', 'aegis', 'misc', 'drak', 'anvl']:
                        if word in key.lower():
                            return value
                        
                    if word in key.lower():
                        return value
        
        # If no match found, use a cleaned-up version of the original ID
        display_name = location_id
        
        # Format the ID nicer if it has underscores
        if '_' in display_name:
            # Remove the numeric part
            display_name = re.sub(r'_\d+$', '', display_name)
            # Replace underscores with spaces and capitalize words
            display_name = ' '.join(word.capitalize() for word in display_name.split('_'))
        
        return display_name

def main():
    # Set up exception handling to show error messages in dialogs
    def show_error(exc_type, exc_value, exc_traceback):
        import traceback
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        messagebox.showerror('Error', f'An unexpected error occurred:\n\n{error_msg}')
        
    # Handle uncaught exceptions
    sys.excepthook = show_error
    
    root = tk.Tk()
    # Apply ttk theme
    style = ttk.Style()
    if sys.platform.startswith('win'):
        # Use native Windows theme if available
        try:
            style.theme_use('vista')
        except:
            pass
    
    app = LogMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 