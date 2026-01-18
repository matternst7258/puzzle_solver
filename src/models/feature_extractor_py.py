"""
Feature Extractor
Extracts visual features from puzzle pieces and puzzle images using deep learning.
Uses TensorFlow/Keras with pre-trained ResNet50 for high accuracy.
"""

import logging
import pickle
import numpy as np
import cv2
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.models import Model

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract visual features from images using deep learning and computer vision."""
    
    def __init__(self):
        """Initialize feature extractor with ResNet50 model."""
        logger.info("Initializing FeatureExtractor with ResNet50...")
        
        # Load pre-trained ResNet50 model
        # Remove top layers to get feature vectors
        base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
        
        # Use the model as-is for feature extraction
        self.model = base_model
        
        # Input shape for ResNet50
        self.input_shape = (224, 224)
        
        logger.info("FeatureExtractor initialized successfully")
    
    def extract_puzzle_features(self, puzzle_image):
        """
        Extract features from complete puzzle image.
        Divides puzzle into overlapping regions and extracts features for each.
        
        Args:
            puzzle_image: PIL Image of the complete puzzle
        
        Returns:
            dict: {
                'regions': [
                    {
                        'x': int,
                        'y': int,
                        'width': int,
                        'height': int,
                        'color_hist': numpy array,
                        'shape': dict,
                        'deep_features': numpy array
                    },
                    ...
                ],
                'grid_size': (rows, cols)
            }
        """
        try:
            logger.info(f"Extracting features from puzzle image {puzzle_image.size}")
            
            # Convert to numpy array
            puzzle_array = np.array(puzzle_image)
            height, width = puzzle_array.shape[:2]
            
            # Define grid parameters
            # Use overlapping windows for better coverage
            window_size = 100  # Size of each region
            overlap = 50       # Overlap between regions
            step = window_size - overlap
            
            regions = []
            
            # Slide window across image
            for y in range(0, height - window_size + 1, step):
                for x in range(0, width - window_size + 1, step):
                    # Extract region
                    region_array = puzzle_array[y:y+window_size, x:x+window_size]
                    
                    # Extract features for this region
                    region_features = self._extract_region_features(region_array)
                    
                    # Add location information
                    region_features['x'] = x
                    region_features['y'] = y
                    region_features['width'] = window_size
                    region_features['height'] = window_size
                    
                    regions.append(region_features)
            
            rows = (height - window_size) // step + 1
            cols = (width - window_size) // step + 1
            
            logger.info(f"Extracted features for {len(regions)} regions ({rows}x{cols} grid)")
            
            return {
                'regions': regions,
                'grid_size': (rows, cols)
            }
            
        except Exception as e:
            logger.error(f"Error extracting puzzle features: {str(e)}", exc_info=True)
            raise
    
    def extract_piece_features(self, piece_image):
        """
        Extract features from a single puzzle piece.
        
        Args:
            piece_image: PIL Image of the puzzle piece
        
        Returns:
            dict: {
                'color_hist': numpy array,
                'shape': dict,
                'deep_features': numpy array
            }
        """
        try:
            # Convert to numpy array
            piece_array = np.array(piece_image)
            
            # Extract features
            features = self._extract_region_features(piece_array)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting piece features: {str(e)}", exc_info=True)
            raise
    
    def _extract_region_features(self, image_array):
        """
        Extract all features from an image region.
        
        Args:
            image_array: numpy array of image region (RGB)
        
        Returns:
            dict: Feature dictionary
        """
        features = {}
        
        # Extract color histogram
        features['color_hist'] = self._extract_color_histogram(image_array)
        
        # Extract shape features
        features['shape'] = self._extract_shape_features(image_array)
        
        # Extract deep learning features
        features['deep_features'] = self._extract_deep_features(image_array)
        
        return features
    
    def _extract_color_histogram(self, image_array):
        """
        Extract color histogram in HSV space.
        
        Args:
            image_array: numpy array of image (RGB)
        
        Returns:
            numpy array: Normalized histogram
        """
        try:
            # Convert RGB to HSV
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            
            # Calculate histogram
            # H: 180 bins, S: 256 bins, V: 256 bins
            hist = cv2.calcHist(
                [hsv],
                [0, 1, 2],  # H, S, V channels
                None,
                [30, 32, 32],  # Bins for H, S, V
                [0, 180, 0, 256, 0, 256]  # Ranges
            )
            
            # Normalize histogram
            hist = cv2.normalize(hist, hist).flatten()
            
            return hist
            
        except Exception as e:
            logger.error(f"Error extracting color histogram: {str(e)}")
            # Return zeros if extraction fails
            return np.zeros(30 * 32 * 32)
    
    def _extract_shape_features(self, image_array):
        """
        Extract shape features using edge detection and Hu moments.
        
        Args:
            image_array: numpy array of image (RGB)
        
        Returns:
            dict: Shape features
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Calculate edge orientation histogram
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            orientation = np.arctan2(sobely, sobelx)
            
            # Create histogram of orientations (16 bins)
            edge_hist, _ = np.histogram(
                orientation.flatten(),
                bins=16,
                range=(-np.pi, np.pi)
            )
            edge_hist = edge_hist.astype(np.float32)
            edge_hist = cv2.normalize(edge_hist, edge_hist).flatten()
            
            # Calculate Hu moments
            moments = cv2.moments(gray)
            hu_moments = cv2.HuMoments(moments).flatten()
            
            # Log transform Hu moments for better numerical stability
            hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-10)
            
            return {
                'edge_hist': edge_hist,
                'hu_moments': hu_moments
            }
            
        except Exception as e:
            logger.error(f"Error extracting shape features: {str(e)}")
            return {
                'edge_hist': np.zeros(16, dtype=np.float32),
                'hu_moments': np.zeros(7, dtype=np.float32)
            }
    
    def _extract_deep_features(self, image_array):
        """
        Extract deep learning features using ResNet50.
        
        Args:
            image_array: numpy array of image (RGB)
        
        Returns:
            numpy array: Feature vector (2048-dimensional)
        """
        try:
            # Resize to ResNet50 input size
            image_resized = cv2.resize(image_array, self.input_shape)
            
            # Add batch dimension
            image_batch = np.expand_dims(image_resized, axis=0)
            
            # Preprocess for ResNet50
            image_preprocessed = preprocess_input(image_batch)
            
            # Extract features
            features = self.model.predict(image_preprocessed, verbose=0)
            
            # Flatten to 1D array
            features = features.flatten()
            
            # Normalize
            features = features / (np.linalg.norm(features) + 1e-8)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting deep features: {str(e)}")
            # Return zeros if extraction fails
            return np.zeros(2048)
    
    def save_features(self, features, filepath):
        """
        Save features to disk using pickle.
        
        Args:
            features: Feature dictionary
            filepath: Path to save file
        """
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(features, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            logger.info(f"Features saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving features: {str(e)}", exc_info=True)
            raise
    
    def load_features(self, filepath):
        """
        Load features from disk.
        
        Args:
            filepath: Path to feature file
        
        Returns:
            dict: Feature dictionary
        """
        try:
            with open(filepath, 'rb') as f:
                features = pickle.load(f)
            
            logger.info(f"Features loaded from {filepath}")
            return features
            
        except Exception as e:
            logger.error(f"Error loading features: {str(e)}", exc_info=True)
            raise


# Initialize TensorFlow logging
tf.get_logger().setLevel('ERROR')
