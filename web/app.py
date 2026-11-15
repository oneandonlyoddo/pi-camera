
import os
import threading
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify, request
from PIL import Image

import menu
from shared_state import is_valid
from settings import (
    COLOUR_TEMP_MAX,
    COLOUR_TEMP_MIN,
    GAIN_MAX,
    GAIN_MIN,
    JPG_EXTENSION,
    PHOTOS_DIR,
    THUMBNAIL_HEIGHT,
    THUMBNAIL_QUALITY,
    THUMBNAIL_WIDTH,
    THUMBNAILS_DIR,
)

app = Flask(__name__)
camera_state = None  # Global to hold the shared state
_thumbnail_lock = threading.Lock()

def init_app(shared_state):
    """
    Initialize the Flask app with the shared camera state.
    This must be called before starting the server.
    """
    global camera_state
    camera_state = shared_state

def generate_thumbnail_if_missing(filename):
    """
    Generate a thumbnail for an image if it doesn't exist yet.

    Args:
        filename: Name of the JPG file

    Returns:
        Path to the thumbnail file
    """
    if Path(filename).name != filename:  # bare names only: never read or write outside DCIM/ (R7)
        raise FileNotFoundError(filename)
    thumb_path = thumbnails_path / filename

    # One at a time: a parallel request must never see a half-written thumbnail (it is cached for a year)
    with _thumbnail_lock:
        if thumb_path.exists():
            return thumb_path

        original_path = photos_path / filename
        if not original_path.exists():
            raise FileNotFoundError(f"Original image not found: {filename}")

        try:
            with Image.open(original_path) as img:
                img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)  # keeps aspect ratio
                tmp = thumb_path.with_suffix(".tmp")
                img.save(tmp, "JPEG", quality=THUMBNAIL_QUALITY)
            os.replace(tmp, thumb_path)  # a crash mid-save never leaves a broken thumbnail
            print(f"Generated thumbnail on-demand: {thumb_path}")
            return thumb_path

        except Exception as e:
            print(f"Error generating thumbnail for {filename}: {e}")
            raise

# Absolute paths from settings.py (R4); module-level so tests can point them elsewhere
photos_path = PHOTOS_DIR
thumbnails_path = THUMBNAILS_DIR
thumbnails_path.mkdir(parents=True, exist_ok=True)  # DCIM/ too

# API key -> CameraState attribute. The API names predate the state names; keep both stable.
API_KEYS = {"gain": "analogue_gain", "color_temp": "colour_temperature", "resolution": "capture_resolution",
            "format": "capture_format", "preset": "preset"}
_API_KEY = {attr: key for key, attr in API_KEYS.items()}


@app.route('/')
def index():
    """Render the main gallery page."""
    return render_template(
        'index.html', gain_min=GAIN_MIN, gain_max=GAIN_MAX, temp_min=COLOUR_TEMP_MIN, temp_max=COLOUR_TEMP_MAX,
        # chip rows in touch-menu order: (title, API key, [(value, label)]), labels as on the Pi menu
        choices=[(title, _API_KEY[attr], [(v, menu.option_label(attr, v)) for v in values])
                 for title, attr, values in menu.categories()],
    )

@app.route('/api/photos')
def get_photos():
    """Return a list of photo filenames sorted by date (newest first)."""
    try:
        # Get all JPG files
        files = list(photos_path.glob(f"*{JPG_EXTENSION}"))
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        filenames = [f.name for f in files]
        print(f"Serving {len(filenames)} photos from {photos_path}")

        # Return list of filenames
        return jsonify(filenames)
    except Exception as e:
        print(f"Error in get_photos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/dcim/<path:filename>')
def serve_photo(filename):
    """Serve a photo from the DCIM directory with caching headers."""
    response = send_from_directory(photos_path, filename)
    # Cache photos for 1 year (they never change once created)
    response.cache_control.max_age = 31536000
    response.cache_control.public = True
    return response

@app.route('/dcim/thumbs/<path:filename>')
def serve_thumbnail(filename):
    """Serve a thumbnail from the thumbnails directory with caching headers.
    Generates thumbnail on-demand if it doesn't exist yet."""
    try:
        # Generate thumbnail if it doesn't exist
        generate_thumbnail_if_missing(filename)

        # Serve the thumbnail
        response = send_from_directory(thumbnails_path, filename)
        # Cache thumbnails for 1 year (they never change once created)
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
        return response
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        print(f"Error serving thumbnail {filename}: {e}")
        return jsonify({"error": "Failed to generate thumbnail"}), 500

@app.route('/api/trigger', methods=['POST'])
def trigger_shutter():
    """Trigger the camera shutter."""
    camera_state.request_shutter()
    return jsonify({"status": "ok", "message": "Shutter requested"})

def settings_json():
    return {key: getattr(camera_state, attr) for key, attr in API_KEYS.items()}  # tuples become JSON lists


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update camera settings (gain, color temp, resolution, format, preset)."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "No data provided"}), 400

    updates = {}
    for key, attr in API_KEYS.items():
        if key in data:
            value = tuple(data[key]) if isinstance(data[key], list) else data[key]  # JSON has no tuples
            if not is_valid(attr, value):  # rejects bools, NaN, inf, out of range (R7)
                return jsonify({"status": "error", "message": f"invalid {key}: {data[key]!r}"}), 400
            updates[attr] = value
    if "analogue_gain" in updates:
        updates["analogue_gain"] = float(updates["analogue_gain"])
    if "colour_temperature" in updates:
        updates["colour_temperature"] = int(updates["colour_temperature"])

    # Only store once every value is valid, so a bad request changes nothing
    for attr, value in updates.items():
        setattr(camera_state, attr, value)

    return jsonify({"status": "ok", **settings_json()})


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current camera settings."""
    return jsonify(settings_json())
