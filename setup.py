import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing required packages...")
    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Required packages installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
            sys.exit(1)
    else:
        print("requirements.txt not found. Installing essential packages...")
        # Install required packages directly
        packages = ["pystray", "pillow", "pyinstaller"]
        for package in packages:
            try:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError as e:
                print(f"Error installing {package}: {e}")
                sys.exit(1)

def create_executable():
    """
    Build an executable for the Game Log Monitor application using PyInstaller
    """
    print("Building Game Log Monitor executable...")
    
    # Install dependencies first
    install_requirements()
    
    # Create icons if they don't exist
    print("Checking and creating icons...")
    try:
        import create_icon
        create_icon.create_app_icons()
    except Exception as e:
        print(f"Error creating icons: {e}")
        print("Continuing without custom icons...")

    # Define icon paths
    app_icon_path = Path("static") / "app_icon.ico"      # For executable
    window_icon_path = Path("static") / "window_icon.ico" # For windows
    tray_icon_path = Path("static") / "tray_icon.png"    # For system tray
    
    # Additional data files to include
    data_files = [
        ("weapon_ids.json", "."),
        ("location_ids.json", "."),
    ]

    # Add icon files from static folder
    icon_files_to_bundle = [
        (app_icon_path, "app_icon.ico"),
        (window_icon_path, "window_icon.ico"),
        (tray_icon_path, "tray_icon.png"),
        (Path("static") / "window_icon.png", "window_icon.png"),  # Optional, if it exists
    ]

    for icon_path_obj, icon_name in icon_files_to_bundle:
        if icon_path_obj.exists():
            data_files.append((str(icon_path_obj), "static"))
        else:
            print(f"Warning: {icon_name} not found in static folder")

    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "KillCollector",
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
    ]

    # Add data files
    for src, dest in data_files:
        if Path(src).exists():
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])

    # Add icon for the executable itself (app_icon.ico)
    if app_icon_path.exists():
        cmd.extend(["--icon", str(app_icon_path)])
    else:
        print("Warning: app_icon.ico not found, executable will use default icon")
    
    # Add main script
    cmd.append("game_log_monitor.py")
    
    # Run PyInstaller
    try:
        subprocess.check_call(cmd)
        print("\nBuild successful!")
        print(f"Executable created: {os.path.abspath('dist/KillCollector.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_executable() 