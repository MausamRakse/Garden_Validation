import cv2
import numpy as np
from PIL import Image

class ImageValidator:
    def __init__(self):
        self.min_blur_score = 100.0  # Threshold for Laplacian Variance
        self.min_brightness = 40     # Threshold for average brightness (0-255)
        self.greenery_threshold = 0.05 # Minimum 5% green pixels for "Garden"

    def load_image(self, file_upload):
        """Converts Streamlit UploadedFile to OpenCV format."""
        file_bytes = np.asarray(bytearray(file_upload.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        # Reset file pointer for potential future reads
        file_upload.seek(0)
        return image

    def is_blurry(self, image):
        """Checks if image is blurry using Laplacian variance."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        return score < self.min_blur_score, score

    def is_dark(self, image):
        """Checks if image is too dark."""
        # Convert to HSV to check V channel brightness
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        brightness = np.mean(hsv[:, :, 2])
        return brightness < self.min_brightness, brightness

    def detect_greenery(self, image):
        """Detects green vegetation using HSV color masking."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define range for green color in HSV
        # Hue: 35-85, Saturation: 30-255, Value: 30-255
        lower_green = np.array([35, 30, 30])
        upper_green = np.array([85, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_ratio = np.sum(mask > 0) / mask.size
        
        return green_ratio > self.greenery_threshold, green_ratio

    def detect_structure(self, image):
        """Detects structural elements (lines) acting as a proxy for 'Home/Building' visibility."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Detect lines using HoughLinesP
        # minLineLength: Minimum length of line. Line segments shorter than this are rejected.
        # maxLineGap: Maximum allowed gap between line segments to treat them as single line.
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)
        
        if lines is None:
            return False, 0
        
        # simple heuristic: count significant lines
        line_count = len(lines)
        # We assume a visible house/fence/pavement has at least a few straight lines
        return line_count > 10, line_count

    def validate_image(self, file_upload, yard_type="General"):
        """Runs all checks on a single image."""
        try:
            image = self.load_image(file_upload)
            if image is None:
                return {"valid": False, "error": "Could not decode image."}

            # 1. Blur Check
            is_blur, blur_score = self.is_blurry(image)
            if is_blur:
                return {"valid": False, "error": f"{yard_type} image is too blurry. (Score: {blur_score:.1f})"}

            # 2. Brightness Check
            is_dark, brightness = self.is_dark(image)
            if is_dark:
                return {"valid": False, "error": f"{yard_type} image is too dark. (Brightness: {brightness:.1f})"}

            # 3. Garden/Greenery Check
            has_green, green_ratio = self.detect_greenery(image)
            
            # 4. Structure/Home Check
            has_structure, line_count = self.detect_structure(image)

            # Logic: We generally want BOTH for a "Home Garden"
            # But specific yards might vary.
            # Front/Back usually have House + Garden.
            # Side might be just wall + path (Structure) or just path (Green?).
            
            # strict check for Greenery
            if not has_green:
                 return {
                    "valid": False, 
                    "error": f"Garden is not visible. {yard_type} must show BOTH Garden + Home. (Greenery: {green_ratio*100:.1f}%)"
                }
            
            # strict check for Home/Structure
            if not has_structure:
                return {
                    "valid": False,
                    "error": f"Home/Building is not clearly visible. {yard_type} must show BOTH Garden + Home."
                }
                
            # Internal consistency check?
            # For now, if both pass, we are good.
            
            return {"valid": True, "message": "OK"}

        except Exception as e:
            return {"valid": False, "error": f"Processing error: {str(e)}"}
