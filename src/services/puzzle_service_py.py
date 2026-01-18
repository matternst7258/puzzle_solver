"""
Puzzle Service
Handles puzzle storage, retrieval, and management.
"""

import os
import json
import uuid
import shutil
import logging
from datetime import datetime
from PIL import Image
from io import BytesIO

from src.models.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


class PuzzleService:
    """Service for managing puzzle images and metadata."""
    
    def __init__(self, puzzle_folder='saved_puzzles'):
        """
        Initialize puzzle service.
        
        Args:
            puzzle_folder: Directory to store puzzles
        """
        self.puzzle_folder = puzzle_folder
        self.feature_extractor = FeatureExtractor()
        
        # Ensure puzzle folder exists
        os.makedirs(self.puzzle_folder, exist_ok=True)
        
        logger.info(f"PuzzleService initialized with folder: {self.puzzle_folder}")
    
    def save_puzzle(self, image_bytes, puzzle_name):
        """
        Save a puzzle image with preprocessing and feature extraction.
        
        Args:
            image_bytes: BytesIO object containing image data
            puzzle_name: Name for the puzzle
        
        Returns:
            dict: Puzzle metadata including puzzle_id, name, dimensions
        """
        try:
            # Generate unique ID
            puzzle_id = str(uuid.uuid4())
            puzzle_dir = os.path.join(self.puzzle_folder, puzzle_id)
            os.makedirs(puzzle_dir, exist_ok=True)
            
            logger.info(f"Saving puzzle {puzzle_id}: {puzzle_name}")
            
            # Load image
            image = Image.open(image_bytes)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            original_width, original_height = image.size
            
            # Resize if too large (max 2048x2048)
            max_size = 2048
            if original_width > max_size or original_height > max_size:
                logger.info(f"Resizing puzzle from {original_width}x{original_height}")
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            width, height = image.size
            
            # Save original (resized) image
            original_path = os.path.join(puzzle_dir, 'original.jpg')
            image.save(original_path, 'JPEG', quality=85, optimize=True)
            logger.info(f"Saved original image: {width}x{height}")
            
            # Create thumbnail (200x200)
            thumbnail = image.copy()
            thumbnail.thumbnail((200, 200), Image.Resampling.LANCZOS)
            thumbnail_path = os.path.join(puzzle_dir, 'thumbnail.jpg')
            thumbnail.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            logger.info("Created thumbnail")
            
            # Extract and save features
            logger.info("Extracting puzzle features...")
            features = self.feature_extractor.extract_puzzle_features(image)
            features_path = os.path.join(puzzle_dir, 'features.pkl')
            self.feature_extractor.save_features(features, features_path)
            logger.info(f"Extracted {len(features['regions'])} regions")
            
            # Create metadata
            metadata = {
                'puzzle_id': puzzle_id,
                'name': puzzle_name,
                'date_added': datetime.utcnow().isoformat(),
                'dimensions': {
                    'width': width,
                    'height': height
                },
                'original_dimensions': {
                    'width': original_width,
                    'height': original_height
                },
                'region_count': len(features['regions'])
            }
            
            # Save metadata
            metadata_path = os.path.join(puzzle_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Puzzle {puzzle_id} saved successfully")
            
            # Cleanup
            image.close()
            thumbnail.close()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error saving puzzle: {str(e)}", exc_info=True)
            # Cleanup on error
            if os.path.exists(puzzle_dir):
                shutil.rmtree(puzzle_dir)
            raise
    
    def get_puzzle(self, puzzle_id):
        """
        Get puzzle metadata.
        
        Args:
            puzzle_id: UUID of the puzzle
        
        Returns:
            dict: Puzzle metadata or None if not found
        """
        try:
            puzzle_dir = os.path.join(self.puzzle_folder, puzzle_id)
            metadata_path = os.path.join(puzzle_dir, 'metadata.json')
            
            if not os.path.exists(metadata_path):
                logger.warning(f"Puzzle not found: {puzzle_id}")
                return None
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Add URLs
            metadata['image_url'] = f"/puzzle_solver/api/puzzles/{puzzle_id}/image"
            metadata['thumbnail_url'] = f"/puzzle_solver/api/puzzles/{puzzle_id}/thumbnail"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting puzzle {puzzle_id}: {str(e)}", exc_info=True)
            return None
    
    def list_puzzles(self):
        """
        List all saved puzzles.
        
        Returns:
            list: Array of puzzle metadata dictionaries
        """
        try:
            puzzles = []
            
            if not os.path.exists(self.puzzle_folder):
                return puzzles
            
            # Iterate through puzzle directories
            for item in os.listdir(self.puzzle_folder):
                puzzle_dir = os.path.join(self.puzzle_folder, item)
                
                if not os.path.isdir(puzzle_dir):
                    continue
                
                metadata_path = os.path.join(puzzle_dir, 'metadata.json')
                
                if not os.path.exists(metadata_path):
                    continue
                
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Add URLs
                    metadata['image_url'] = f"/puzzle_solver/api/puzzles/{metadata['puzzle_id']}/image"
                    metadata['thumbnail_url'] = f"/puzzle_solver/api/puzzles/{metadata['puzzle_id']}/thumbnail"
                    
                    puzzles.append(metadata)
                    
                except Exception as e:
                    logger.error(f"Error reading puzzle metadata {item}: {str(e)}")
                    continue
            
            # Sort by date added (newest first)
            puzzles.sort(key=lambda x: x.get('date_added', ''), reverse=True)
            
            logger.info(f"Found {len(puzzles)} saved puzzles")
            return puzzles
            
        except Exception as e:
            logger.error(f"Error listing puzzles: {str(e)}", exc_info=True)
            return []
    
    def delete_puzzle(self, puzzle_id):
        """
        Delete a puzzle and all associated files.
        
        Args:
            puzzle_id: UUID of the puzzle
        
        Returns:
            bool: True if successful, False if puzzle not found
        """
        try:
            puzzle_dir = os.path.join(self.puzzle_folder, puzzle_id)
            
            if not os.path.exists(puzzle_dir):
                logger.warning(f"Puzzle not found for deletion: {puzzle_id}")
                return False
            
            # Remove entire puzzle directory
            shutil.rmtree(puzzle_dir)
            logger.info(f"Deleted puzzle: {puzzle_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting puzzle {puzzle_id}: {str(e)}", exc_info=True)
            raise
    
    def get_puzzle_image_path(self, puzzle_id):
        """
        Get the file path to the puzzle image.
        
        Args:
            puzzle_id: UUID of the puzzle
        
        Returns:
            str: Path to image file or None if not found
        """
        puzzle_dir = os.path.join(self.puzzle_folder, puzzle_id)
        image_path = os.path.join(puzzle_dir, 'original.jpg')
        
        if os.path.exists(image_path):
            return image_path
        
        return None
    
    def get_puzzle_thumbnail_path(self, puzzle_id):
        """
        Get the file path to the puzzle thumbnail.
        
        Args:
            puzzle_id: UUID of the puzzle
        
        Returns:
            str: Path to thumbnail file or None if not found
        """
        puzzle_dir = os.path.join(self.puzzle_folder, puzzle_id)
        thumbnail_path = os.path.join(puzzle_dir, 'thumbnail.jpg')
        
        if os.path.exists(thumbnail_path):
            return thumbnail_path
        
        return None
    
    def get_puzzle_features_path(self, puzzle_id):
        """
        Get the file path to the puzzle features.
        
        Args:
            puzzle_id: UUID of the puzzle
        
        Returns:
            str: Path to features file or None if not found
        """
        puzzle_dir = os.path.join(self.puzzle_folder, puzzle_id)
        features_path = os.path.join(puzzle_dir, 'features.pkl')
        
        if os.path.exists(features_path):
            return features_path
        
        return None
    
    def load_puzzle_features(self, puzzle_id):
        """
        Load pre-computed features for a puzzle.
        
        Args:
            puzzle_id: UUID of the puzzle
        
        Returns:
            dict: Feature data or None if not found
        """
        try:
            features_path = self.get_puzzle_features_path(puzzle_id)
            
            if features_path is None:
                logger.error(f"Features not found for puzzle {puzzle_id}")
                return None
            
            features = self.feature_extractor.load_features(features_path)
            logger.info(f"Loaded features for puzzle {puzzle_id}")
            
            return features
            
        except Exception as e:
            logger.error(f"Error loading features for puzzle {puzzle_id}: {str(e)}", exc_info=True)
            return None
    
    def get_puzzle_image(self, puzzle_id):
        """
        Load puzzle image into memory.
        
        Args:
            puzzle_id: UUID of the puzzle
        
        Returns:
            PIL.Image: Puzzle image or None if not found
        """
        try:
            image_path = self.get_puzzle_image_path(puzzle_id)
            
            if image_path is None:
                logger.error(f"Image not found for puzzle {puzzle_id}")
                return None
            
            image = Image.open(image_path)
            return image
            
        except Exception as e:
            logger.error(f"Error loading image for puzzle {puzzle_id}: {str(e)}", exc_info=True)
            return None
