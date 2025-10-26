from PIL import Image, ImageDraw, ImageFont

def create_app_icon():
    # Create a new image with transparent background
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle for the background
    draw.ellipse((10, 10, 246, 246), fill=(50, 50, 100, 255), outline=(200, 200, 255, 255), width=4)
    
    # Draw a smaller inner circle
    draw.ellipse((40, 40, 216, 216), fill=(40, 40, 80, 255))
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except IOError:
        try:
            # Try a more generic approach
            font = ImageFont.load_default()
        except:
            print("Couldn't load font, using default")
            font = None
    
    text = "GLM"
    if font:
        # Get text dimensions to center it
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        text_x = (256 - text_width) // 2
        text_y = (256 - text_height) // 2
        
        draw.text((text_x, text_y), text, font=font, fill=(200, 200, 255, 255))
    else:
        # Fallback if font loading fails
        draw.text((90, 100), text, fill=(200, 200, 255, 255))
    
    # Save the icon in multiple formats
    img.save("static/app_icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])
    img.save("static/app_icon.png")
    
    print("Icon created successfully: app_icon.ico and app_icon.png")

if __name__ == "__main__":
    create_app_icon() 