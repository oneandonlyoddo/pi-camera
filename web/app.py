
import os
import sys
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify

# Add parent directory to path to allow importing settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import PHOTOS_DIR, JPG_EXTENSION

app = Flask(__name__)

# Ensure the PHOTOS_DIR exists
photos_path = Path("../" + PHOTOS_DIR)
# Only create if it doesn't default to a weird path, but settings.py sets it to ~/DCIM.
# We'll rely on the main camera app or this app to ensure it exists.
if not photos_path.exists():
    try:
        photos_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create photos directory: {e}")

@app.route('/')
def index():
    """Render the main gallery page."""
    return render_template('index.html')

@app.route('/api/photos')
def get_photos():
    """Return a list of photo filenames sorted by date (newest first)."""
    try:
        if not photos_path.exists():
            return jsonify([])
            
        # Get all JPG files
        files = list(photos_path.glob(f"*{JPG_EXTENSION}"))
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Return list of filenames
        return jsonify([f.name for f in files])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dcim/<path:filename>')
def serve_photo(filename):
    """Serve a photo from the DCIM directory."""
    return send_from_directory(photos_path, filename)

if __name__ == '__main__':
    # Run slightly accessible so we can test it from other devices if needed
    app.run(host='0.0.0.0', port=5000, debug=True)
