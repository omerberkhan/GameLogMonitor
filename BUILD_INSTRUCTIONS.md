# Building Game Log Monitor

This document provides instructions for building the Game Log Monitor application into a standalone executable.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Method 1: Using the Build Script (Recommended)

The easiest way to build the application is to use the included build script:

1. Open a command prompt in the project directory
2. Run the build script:
   ```
   build.bat
   ```
3. Wait for the build process to complete
4. The executable will be created in the `dist` folder

## Method 2: Manual Build

If you prefer to build manually:

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Run PyInstaller with the spec file:
   ```
   pyinstaller --clean GameLogMonitor.spec
   ```

3. The executable will be created in the `dist` folder

## Method 3: Using setup.py

An alternative method is to use the setup.py script:

1. Run the setup script:
   ```
   python setup.py
   ```

2. This will install dependencies and build the executable automatically
3. The executable will be created in the `dist` folder

## Troubleshooting

If you encounter the error "No module named 'pystray'" or similar errors:

1. Make sure you've installed all dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Try rebuilding with the `--clean` flag:
   ```
   pyinstaller --clean GameLogMonitor.spec
   ```

3. If the issue persists, try building with console output enabled to see detailed errors:
   ```
   pyinstaller --clean --console GameLogMonitor.spec
   ```

## Required Files

The following files should be present for the application to work properly:

- `game_log_monitor.py` - Main application code
- `weapon_ids.json` - Weapon ID mappings
- `location_ids.json` - Location ID mappings

These files will be automatically included in the build process. 