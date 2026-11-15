
import os
import sys
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify, request
from PIL import Image

# Add parent directory to path to allow importing settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import presets  # noqa: E402
from menu import resolution_label, value_label  # noqa: E402
from shared_state import is_valid  # noqa: E402
from settings import (  # noqa: E402 (needs the sys.path line above)
    CAPTURE_FORMATS,
    CAPTURE_RESOLUTIONS,
    COLOUR_TEMP_MAX,
    GAIN_STEPS,
    COLOUR_TEMP_MIN,
    WB_PRESETS,
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

    # If thumbnail already exists, return it
    if thumb_path.exists():
        return thumb_path

    # Generate thumbnail from original image
    original_path = photos_path / filename
    if not original_path.exists():
        raise FileNotFoundError(f"Original image not found: {filename}")

    try:
        # Open the original image
        img = Image.open(original_path)

        # Create thumbnail (maintains aspect ratio)
        img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

        # Save thumbnail
        img.save(thumb_path, "JPEG", quality=THUMBNAIL_QUALITY)

        print(f"Generated thumbnail on-demand: {thumb_path}")
        return thumb_path

    except Exception as e:
        print(f"Error generating thumbnail for {filename}: {e}")
        raise

# Absolute paths from settings.py (R4); module-level so tests can point them elsewhere
photos_path = PHOTOS_DIR
thumbnails_path = THUMBNAILS_DIR

print(f"Flask serving photos from: {photos_path}")
print(f"Flask serving thumbnails from: {thumbnails_path}")

if not photos_path.exists():
    try:
        photos_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create photos directory: {e}")

if not thumbnails_path.exists():
    try:
        thumbnails_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create thumbnails directory: {e}")

@app.route('/')
def index():
    """Render the main gallery page."""
    return render_template(
        'index.html', gain_min=GAIN_MIN, gain_max=GAIN_MAX, temp_min=COLOUR_TEMP_MIN, temp_max=COLOUR_TEMP_MAX,
        wb_presets=WB_PRESETS,
        # chip rows: (API key, [(value, label)]), labels as on the Pi menu
        choices=[
            ("resolution", [(list(r), f"{resolution_label(r)} {r[0]}x{r[1]}") for r in CAPTURE_RESOLUTIONS]),
            ("format", [(f, f) for f in CAPTURE_FORMATS]),
            ("preset", [(p, value_label("preset", p)) for p in ("", *presets.PRESETS)]),
        ],
        gain_steps=[(g, value_label("analogue_gain", g)) for g in GAIN_STEPS],
    )

@app.route('/api/photos')
def get_photos():
    """Return a list of photo filenames sorted by date (newest first)."""
    try:
        if not photos_path.exists():
            print(f"Warning: Photos path does not exist: {photos_path}")
            return jsonify([])

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
    if camera_state:
        camera_state.shutter_requested = True
        return jsonify({"status": "ok", "message": "Shutter requested"})
    return jsonify({"status": "error", "message": "Camera state not initialized"}), 500

def parse_setting(data, key, low, high):
    """`data[key]` as a float that is 0 (auto) or within [low, high]; None if absent.

    Raises ValueError/TypeError for anything else, including booleans, NaN and inf (R7).
    """
    if key not in data:
        return None
    value = data[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be a number")
    value = float(value)
    if not (value == 0 or low <= value <= high):  # NaN fails both comparisons
        raise ValueError(f"{key} must be 0 (auto) or between {low} and {high}")
    return value

CHOICES = {"resolution": "capture_resolution", "format": "capture_format", "preset": "preset"}  # API key -> state


def settings_json():
    return {
        "gain": camera_state.analogue_gain,
        "color_temp": camera_state.colour_temperature,
        "resolution": list(camera_state.capture_resolution),
        "format": camera_state.capture_format,
        "preset": camera_state.preset,
    }


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update camera settings (gain, color temp, resolution, format, preset)."""
    if not camera_state:
        return jsonify({"status": "error", "message": "Camera state not initialized"}), 500

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "No data provided"}), 400

    try:
        gain = parse_setting(data, 'gain', GAIN_MIN, GAIN_MAX)
        temp = parse_setting(data, 'color_temp', COLOUR_TEMP_MIN, COLOUR_TEMP_MAX)
    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    choices = {}
    for key, attr in CHOICES.items():
        if key in data:
            value = tuple(data[key]) if isinstance(data[key], list) else data[key]  # JSON has no tuples
            if not is_valid(attr, value):
                return jsonify({"status": "error", "message": f"invalid {key}: {data[key]!r}"}), 400
            choices[attr] = value

    # Only store once every value is valid, so a bad request changes nothing
    if gain is not None:
        camera_state.analogue_gain = gain
    if temp is not None:
        camera_state.colour_temperature = int(temp)
    for attr, value in choices.items():
        setattr(camera_state, attr, value)

    return jsonify({"status": "ok", **settings_json()})


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current camera settings."""
    if not camera_state:
        return jsonify({"status": "error"}), 500
    return jsonify(settings_json())

if __name__ == '__main__':
    # Standalone run (no camera control)
    app.run(host='0.0.0.0', port=5000, debug=True)
