from PIL import Image
import os

def convert_png_to_ico(png_filename, ico_filename):
    """Convert a PNG file to ICO format with multiple sizes"""
    png_path = os.path.join("static", png_filename)
    ico_path = os.path.join("static", ico_filename)

    if not os.path.exists(png_path):
        print(f"Warning: {png_path} not found! Skipping...")
        return False

    try:
        # Load the existing PNG image
        img = Image.open(png_path)

        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Save as ICO with multiple sizes for better quality at different resolutions
        img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

        print(f"[OK] Created {ico_filename} from {png_filename}")
        return True

    except Exception as e:
        print(f"[ERROR] Converting {png_filename}: {e}")
        return False

def create_app_icons():
    """Convert all PNG icons to ICO format for the application"""
    print("Converting PNG icons to ICO format...\n")

    # Define icon conversions
    icons = [
        ("window_icon.png", "window_icon.ico"),  # For all application windows
        ("app_icon.png", "app_icon.ico"),        # For executable
    ]

    success_count = 0
    for png_file, ico_file in icons:
        if convert_png_to_ico(png_file, ico_file):
            success_count += 1

    # Check for tray icon (doesn't need ICO conversion, used as PNG)
    tray_png = os.path.join("static", "tray_icon.png")
    if os.path.exists(tray_png):
        print("[OK] Found tray_icon.png (used directly for system tray)")
        success_count += 1
    else:
        print("[WARN] tray_icon.png not found!")

    print(f"\nIcon conversion complete: {success_count}/{len(icons) + 1} icons ready")
    return success_count > 0

if __name__ == "__main__":
    create_app_icons() 