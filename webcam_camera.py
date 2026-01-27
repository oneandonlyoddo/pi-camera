
import time
import datetime
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from settings import *
from hud import HUD

class WebcamCamera:
    """
    Mock Camera controller using a local webcam (via OpenCV) 
    to mimic the Raspberry Pi HQ Camera module behaviour.
    """
    

    def __init__(self, button_pin=None, photos_dir=PHOTOS_DIR, camera_state=None):
        """
        Initialize the webcam camera.
        Args ignored or used compatibly to match DigitalCamera interface.
        """
        self.photos_dir = Path(photos_dir)
        self.thumbnails_dir = Path(THUMBNAILS_DIR)
        self.running = False
        self.hud = HUD(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.cap = None
        self.camera_state = camera_state

        # Create photos and thumbnails directories if they don't exist
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        print(f"Photos will be saved to: {self.photos_dir} (Webcam Mode)")
        print(f"Thumbnails will be saved to: {self.thumbnails_dir}")
        
    def setup_camera(self):
        """Initialize the webcam."""
        # Open default camera (index 0)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return

        # Set resolution (try to match preview settings)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, PREVIEW_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PREVIEW_HEIGHT)
        print("Webcam initialized")

    def generate_thumbnail(self, jpg_path):
        """
        Generate a thumbnail for the given JPG image.

        Args:
            jpg_path: Path to the full-size JPG image
        """
        try:
            # Open the image
            img = Image.open(jpg_path)

            # Create thumbnail (maintains aspect ratio)
            img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

            # Save thumbnail with same filename in thumbs directory
            thumb_path = self.thumbnails_dir / jpg_path.name
            img.save(thumb_path, "JPEG", quality=THUMBNAIL_QUALITY)

            print(f"  Thumbnail: {thumb_path}")

        except Exception as e:
            print(f"✗ Error generating thumbnail: {e}")

    def capture_photo(self, frame):
        """Save the current frame as a photo."""
        try:
            timestamp = datetime.datetime.now().strftime(FILENAME_TIMESTAMP_FORMAT)
            jpg_path = self.photos_dir / f"{FILENAME_PREFIX}_{timestamp}{JPG_EXTENSION}"

            # Save the frame
            cv2.imwrite(str(jpg_path), frame)

            print(f"✓ Photo saved: {jpg_path}")

            # Generate thumbnail
            self.generate_thumbnail(jpg_path)

        except Exception as e:
            print(f"✗ Error capturing photo: {e}")

    def run(self):
        """Start the camera preview loop."""
        try:
            print("Starting Webcam Camera (Mock Mode)...")
            print("Press SPACE to take a photo")
            print("Press 'q' or Ctrl+C to exit")
            
            self.setup_camera()
            self.running = True
            
            class MockCamera:
                """Mock object to pass to HUD.update()"""
                def set_overlay(self, overlay_array):
                    self.overlay = overlay_array
                def capture_metadata(self):
                    return {} # Return empty metadata for now

            mock_camera_obj = MockCamera()

            while self.running:
                if self.cap is None or not self.cap.isOpened():
                    break
                    
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Can't receive frame (stream end?). Exiting ...")
                    break

                # Check for web shutter request
                if self.camera_state and self.camera_state.consume_shutter_request():
                    print("Web shutter request received - capturing image...")
                    self.capture_photo(frame)

                # Simulate applying settings from web
                if self.camera_state:
                    gain = self.camera_state.analogue_gain
                    temp = self.camera_state.colour_temperature
                    if gain > 0:
                        # Just print for verification since webcam gain is tricky to mock uniformly
                        # print(f"Mock Gain set to {gain}")
                        pass

                # Update HUD
                # HUD.update() calls camera.set_overlay(np_array)
                # We catch that overlay in our mock object
                self.hud.update(mock_camera_obj)
                
                # If we have an overlay from the HUD, composite it onto the frame
                if hasattr(mock_camera_obj, 'overlay'):
                    # Overlay is RGBA, Frame is BGR
                    # Convert overlay to BGR and Alpha channel
                    overlay = mock_camera_obj.overlay
                    if overlay is not None:
                        # Resize overlay to match frame if needed (should match if config is correct)
                        if overlay.shape[:2] != frame.shape[:2]:
                            overlay = cv2.resize(overlay, (frame.shape[1], frame.shape[0]))
                        
                        # Normalize alpha to 0-1
                        alpha = overlay[:, :, 3] / 255.0
                        
                        # Create 3-channel alpha mask
                        alpha_3ch = np.dstack((alpha, alpha, alpha))
                        
                        # Convert overlay RGB to BGR (OpenCV uses BGR)
                        overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGBA2BGR)
                        
                        # Composite
                        # out = alpha * overlay + (1 - alpha) * frame
                        frame = (alpha_3ch * overlay_bgr + (1.0 - alpha_3ch) * frame).astype(np.uint8)

                # Show the frame
                cv2.imshow('Pi Camera Preview (Webcam Mock)', frame)

                # Handle user input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                elif key == 32: # SPACE bar
                    self.capture_photo(frame)
                    # Visual feedback
                    print("Click!")
                    time.sleep(0.2)
                
        except KeyboardInterrupt:
            print("\nShutting down camera...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources."""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Camera stopped. Goodbye!")

