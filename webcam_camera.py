
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
    
    def __init__(self, button_pin=None, photos_dir=PHOTOS_DIR):
        """
        Initialize the webcam camera.
        Args ignored or used compatibly to match DigitalCamera interface.
        """
        self.photos_dir = Path(photos_dir)
        self.running = False
        self.hud = HUD(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.cap = None
        
        # Create photos directory if it doesn't exist
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        print(f"Photos will be saved to: {self.photos_dir} (Webcam Mode)")
        
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
      
    def capture_photo(self, frame):
        """Save the current frame as a photo."""
        try:
            timestamp = datetime.datetime.now().strftime(FILENAME_TIMESTAMP_FORMAT)
            jpg_path = self.photos_dir / f"{FILENAME_PREFIX}_{timestamp}{JPG_EXTENSION}"
            
            # Save the frame
            cv2.imwrite(str(jpg_path), frame)
            
            print(f"✓ Photo saved: {jpg_path}")
            
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
