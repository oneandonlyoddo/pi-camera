#!/usr/bin/python3

import time
import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from picamera2 import Picamera2, Preview
import libcamera

from settings import (
    
    PREVIEW_WIDTH,
    PREVIEW_HEIGHT,
    PREVIEW_WINDOW_X,
    PREVIEW_WINDOW_Y,
    HUD_UPDATE_INTERVAL,
    HUD_FONT_PATH_LARGE,
    HUD_FONT_PATH_SMALL,
    HUD_FONT_SIZE_LARGE,
    HUD_FONT_SIZE_SMALL,
    HUD_DATE_FORMAT,
    HUD_TIME_FORMAT,
    HUD_PADDING,
    HUD_BACKGROUND_PADDING,
    HUD_TEXT_SPACING,
    HUD_COLOR_BACKGROUND,
    HUD_COLOR_TIME_TEXT,
    HUD_COLOR_DATE_TEXT,
    HUD_COLOR_SHADOW,
    HUD_SHADOW_OFFSET
)


preview_size = (PREVIEW_WIDTH, PREVIEW_HEIGHT)
picam2 = Picamera2()
picam2.start_preview(
    Preview.DRM,
    x=PREVIEW_WINDOW_X,
    y=PREVIEW_WINDOW_Y,
    width=PREVIEW_WIDTH,
    height=PREVIEW_HEIGHT
)

preview_config = picam2.create_preview_configuration(main={"size": (PREVIEW_WIDTH, PREVIEW_HEIGHT)})
preview_config["transform"] = libcamera.Transform(hflip=1, vflip=1)
preview_config["format"] = "YUV420"

picam2.configure(preview_config)



picam2.start()
time.sleep(1)


try:
    while True:
        """Update the HUD overlay with current time and date."""
        # Create a transparent image for the overlay
        overlay_img = Image.new('RGBA', preview_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)
        
        # Get current date and time
        now = datetime.datetime.now()
        date_str = now.strftime(HUD_DATE_FORMAT)
        time_str = now.strftime(HUD_TIME_FORMAT)
        
        # Try to use a nice font, fall back to default if not available
        try:
            font_large = ImageFont.truetype(HUD_FONT_PATH_LARGE, HUD_FONT_SIZE_LARGE)
            font_small = ImageFont.truetype(HUD_FONT_PATH_SMALL, HUD_FONT_SIZE_SMALL)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Calculate time text dimensions and position (top-right corner)
        time_bbox = draw.textbbox((0, 0), time_str, font=font_large)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = preview_size[0] - time_width - HUD_PADDING
        time_y = HUD_PADDING
        
        # Calculate date text dimensions
        date_bbox = draw.textbbox((0, 0), date_str, font=font_small)
        date_width = date_bbox[2] - date_bbox[0]
        date_height = date_bbox[3] - date_bbox[1]
        time_height = time_bbox[3] - time_bbox[1]
        
        # Calculate background rectangle dimensions to fit both time and date
        bg_width = max(time_width, date_width) + (HUD_BACKGROUND_PADDING * 2)
        bg_height = time_height + date_height + (HUD_BACKGROUND_PADDING * 3)
        bg_x = preview_size[0] - bg_width - HUD_PADDING + HUD_BACKGROUND_PADDING
        bg_y = HUD_PADDING - HUD_BACKGROUND_PADDING
        
        # Draw semi-transparent background for better readability
        
        draw.rectangle(
            [bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
            fill=HUD_COLOR_BACKGROUND
        )
        
        # Draw time text with shadow for better visibility
        draw.text(
            (time_x + HUD_SHADOW_OFFSET, time_y + HUD_SHADOW_OFFSET),
            time_str,
            font=font_large,
            fill=HUD_COLOR_SHADOW
        )
        draw.text((time_x, time_y), time_str, font=font_large, fill=HUD_COLOR_TIME_TEXT)
        
        # Draw date (smaller text, below time)
        date_x = preview_size[0] - date_width - HUD_PADDING
        date_y = time_y + time_height + HUD_TEXT_SPACING
        draw.text(
            (date_x + HUD_SHADOW_OFFSET, date_y + HUD_SHADOW_OFFSET),
            date_str,
            font=font_small,
            fill=HUD_COLOR_SHADOW
        )
        draw.text((date_x, date_y), date_str, font=font_small, fill=HUD_COLOR_DATE_TEXT)
        
        # Update the overlay
        picam2.set_overlay(np.array(overlay_img.rotate(180)))
        time.sleep(1)
        
except KeyboardInterrupt:
    picam2.stop_preview()
    picam2.stop()
    picam2.close()
    #tcflush(stdin, TCIOFLUSH)