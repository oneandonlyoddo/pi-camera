# /// script
# requires-python = ">=3.13"
# dependencies = ["flask", "pillow"]
# ///
"""Run the web app on the desktop with dummy photos (no Pi, no camera).

    uv run scripts/web_dev.py                     # dummy JPGs in dev-photos/ (made on first run)
    uv run scripts/web_dev.py --photos device-out # real photos copied back by dev.sh --shoot

Settings live in memory only; the shutter button does nothing. Never points at DCIM/ (R11).
"""
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

import web.app as webapp  # noqa: E402
from shared_state import CameraState  # noqa: E402

COLOURS = [(230, 120, 40), (40, 90, 160), (90, 150, 70), (160, 50, 80), (200, 180, 60), (70, 70, 70)]


def make_dummies(folder, count=30):
    """IMG_<date>_<time>.jpg over the last ~10 days (the gallery groups by the filename date), mtime to match."""
    now = datetime.now()
    for i in range(count):
        taken = now - timedelta(days=i // 4 * 1.5, hours=i % 4, minutes=7 * i)
        path = folder / f"IMG_{taken:%Y%m%d_%H%M%S_%f}.jpg"
        img = Image.new("RGB", (2028, 1520), COLOURS[i % len(COLOURS)])  # 3MP, the Pi's smaller capture size
        ImageDraw.Draw(img).text((80, 80), f"#{i}  {taken:%a %d %b %H:%M}", fill="white", font_size=120)
        img.save(path, "JPEG", quality=80)
        os.utime(path, (taken.timestamp(), taken.timestamp()))
    print(f"Made {count} dummy photos in {folder}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--photos", type=Path, default=ROOT / "dev-photos", help="folder with JPGs")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    photos = args.photos.resolve()
    if photos == webapp.PHOTOS_DIR.resolve():
        sys.exit("Refusing to serve DCIM/: thumbnails would be written into the photo folder (R11)")
    thumbs = photos / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    if not any(photos.glob("*.jpg")):
        make_dummies(photos)

    webapp.photos_path = photos
    webapp.thumbnails_path = thumbs
    webapp.init_app(CameraState())
    webapp.app.run(host="127.0.0.1", port=args.port, debug=True)  # debug: reloads on code and template edits


if __name__ == "__main__":
    main()
