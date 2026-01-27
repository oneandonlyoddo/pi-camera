
import os
import sys
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify, request

# Add parent directory to path to allow importing settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import PHOTOS_DIR, THUMBNAILS_DIR, JPG_EXTENSION

app = Flask(__name__)
camera_state = None  # Global to hold the shared state

def init_app(shared_state):
    """
    Initialize the Flask app with the shared camera state.
    This must be called before starting the server.
    """
    global camera_state
    camera_state = shared_state

# Ensure the PHOTOS_DIR and THUMBNAILS_DIR exist
# Resolve paths relative to the project root (parent of web/ directory)
project_root = Path(__file__).parent.parent.resolve()
photos_path = (project_root / PHOTOS_DIR).resolve()
thumbnails_path = (project_root / THUMBNAILS_DIR).resolve()

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
    return render_template('index.html')

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
    """Serve a thumbnail from the thumbnails directory with caching headers."""
    response = send_from_directory(thumbnails_path, filename)
    # Cache thumbnails for 1 year (they never change once created)
    response.cache_control.max_age = 31536000
    response.cache_control.public = True
    return response

@app.route('/api/trigger', methods=['POST'])
def trigger_shutter():
    """Trigger the camera shutter."""
    if camera_state:
        camera_state.shutter_requested = True
        return jsonify({"status": "ok", "message": "Shutter requested"})
    return jsonify({"status": "error", "message": "Camera state not initialized"}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update camera settings (gain, color temp)."""
    if not camera_state:
        return jsonify({"status": "error", "message": "Camera state not initialized"}), 500
        
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    if 'gain' in data:
        try:
            val = float(data['gain'])
            camera_state.analogue_gain = val
        except ValueError:
            pass
            
    if 'color_temp' in data:
        try:
            val = int(data['color_temp'])
            camera_state.colour_temperature = val
        except ValueError:
            pass
            
    return jsonify({
        "status": "ok", 
        "gain": camera_state.analogue_gain,
        "color_temp": camera_state.colour_temperature
    })
    
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current camera settings."""
    if not camera_state:
        return jsonify({"status": "error"}), 500
        
    return jsonify({
        "gain": camera_state.analogue_gain,
        "color_temp": camera_state.colour_temperature
    })

if __name__ == '__main__':
    # Standalone run (no camera control)
    app.run(host='0.0.0.0', port=5000, debug=True)
