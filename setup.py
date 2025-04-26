import os
import sys
import subprocess
from pathlib import Path

def create_executable():
    """
    Build an executable for the Game Log Monitor application using PyInstaller
    """
    print("Building Game Log Monitor executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create icon if it doesn't exist
    icon_path = Path("app_icon.ico")
    if not icon_path.exists():
        try:
            print("Creating application icon...")
            import create_icon
            create_icon.create_app_icon()
        except Exception as e:
            print(f"Error creating icon: {e}")
            print("Continuing without custom icon...")
            icon_path = None
    
    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "GameLogMonitor"
    ]
    
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