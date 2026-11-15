import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import menu
from settings import (
    HUD_BACKGROUND_IMAGE_PATH,
    HUD_COLOR_ACCENT,
    HUD_COLOR_BLACK,
    HUD_COLOR_BUTTON,
    HUD_COLOR_MUTED,
    HUD_COLOR_PANEL,
    HUD_COLOR_TEXT,
    HUD_COLOR_WHITE,
    HUD_FONT_PATH,
    HUD_FONT_SIZE,
    HUD_PADDING_H,
    HUD_PADDING_W,
    HUD_TIME_FORMAT,
    PREVIEW_HEIGHT,
    PREVIEW_ROTATE,
    PREVIEW_WIDTH,
)

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

        # Try to use a nice font, fall back to default if not available
        try:
            self.font = ImageFont.truetype(str(HUD_FONT_PATH), HUD_FONT_SIZE)
        except OSError:
            self.font = ImageFont.load_default()

    def update(self, camera, state):
        """
        Update the HUD overlay with current time, date, and camera metadata.
        Displays exposure time, analogue gain, white balance, capture resolution and format,
        the MENU button, and the touch menu when it is open.

        Args:
            camera: Picamera2 instance to set the overlay on
            state: CameraState (capture settings, menu open)
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
        except Exception:
            meta_str = "Waiting..."

        font = self.font

        # Calculate date text dimensions
        time_bbox = draw.textbbox((0, 0), time_str, font=font)
        time_width = time_bbox[2] - time_bbox[0]
        
        # Draw time
        time_x = self.preview_size[0] - time_width - HUD_PADDING_W
        time_y = HUD_PADDING_H
        draw.text((time_x, time_y), time_str, font=font, fill=HUD_COLOR_WHITE)
        
        # Calculate metadata text dimensions
        meta_bbox = draw.textbbox((0, 0), meta_str, font=font)
        meta_height = meta_bbox[3] - meta_bbox[1]

        # Draw Metadata
        draw.text((HUD_PADDING_W, self.preview_size[1] - meta_height - HUD_PADDING_H), meta_str, font=font, fill=HUD_COLOR_BLACK )

        # MENU button + capture settings, top left
        self._button(draw, menu.MENU_BUTTON, "MENU", HUD_COLOR_ACCENT, HUD_COLOR_BLACK)
        capture_str = f"{menu.resolution_label(state.capture_resolution)} {state.capture_format}"
        draw.text((menu.MENU_BUTTON[2] + 12, time_y), capture_str, font=font, fill=HUD_COLOR_WHITE)

        if state.menu_open:
            self._draw_menu(draw, state)

        # Update the overlay
        if PREVIEW_ROTATE:
            overlay_img = overlay_img.rotate(180)
        camera.set_overlay(np.array(overlay_img))

    def _button(self, draw, rect, label, fill, text_fill):
        draw.rounded_rectangle(rect, radius=10, fill=fill)
        draw.text(((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2), label, font=self.font, fill=text_fill, anchor="mm")

    def _draw_menu(self, draw, state):
        """The touch menu, from menu.buttons() (same rects as the hit test)."""
        draw.rounded_rectangle(menu.PANEL, radius=16, fill=HUD_COLOR_PANEL)
        x = menu.PANEL[0] + 16
        draw.text((x, menu.PANEL[1] + 12), "SETTINGS", font=self.font, fill=HUD_COLOR_TEXT)
        draw.text((x, menu.ROW_RESOLUTION_Y - 34), "RESOLUTION", font=self.font, fill=HUD_COLOR_MUTED)
        draw.text((x, menu.ROW_FORMAT_Y - 34), "FORMAT", font=self.font, fill=HUD_COLOR_MUTED)
        for rect, label, selected, _action in menu.buttons(state):
            if selected:
                self._button(draw, rect, label, HUD_COLOR_ACCENT, HUD_COLOR_PANEL)
            else:
                self._button(draw, rect, label, HUD_COLOR_BUTTON, HUD_COLOR_TEXT)
