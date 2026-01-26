import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from settings import *

class HUD:
    """Head-Up Display (HUD) controller for the camera overlay."""
    
    def __init__(self, width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT):
        """
        Initialize the HUD.
        
        Args:
            width: Width of the preview window
            height: Height of the preview window
        """
        self.preview_size = (width, height)
        self.overlay = None
        self.background_image = None
        
        # Load background image if configured
        if HUD_BACKGROUND_IMAGE_PATH:
            try:
                bg_path = Path(HUD_BACKGROUND_IMAGE_PATH)
                if bg_path.exists():
                    img = Image.open(bg_path).convert('RGBA')
                    # Resize to match preview size if needed
                    if img.size != self.preview_size:
                        img = img.resize(self.preview_size, Image.Resampling.LANCZOS)
                    self.background_image = img
                    print(f"Loaded HUD background from {bg_path}")
                else:
                    print(f"Warning: HUD background file not found: {bg_path}")
            except Exception as e:
                print(f"Error loading HUD background: {e}")
        
    def update(self, camera):
        """
        Update the HUD overlay with current time and date.
        
        Args:
            camera: Picamera2 instance to set the overlay on
        """
        # Create a transparent image for the overlay
        if self.background_image:
            overlay_img = self.background_image.copy()
        else:
            overlay_img = Image.new('RGBA', self.preview_size, (0, 0, 0, 0))
            
        draw = ImageDraw.Draw(overlay_img)
        
        # Get current date and time
        now = datetime.datetime.now()
        time_str = now.strftime(HUD_TIME_FORMAT)

        # Try getting metadata
        try:
            metadata = camera.capture_metadata()
            # Exposure is in microseconds, convert to ms for display
            exp_ms = metadata.get("ExposureTime", 0) / 1000 
            gain = metadata.get("AnalogueGain", 0)
            temp = metadata.get("ColourTemperature", 0)
            meta_str = f"Exp: {exp_ms:.1f}ms - Gain: {gain:.2f}x - WB: {temp:.0f}K"
        except Exception as e:
            meta_str = "Waiting..."
        
        # Try to use a nice font, fall back to default if not available
        try:
            font = ImageFont.truetype(HUD_FONT_PATH, HUD_FONT_SIZE)
        except:
            font = ImageFont.load_default()
        
        # Calculate date text dimensions
        time_bbox = draw.textbbox((0, 0), time_str, font=font)
        time_width = time_bbox[2] - time_bbox[0]
        
        # Draw time
        time_x = self.preview_size[0] - time_width - HUD_PADDING_W
        time_y = HUD_PADDING_H
        draw.text((time_x, time_y), time_str, font=font, fill=HUD_COLOR_TEXT)
        
        # Calculate metadata text dimensions
        meta_bbox = draw.textbbox((0, 0), meta_str, font=font)
        meta_height = meta_bbox[3] - meta_bbox[1]

        # Draw Metadata
        draw.text((HUD_PADDING_W, self.preview_size[1] - meta_height - HUD_PADDING_H), meta_str, font=font, fill=HUD_COLOR_TEXT )
        
        # Update the overlay
        if PREVIEW_ROTATE:
            overlay_img = overlay_img.rotate(180)
        camera.set_overlay(np.array(overlay_img))
