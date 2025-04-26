# Game Log Monitor

A Python application that monitors a game log file (Game.log) in real-time and displays death event messages in an overlay window.

## Features

- Real-time monitoring of Game.log file
- Filters and displays lines that start with `<Actor Death>`
- Supports both old and new log formats:
  - Old format: `<Actor Death> 'Player' [ID] in zone 'Location' killed by 'Killer' with damage type 'Type'`
  - New format: `<timestamp> [Notice] <Actor Death> CActor::Kill: 'Player' [ID] in zone 'Location' killed by 'Killer' [ID] using 'Weapon' [Class unknown] with damage type 'Type'...`
- Shows the last 5 death messages in an always-on-top overlay
- Draggable overlay window with lock/unlock functionality
- Simple toggle button for starting/stopping monitoring
- System tray integration for easy access
- Customizable overlay appearance (colors, size, font, opacity)
- Persistent settings between sessions

## Requirements

- Windows operating system
- Python 3.6 or higher
- Required packages:
  - tkinter (usually comes with Python)
  - pystray
  - pillow (PIL)

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python game_log_monitor.py
   ```

2. If the application doesn't automatically find Game.log, click "Select Log File" to locate it
3. Click "Start Monitoring" to begin monitoring and display the overlay
4. The overlay will show the most recent 5 death messages from the game
5. You can move the overlay by dragging it with your mouse (when unlocked)
6. Right-click the system tray icon to:
   - Show the main app window
   - Toggle monitoring
   - Toggle overlay lock (to enable/disable dragging)
   - Exit the application

## Testing

For testing purposes without an actual Game.log file, you can use the included test log generator:

```
python test_log_generator.py --path Game.log --duration 120 --interval 0.5
```

This will create a test Game.log file in the current directory and continuously update it with random entries, including `<Actor Death>` lines in both old and new formats. The parameters are:

- `--path` or `-p`: Where to create the log file (default: Game.log)
- `--duration` or `-d`: How long to run in seconds (default: 60)
- `--interval` or `-i`: Seconds between log entries (default: 1.0)

You can then point the Game Log Monitor to this test file for development and testing.

## Building an Executable

To create a standalone executable:

1. Run the setup script:
   ```
   python setup.py
   ```
   
This will create a standalone executable in the `dist` folder.

Alternatively, you can use PyInstaller directly:

```
pyinstaller --onefile --windowed --icon=app_icon.ico game_log_monitor.py
```

## License

This project is open-source and free to use. 