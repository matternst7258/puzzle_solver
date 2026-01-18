"""
Input Validators
Validates user input for API endpoints including file uploads and URLs.
"""

import os
import re
import logging
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'heic', 'bmp', 'tiff'}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/heic',
    'image/bmp',
    'image/tiff'
}

# Maximum file sizes
MAX_PUZZLE_SIZE_MB = 10
MAX_PIECE_SIZE_MB = 10

# URL validation
ALLOWED_URL_SCHEMES = {'http', 'https'}
MAX_URL_LENGTH = 2048


def validate_puzzle_upload(file):
    """
    Validate puzzle image upload.
    
    Args:
        file: FileStorage object from Flask request
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not file:
            return False, "No file provided"
        
        # Check if file has a filename
        if file.filename == '':
            return False, "No file selected"
        
        # Check file extension
        if not allowed_file(file.filename):
            return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Check MIME type
        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"Unexpected MIME type: {file.content_type}")
            # Don't reject based solely on MIME type as it can be incorrect
        
        # File size check (if available)
        if hasattr(file, 'content_length') and file.content_length:
            size_mb = file.content_length / (1024 * 1024)
            if size_mb > MAX_PUZZLE_SIZE_MB:
                return False, f"File too large ({size_mb:.1f}MB). Maximum size is {MAX_PUZZLE_SIZE_MB}MB"
        
        return True, "Valid puzzle upload"
        
    except Exception as e:
        logger.error(f"Error validating puzzle upload: {str(e)}", exc_info=True)
        return False, f"Error validating file: {str(e)}"


def validate_piece_upload(file):
    """
    Validate puzzle piece image upload.
    
    Args:
        file: FileStorage object from Flask request
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not file:
            return False, "No piece image provided"
        
        # Check if file has a filename
        if file.filename == '':
            return False, "No file selected"
        
        # Check file extension
        if not allowed_file(file.filename):
            return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Check MIME type
        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"Unexpected MIME type: {file.content_type}")
        
        # File size check
        if hasattr(file, 'content_length') and file.content_length:
            size_mb = file.content_length / (1024 * 1024)
            if size_mb > MAX_PIECE_SIZE_MB:
                return False, f"File too large ({size_mb:.1f}MB). Maximum size is {MAX_PIECE_SIZE_MB}MB"
        
        return True, "Valid piece upload"
        
    except Exception as e:
        logger.error(f"Error validating piece upload: {str(e)}", exc_info=True)
        return False, f"Error validating file: {str(e)}"


def allowed_file(filename):
    """
    Check if filename has an allowed extension.
    
    Args:
        filename: Name of the file
    
    Returns:
        bool: True if extension is allowed
    """
    if not filename:
        return False
    
    # Get extension
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def validate_url(url):
    """
    Validate URL for puzzle image download.
    
    Args:
        url: URL string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if URL is provided
        if not url or not isinstance(url, str):
            return False, "No URL provided"
        
        # Remove whitespace
        url = url.strip()
        
        # Check length
        if len(url) > MAX_URL_LENGTH:
            return False, f"URL too long. Maximum length is {MAX_URL_LENGTH} characters"
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"
        
        # Check scheme
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            return False, f"Invalid URL scheme. Only HTTP and HTTPS are allowed"
        
        # Check if domain exists
        if not parsed.netloc:
            return False, "Invalid URL: no domain found"
        
        # Check for suspicious patterns
        if contains_suspicious_patterns(url):
            return False, "URL contains suspicious patterns"
        
        # Check if URL points to an image (basic check)
        if not url_looks_like_image(url):
            logger.warning(f"URL may not point to an image: {url}")
            # Don't reject, just warn - content-type check will happen during download
        
        return True, "Valid URL"
        
    except Exception as e:
        logger.error(f"Error validating URL: {str(e)}", exc_info=True)
        return False, f"Error validating URL: {str(e)}"


def url_looks_like_image(url):
    """
    Check if URL appears to point to an image file.
    This is a heuristic check, not definitive.
    
    Args:
        url: URL string
    
    Returns:
        bool: True if URL looks like it points to an image
    """
    # Parse URL
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Check for image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.bmp', '.tiff', '.gif']
    
    for ext in image_extensions:
        if path.endswith(ext):
            return True
    
    # Check for common image URL patterns
    if '/images/' in path or '/img/' in path or '/photo/' in path:
        return True
    
    # If no extension but has query parameters, it might still be an image
    if parsed.query:
        return True
    
    return False


def contains_suspicious_patterns(url):
    """
    Check for suspicious patterns in URL that might indicate malicious intent.
    
    Args:
        url: URL string
    
    Returns:
        bool: True if suspicious patterns found
    """
    # Convert to lowercase for checking
    url_lower = url.lower()
    
    # Suspicious patterns
    suspicious_patterns = [
        'javascript:',
        'data:',
        'file://',
        'ftp://',
        '<script',
        'onclick',
        'onerror',
        '../',  # Path traversal
        '..\\',
    ]
    
    for pattern in suspicious_patterns:
        if pattern in url_lower:
            logger.warning(f"Suspicious pattern found in URL: {pattern}")
            return True
    
    return False


def validate_puzzle_id(puzzle_id):
    """
    Validate puzzle ID format (UUID).
    
    Args:
        puzzle_id: Puzzle ID string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if provided
        if not puzzle_id or not isinstance(puzzle_id, str):
            return False, "No puzzle ID provided"
        
        # UUID pattern (8-4-4-4-12 hex digits)
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(puzzle_id):
            return False, "Invalid puzzle ID format"
        
        # Check for path traversal attempts
        if '..' in puzzle_id or '/' in puzzle_id or '\\' in puzzle_id:
            logger.warning(f"Path traversal attempt detected in puzzle ID: {puzzle_id}")
            return False, "Invalid puzzle ID"
        
        return True, "Valid puzzle ID"
        
    except Exception as e:
        logger.error(f"Error validating puzzle ID: {str(e)}", exc_info=True)
        return False, f"Error validating puzzle ID: {str(e)}"


def validate_puzzle_name(name):
    """
    Validate puzzle name.
    
    Args:
        name: Puzzle name string
    
    Returns:
        tuple: (is_valid, error_message, sanitized_name)
    """
    try:
        # Check if provided
        if not name:
            # Use default name
            return True, "Using default name", "Untitled Puzzle"
        
        # Convert to string
        name = str(name).strip()
        
        # Check length
        if len(name) > 100:
            return False, "Puzzle name too long. Maximum 100 characters", None
        
        if len(name) < 1:
            return True, "Using default name", "Untitled Puzzle"
        
        # Sanitize name (remove special characters that might cause issues)
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
        
        # Check if anything remains after sanitization
        if len(sanitized) < 1:
            return True, "Using default name", "Untitled Puzzle"
        
        return True, "Valid puzzle name", sanitized
        
    except Exception as e:
        logger.error(f"Error validating puzzle name: {str(e)}", exc_info=True)
        return False, f"Error validating puzzle name: {str(e)}", None


def sanitize_filename(filename):
    """
    Sanitize a filename to prevent security issues.
    
    Args:
        filename: Original filename
    
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return "file"
    
    # Use werkzeug's secure_filename
    safe_name = secure_filename(filename)
    
    # If nothing remains, use default
    if not safe_name:
        return "file"
    
    return safe_name


def validate_request_data(data, required_fields):
    """
    Validate that required fields are present in request data.
    
    Args:
        data: Dictionary of request data
        required_fields: List of required field names
    
    Returns:
        tuple: (is_valid, error_message, missing_fields)
    """
    try:
        if not data:
            return False, "No data provided", required_fields
        
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", missing_fields
        
        return True, "All required fields present", []
        
    except Exception as e:
        logger.error(f"Error validating request data: {str(e)}", exc_info=True)
        return False, f"Error validating request: {str(e)}", []


def validate_confidence_threshold(threshold):
    """
    Validate confidence threshold value.
    
    Args:
        threshold: Confidence threshold (0-100)
    
    Returns:
        tuple: (is_valid, error_message, value)
    """
    try:
        # Convert to float
        try:
            threshold = float(threshold)
        except (ValueError, TypeError):
            return False, "Confidence threshold must be a number", None
        
        # Check range
        if threshold < 0 or threshold > 100:
            return False, "Confidence threshold must be between 0 and 100", None
        
        return True, "Valid threshold", threshold
        
    except Exception as e:
        logger.error(f"Error validating confidence threshold: {str(e)}", exc_info=True)
        return False, f"Error validating threshold: {str(e)}", None


def validate_integer_param(value, param_name, min_val=None, max_val=None):
    """
    Validate an integer parameter.
    
    Args:
        value: Value to validate
        param_name: Name of the parameter (for error messages)
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
    
    Returns:
        tuple: (is_valid, error_message, int_value)
    """
    try:
        # Convert to int
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return False, f"{param_name} must be an integer", None
        
        # Check minimum
        if min_val is not None and int_value < min_val:
            return False, f"{param_name} must be at least {min_val}", None
        
        # Check maximum
        if max_val is not None and int_value > max_val:
            return False, f"{param_name} must be at most {max_val}", None
        
        return True, f"Valid {param_name}", int_value
        
    except Exception as e:
        logger.error(f"Error validating {param_name}: {str(e)}", exc_info=True)
        return False, f"Error validating {param_name}: {str(e)}", None
