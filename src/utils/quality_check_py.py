"""
Quality Check Utilities
Validates image quality before processing to ensure accurate results.
Checks for blur, contrast, brightness, and other quality factors.
"""

import logging
import numpy as np
from PIL import Image
from io import BytesIO

from src.services.image_service import ImageService

logger = logging.getLogger(__name__)


# Quality thresholds
SHARPNESS_THRESHOLD = 100.0  # Laplacian variance threshold
CONTRAST_THRESHOLD = 30.0    # Standard deviation threshold
MIN_BRIGHTNESS = 20.0        # Minimum average brightness
MAX_BRIGHTNESS = 235.0       # Maximum average brightness
MIN_DIMENSION = 200          # Minimum width/height in pixels
MAX_DIMENSION = 4000         # Maximum width/height in pixels


def check_image_quality(image_bytes, check_type='puzzle'):
    """
    Check if image quality is sufficient for processing.
    
    Args:
        image_bytes: BytesIO object containing image data
        check_type: Type of check ('puzzle' or 'piece')
    
    Returns:
        tuple: (is_valid, error_message, quality_score)
            - is_valid: bool, True if quality is acceptable
            - error_message: str, description of issue if invalid
            - quality_score: float, overall quality score (0-100)
    """
    try:
        # Reset to beginning
        image_bytes.seek(0)
        
        # Load image
        image = Image.open(image_bytes)
        
        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Initialize image service for quality checks
        image_service = ImageService()
        
        # Check 1: Dimensions
        width, height = image.size
        
        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            image.close()
            return False, f"Image too small. Minimum size is {MIN_DIMENSION}x{MIN_DIMENSION} pixels.", 0.0
        
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            image.close()
            return False, f"Image too large. Maximum size is {MAX_DIMENSION}x{MAX_DIMENSION} pixels.", 0.0
        
        # Check 2: Sharpness (blur detection)
        sharpness = image_service.calculate_image_sharpness(image_array)
        
        if sharpness < SHARPNESS_THRESHOLD:
            image.close()
            sharpness_score = (sharpness / SHARPNESS_THRESHOLD) * 100
            return False, f"Image appears too blurry. Please retake photo with better focus.", sharpness_score
        
        # Check 3: Contrast
        contrast = image_service.calculate_image_contrast(image_array)
        
        if contrast < CONTRAST_THRESHOLD:
            image.close()
            contrast_score = (contrast / CONTRAST_THRESHOLD) * 100
            return False, f"Image has insufficient contrast. Try better lighting or different background.", contrast_score
        
        # Check 4: Brightness
        brightness = image_service.calculate_brightness(image_array)
        
        if brightness < MIN_BRIGHTNESS:
            image.close()
            brightness_score = (brightness / MIN_BRIGHTNESS) * 100
            return False, f"Image is too dark. Please use better lighting.", brightness_score
        
        if brightness > MAX_BRIGHTNESS:
            image.close()
            brightness_score = 100 - ((brightness - MAX_BRIGHTNESS) / (255 - MAX_BRIGHTNESS)) * 100
            return False, f"Image is overexposed. Please reduce lighting or adjust camera exposure.", brightness_score
        
        # Calculate overall quality score
        sharpness_score = min(100, (sharpness / SHARPNESS_THRESHOLD) * 100)
        contrast_score = min(100, (contrast / CONTRAST_THRESHOLD) * 100)
        
        # Brightness score (optimal around 127)
        brightness_deviation = abs(brightness - 127)
        brightness_score = max(0, 100 - (brightness_deviation / 127) * 100)
        
        # Weighted average
        quality_score = (
            0.40 * sharpness_score +    # 40% weight on sharpness (most important)
            0.35 * contrast_score +      # 35% weight on contrast
            0.25 * brightness_score      # 25% weight on brightness
        )
        
        # Cleanup
        image.close()
        
        logger.info(f"Image quality check passed: sharpness={sharpness:.1f}, contrast={contrast:.1f}, brightness={brightness:.1f}, score={quality_score:.1f}")
        
        return True, "Image quality is acceptable", quality_score
        
    except Exception as e:
        logger.error(f"Error checking image quality: {str(e)}", exc_info=True)
        return False, f"Error validating image: {str(e)}", 0.0


def validate_image_format(image_bytes):
    """
    Validate that the file is a supported image format.
    
    Args:
        image_bytes: BytesIO object containing image data
    
    Returns:
        tuple: (is_valid, error_message, format)
    """
    try:
        image_bytes.seek(0)
        image = Image.open(image_bytes)
        
        # Get format
        image_format = image.format
        
        # Supported formats
        supported_formats = ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF']
        
        if image_format not in supported_formats:
            image.close()
            return False, f"Unsupported image format: {image_format}. Please use JPEG, PNG, or WebP.", None
        
        image.close()
        return True, "Valid image format", image_format
        
    except Exception as e:
        logger.error(f"Error validating image format: {str(e)}")
        return False, f"Invalid or corrupted image file", None


def estimate_piece_visibility(image_array):
    """
    Estimate how visible the puzzle piece is in the image.
    Useful for detecting if piece is too small or background is too similar.
    
    Args:
        image_array: numpy array of image
    
    Returns:
        float: Visibility score (0-100)
    """
    try:
        import cv2
        
        # Convert to grayscale
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate edge density
        edge_density = np.sum(edges > 0) / edges.size
        
        # Calculate variance in image (uniformity check)
        variance = np.var(gray)
        
        # Visibility score combines edge density and variance
        visibility_score = min(100, (edge_density * 1000 + variance / 10))
        
        return visibility_score
        
    except Exception as e:
        logger.error(f"Error estimating piece visibility: {str(e)}")
        return 50.0  # Default middle score


def get_quality_suggestions(sharpness, contrast, brightness):
    """
    Generate helpful suggestions based on quality metrics.
    
    Args:
        sharpness: Sharpness value
        contrast: Contrast value
        brightness: Brightness value
    
    Returns:
        list: List of suggestion strings
    """
    suggestions = []
    
    # Sharpness suggestions
    if sharpness < SHARPNESS_THRESHOLD * 0.5:
        suggestions.append("Image is very blurry. Hold camera steady and ensure autofocus is working.")
    elif sharpness < SHARPNESS_THRESHOLD:
        suggestions.append("Image is slightly blurry. Try tapping screen to focus before taking photo.")
    
    # Contrast suggestions
    if contrast < CONTRAST_THRESHOLD * 0.5:
        suggestions.append("Very low contrast. Place piece on a contrasting background (dark piece on light background or vice versa).")
    elif contrast < CONTRAST_THRESHOLD:
        suggestions.append("Low contrast. Try a different background color.")
    
    # Brightness suggestions
    if brightness < MIN_BRIGHTNESS:
        suggestions.append("Image is too dark. Use better lighting or move closer to a light source.")
    elif brightness < MIN_BRIGHTNESS * 1.5:
        suggestions.append("Image is dim. Consider using more lighting.")
    elif brightness > MAX_BRIGHTNESS:
        suggestions.append("Image is overexposed. Reduce lighting or adjust camera exposure.")
    elif brightness > MAX_BRIGHTNESS * 0.9:
        suggestions.append("Image is very bright. Try reducing light or adjusting camera settings.")
    
    # General suggestions
    if not suggestions:
        suggestions.append("Image quality is good!")
    
    return suggestions


def check_file_size(file_obj, max_size_mb=10):
    """
    Check if file size is within acceptable limits.
    
    Args:
        file_obj: File object or BytesIO
        max_size_mb: Maximum size in megabytes
    
    Returns:
        tuple: (is_valid, error_message, size_mb)
    """
    try:
        # Get current position
        current_pos = file_obj.tell()
        
        # Seek to end to get size
        file_obj.seek(0, 2)
        size_bytes = file_obj.tell()
        
        # Reset to original position
        file_obj.seek(current_pos)
        
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            return False, f"File too large ({size_mb:.1f}MB). Maximum size is {max_size_mb}MB.", size_mb
        
        return True, "File size acceptable", size_mb
        
    except Exception as e:
        logger.error(f"Error checking file size: {str(e)}")
        return False, "Error checking file size", 0.0


def comprehensive_quality_check(image_bytes, check_type='puzzle'):
    """
    Perform comprehensive quality check with detailed feedback.
    
    Args:
        image_bytes: BytesIO object containing image data
        check_type: Type of check ('puzzle' or 'piece')
    
    Returns:
        dict: {
            'valid': bool,
            'message': str,
            'score': float,
            'details': {
                'sharpness': float,
                'contrast': float,
                'brightness': float,
                'dimensions': tuple,
                'format': str
            },
            'suggestions': list
        }
    """
    result = {
        'valid': False,
        'message': '',
        'score': 0.0,
        'details': {},
        'suggestions': []
    }
    
    try:
        # Check file size
        size_valid, size_msg, size_mb = check_file_size(image_bytes)
        if not size_valid:
            result['message'] = size_msg
            return result
        
        # Check format
        format_valid, format_msg, img_format = validate_image_format(image_bytes)
        if not format_valid:
            result['message'] = format_msg
            return result
        
        result['details']['format'] = img_format
        
        # Check quality
        quality_valid, quality_msg, quality_score = check_image_quality(image_bytes, check_type)
        
        # Get detailed metrics
        image_bytes.seek(0)
        image = Image.open(image_bytes)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        image_array = np.array(image)
        
        image_service = ImageService()
        sharpness = image_service.calculate_image_sharpness(image_array)
        contrast = image_service.calculate_image_contrast(image_array)
        brightness = image_service.calculate_brightness(image_array)
        
        result['details']['sharpness'] = round(sharpness, 2)
        result['details']['contrast'] = round(contrast, 2)
        result['details']['brightness'] = round(brightness, 2)
        result['details']['dimensions'] = image.size
        
        image.close()
        
        # Get suggestions
        suggestions = get_quality_suggestions(sharpness, contrast, brightness)
        result['suggestions'] = suggestions
        
        result['valid'] = quality_valid
        result['message'] = quality_msg
        result['score'] = round(quality_score, 1)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in comprehensive quality check: {str(e)}", exc_info=True)
        result['message'] = f"Error checking image quality: {str(e)}"
        return result
