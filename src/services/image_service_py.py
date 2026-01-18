"""
Image Service
Handles image downloading, processing, and utility functions.
"""

import logging
import requests
from io import BytesIO
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class ImageService:
    """Service for image downloading and processing utilities."""
    
    def __init__(self, timeout=30, max_size_mb=10):
        """
        Initialize image service.
        
        Args:
            timeout: Request timeout in seconds
            max_size_mb: Maximum file size in MB
        """
        self.timeout = timeout
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # User agent for HTTP requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        logger.info(f"ImageService initialized (timeout={timeout}s, max_size={max_size_mb}MB)")
    
    def download_from_url(self, url):
        """
        Download image from URL.
        
        Args:
            url: URL to download image from
        
        Returns:
            BytesIO: Image data in memory or None if failed
        """
        try:
            logger.info(f"Downloading image from URL: {url}")
            
            # Make request with timeout
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )
            
            # Check response status
            if response.status_code != 200:
                logger.error(f"Failed to download image: HTTP {response.status_code}")
                return None
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logger.error(f"URL does not point to an image: {content_type}")
                return None
            
            # Check content length
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.max_size_bytes:
                logger.error(f"Image too large: {int(content_length) / 1024 / 1024:.1f}MB")
                return None
            
            # Download in chunks to avoid memory issues
            image_data = BytesIO()
            total_size = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    total_size += len(chunk)
                    
                    # Check size limit
                    if total_size > self.max_size_bytes:
                        logger.error(f"Image exceeds size limit during download")
                        return None
                    
                    image_data.write(chunk)
            
            # Reset to beginning
            image_data.seek(0)
            
            # Verify it's a valid image
            try:
                img = Image.open(image_data)
                img.verify()
                image_data.seek(0)  # Reset after verify
            except Exception as e:
                logger.error(f"Downloaded file is not a valid image: {str(e)}")
                return None
            
            logger.info(f"Successfully downloaded image ({total_size / 1024:.1f}KB)")
            return image_data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout downloading image from {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading image: {str(e)}", exc_info=True)
            return None
    
    def resize_image(self, image, max_width=2048, max_height=2048):
        """
        Resize image if it exceeds maximum dimensions.
        Maintains aspect ratio.
        
        Args:
            image: PIL Image
            max_width: Maximum width
            max_height: Maximum height
        
        Returns:
            PIL Image: Resized image
        """
        try:
            width, height = image.size
            
            # Check if resize needed
            if width <= max_width and height <= max_height:
                return image
            
            # Calculate new dimensions maintaining aspect ratio
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
            
            # Resize with high-quality resampling
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return resized
            
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}", exc_info=True)
            return image
    
    def compress_image(self, image, quality=85):
        """
        Compress image to JPEG format.
        
        Args:
            image: PIL Image
            quality: JPEG quality (1-100)
        
        Returns:
            BytesIO: Compressed image data
        """
        try:
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Compress to BytesIO
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Error compressing image: {str(e)}", exc_info=True)
            raise
    
    def remove_background(self, image_array, method='grabcut'):
        """
        Remove background from image (useful for puzzle pieces).
        
        Args:
            image_array: numpy array of image
            method: Background removal method ('grabcut', 'threshold')
        
        Returns:
            numpy array: Image with background removed
        """
        try:
            import cv2
            
            if method == 'grabcut':
                return self._remove_background_grabcut(image_array)
            elif method == 'threshold':
                return self._remove_background_threshold(image_array)
            else:
                logger.warning(f"Unknown background removal method: {method}")
                return image_array
            
        except Exception as e:
            logger.error(f"Error removing background: {str(e)}")
            return image_array
    
    def _remove_background_grabcut(self, image_array):
        """
        Remove background using GrabCut algorithm.
        
        Args:
            image_array: numpy array of image (RGB)
        
        Returns:
            numpy array: Image with background removed
        """
        try:
            import cv2
            
            # Create mask
            mask = np.zeros(image_array.shape[:2], np.uint8)
            
            # Background and foreground models
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Define rectangle around foreground (approximate)
            height, width = image_array.shape[:2]
            rect = (10, 10, width - 10, height - 10)
            
            # Apply GrabCut
            cv2.grabCut(
                image_array,
                mask,
                rect,
                bgd_model,
                fgd_model,
                5,  # iterations
                cv2.GC_INIT_WITH_RECT
            )
            
            # Create binary mask
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Apply mask
            result = image_array * mask2[:, :, np.newaxis]
            
            return result
            
        except Exception as e:
            logger.error(f"Error in GrabCut background removal: {str(e)}")
            return image_array
    
    def _remove_background_threshold(self, image_array):
        """
        Remove background using simple thresholding.
        Assumes background is relatively uniform.
        
        Args:
            image_array: numpy array of image (RGB)
        
        Returns:
            numpy array: Image with background removed
        """
        try:
            import cv2
            
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Apply Otsu's thresholding
            _, mask = cv2.threshold(
                gray,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            # Apply morphological operations to clean up mask
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Convert mask to 3 channels
            mask = mask[:, :, np.newaxis] / 255
            
            # Apply mask
            result = (image_array * mask).astype(np.uint8)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in threshold background removal: {str(e)}")
            return image_array
    
    def detect_orientation(self, image_array):
        """
        Detect if image needs rotation correction.
        Uses edge detection and dominant orientations.
        
        Args:
            image_array: numpy array of image
        
        Returns:
            int: Suggested rotation in degrees (0, 90, 180, 270)
        """
        try:
            import cv2
            
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(
                edges,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                return 0
            
            # Get largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[-1]
            
            # Determine rotation needed
            if angle < -45:
                rotation = 90
            elif angle > 45:
                rotation = 270
            elif angle < -22.5:
                rotation = 45
            elif angle > 22.5:
                rotation = 315
            else:
                rotation = 0
            
            logger.info(f"Detected orientation angle: {angle:.1f}°, suggested rotation: {rotation}°")
            
            return rotation
            
        except Exception as e:
            logger.error(f"Error detecting orientation: {str(e)}")
            return 0
    
    def calculate_image_sharpness(self, image_array):
        """
        Calculate image sharpness using Laplacian variance.
        Higher values indicate sharper images.
        
        Args:
            image_array: numpy array of image
        
        Returns:
            float: Sharpness score
        """
        try:
            import cv2
            
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            
            return variance
            
        except Exception as e:
            logger.error(f"Error calculating sharpness: {str(e)}")
            return 0.0
    
    def calculate_image_contrast(self, image_array):
        """
        Calculate image contrast using standard deviation.
        
        Args:
            image_array: numpy array of image
        
        Returns:
            float: Contrast score
        """
        try:
            import cv2
            
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Calculate standard deviation (contrast measure)
            contrast = np.std(gray)
            
            return contrast
            
        except Exception as e:
            logger.error(f"Error calculating contrast: {str(e)}")
            return 0.0
    
    def calculate_brightness(self, image_array):
        """
        Calculate average brightness of image.
        
        Args:
            image_array: numpy array of image
        
        Returns:
            float: Brightness (0-255)
        """
        try:
            import cv2
            
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Calculate mean brightness
            brightness = np.mean(gray)
            
            return brightness
            
        except Exception as e:
            logger.error(f"Error calculating brightness: {str(e)}")
            return 0.0
