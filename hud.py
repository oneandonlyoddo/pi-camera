import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import menu
from settings import (
    HUD_COLOR_ACCENT,
    HUD_COLOR_DARK,
    HUD_COLOR_GREY,
    HUD_COLOR_LIGHT,
    HUD_BAR_HEIGHT,
    HUD_FONT_PATH,
    HUD_FONT_SIZE,
    HUD_GRID_WIDTH,
    HUD_PADDING_W,
    HUD_TIME_FORMAT,
    PREVIEW_HEIGHT,
    PREVIEW_ROTATE,
    PREVIEW_WIDTH,
)


def base_image(size):
    """The static HUD: rule-of-thirds grid, then the top and bottom bars over it. Solid colours only."""
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))  # fully transparent = the preview shows through
    draw = ImageDraw.Draw(img)
    for x in (w // 3, 2 * w // 3):
        draw.line([(x, 0), (x, h)], fill=HUD_COLOR_LIGHT, width=HUD_GRID_WIDTH)
    for y in (h // 3, 2 * h // 3):
        draw.line([(0, y), (w, y)], fill=HUD_COLOR_LIGHT, width=HUD_GRID_WIDTH)
    draw.rectangle((0, 0, w, HUD_BAR_HEIGHT - 1), fill=HUD_COLOR_DARK)
    draw.rectangle((0, h - HUD_BAR_HEIGHT, w, h), fill=HUD_COLOR_DARK)
    return img


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
        self.base = base_image(self.preview_size)  # static: drawn once, copied per update

        # Try to use a nice font, fall back to default if not available
        try:
            self.font = ImageFont.truetype(str(HUD_FONT_PATH), HUD_FONT_SIZE)
        except OSError:
            self.font = ImageFont.load_default()

    def update(self, camera, state):
        """
        Update the HUD overlay: grid, capture resolution and format, preset, time and date (top),
        exposure, gain and white balance (bottom left), the MENU button (bottom right),
        and the touch menu when it is open.

        Args:
            camera: Picamera2 instance to set the overlay on
            state: CameraState (capture settings, menu open)
        """
        overlay_img = self.base.copy()
        draw = ImageDraw.Draw(overlay_img)
        font = self.font
        width, height = self.preview_size

        try:
            metadata = camera.capture_metadata()
            exp_ms = metadata.get("ExposureTime", 0) / 1000  # microseconds -> ms
            gain = metadata.get("AnalogueGain", 0)
            temp = metadata.get("ColourTemperature", 0)
            meta_str = f"Exp: {exp_ms:.1f}ms - Gain: {gain:.2f}x - WB: {temp:.0f}K"
        except Exception:
            meta_str = "Waiting..."

        if state.menu_open:  # the menu replaces the data fields, so none peek out around the panel
            self._draw_menu(draw, state)
            self._show(camera, overlay_img)
            return

        # Top bar: capture settings left, time right
        top_y = HUD_BAR_HEIGHT / 2
        capture_str = f"{menu.resolution_label(state.capture_resolution)} {state.capture_format}"
        draw.text((HUD_PADDING_W, top_y), capture_str, font=font, fill=HUD_COLOR_LIGHT, anchor="lm")
        time_str = datetime.datetime.now().strftime(HUD_TIME_FORMAT)
        draw.text((width - HUD_PADDING_W, top_y), time_str, font=font, fill=HUD_COLOR_LIGHT, anchor="rm")
        if state.preset:  # none: the centre stays empty
            draw.text((width / 2, top_y), state.preset, font=font, fill=HUD_COLOR_LIGHT, anchor="mm")

        # Bottom bar: data fields left, MENU right
        bottom_y = height - HUD_BAR_HEIGHT / 2
        draw.text((HUD_PADDING_W, bottom_y), meta_str, font=font, fill=HUD_COLOR_LIGHT, anchor="lm")
        self._button(draw, menu.MENU_BUTTON, "MENU", HUD_COLOR_ACCENT, HUD_COLOR_DARK)
        self._show(camera, overlay_img)

    def _show(self, camera, overlay_img):
        if PREVIEW_ROTATE:
            overlay_img = overlay_img.rotate(180)
        camera.set_overlay(np.array(overlay_img))

    def _button(self, draw, rect, label, fill, text_fill, outline=None):
        draw.rounded_rectangle(rect, radius=10, fill=fill, outline=outline, width=2)
        draw.text(((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2), label, font=self.font, fill=text_fill, anchor="mm")

    def _draw_menu(self, draw, state):
        """The touch menu, from menu.buttons() (same rects as the hit test)."""
        draw.rectangle(menu.PANEL, fill=HUD_COLOR_DARK)
        x = menu.PANEL[0] + 16
        draw.text((x, menu.PANEL[1] + 12), "SETTINGS", font=self.font, fill=HUD_COLOR_LIGHT)
        draw.text((x, menu.ROW_RESOLUTION_Y - 34), "RESOLUTION", font=self.font, fill=HUD_COLOR_GREY)
        draw.text((x, menu.ROW_FORMAT_Y - 34), "FORMAT", font=self.font, fill=HUD_COLOR_GREY)
        draw.text((x, menu.ROW_PRESET_Y - 34), "PRESET", font=self.font, fill=HUD_COLOR_GREY)
        for rect, label, selected, _action in menu.buttons(state):
            if selected:
                self._button(draw, rect, label, HUD_COLOR_ACCENT, HUD_COLOR_DARK)
            else:
                self._button(draw, rect, label, HUD_COLOR_DARK, HUD_COLOR_LIGHT, outline=HUD_COLOR_GREY)
