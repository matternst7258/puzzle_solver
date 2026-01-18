"""
PuzzleSolver AI - Source Package
A web application for matching puzzle pieces to their locations in complete puzzles.
"""

__version__ = '1.0.0'
__author__ = 'PuzzleSolver Team'
__description__ = 'AI-powered puzzle piece matching application'

# Package imports for convenient access
from src.api import api_bp
from src.services import PuzzleService, MatchingService, ImageService
from src.models import FeatureExtractor
from src.utils import (
    check_image_quality,
    validate_puzzle_upload,
    validate_piece_upload,
    validate_url
)

__all__ = [
    # API
    'api_bp',
    
    # Services
    'PuzzleService',
    'MatchingService',
    'ImageService',
    
    # Models
    'FeatureExtractor',
    
    # Utils
    'check_image_quality',
    'validate_puzzle_upload',
    'validate_piece_upload',
    'validate_url',
]
