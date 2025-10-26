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
    
    # Create icon if it doesn't exist
    icon_path = Path("static/app_icon.ico")
    if not icon_path.exists():
        try:
            print("Creating application icon...")
            import create_icon
            create_icon.create_app_icon()
        except Exception as e:
            print(f"Error creating icon: {e}")
            print("Continuing without custom icon...")
            icon_path = None
    
    # Additional data files to include
    data_files = [
        ("weapon_ids.json", "."),
        ("location_ids.json", "."),
    ]
    
    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "GameLogMonitor",
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
    ]
    
    # Add data files
    for src, dest in data_files:
        if Path(src).exists():
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])
    
    # Add icon if available
    if icon_path and icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Add main script
    cmd.append("game_log_monitor.py")
    
    # Run PyInstaller
    try:
        subprocess.check_call(cmd)
        print("\nBuild successful!")
        print(f"Executable created: {os.path.abspath('dist/GameLogMonitor.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_executable() 