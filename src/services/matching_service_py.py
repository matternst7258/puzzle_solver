"""
Matching Service
Handles puzzle piece matching against complete puzzles.
Uses multi-stage filtering and deep learning features for accuracy.
"""

import logging
import numpy as np
from PIL import Image
from io import BytesIO
import cv2
from scipy.spatial.distance import cosine

from src.models.feature_extractor import FeatureExtractor
from src.services.puzzle_service import PuzzleService

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for matching puzzle pieces to puzzle locations."""
    
    def __init__(self):
        """Initialize matching service."""
        self.feature_extractor = FeatureExtractor()
        self.puzzle_service = PuzzleService()
        
        logger.info("MatchingService initialized")
    
    def find_matches(self, piece_bytes, puzzle_id, top_k=5):
        """
        Find matching locations for a puzzle piece.
        
        CRITICAL: piece_bytes is processed in memory only and immediately discarded.
        
        Args:
            piece_bytes: BytesIO object containing piece image
            puzzle_id: UUID of the puzzle to match against
            top_k: Number of top matches to return
        
        Returns:
            list: Top matches with confidence scores and locations
        """
        try:
            logger.info(f"Starting piece matching for puzzle {puzzle_id}")
            
            # Load puzzle features
            puzzle_features = self.puzzle_service.load_puzzle_features(puzzle_id)
            if puzzle_features is None:
                logger.error(f"Could not load features for puzzle {puzzle_id}")
                return []
            
            puzzle_metadata = self.puzzle_service.get_puzzle(puzzle_id)
            if puzzle_metadata is None:
                logger.error(f"Could not load metadata for puzzle {puzzle_id}")
                return []
            
            # Extract piece features for all orientations
            piece_features_list = self._extract_piece_features_all_orientations(piece_bytes)
            
            logger.info(f"Extracted features for {len(piece_features_list)} orientations")
            
            # Match against puzzle regions for each orientation
            all_matches = []
            
            for rotation_deg, piece_features in piece_features_list:
                matches = self._match_piece_to_puzzle(
                    piece_features,
                    puzzle_features,
                    puzzle_metadata,
                    rotation_deg
                )
                all_matches.extend(matches)
            
            # Sort all matches by confidence
            all_matches.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Return top K matches
            top_matches = all_matches[:top_k]
            
            logger.info(f"Found {len(top_matches)} top matches. Best confidence: {top_matches[0]['confidence']:.1f}%" if top_matches else "No matches found")
            
            return top_matches
            
        except Exception as e:
            logger.error(f"Error in find_matches: {str(e)}", exc_info=True)
            return []
    
    def _extract_piece_features_all_orientations(self, piece_bytes):
        """
        Extract features for piece at all 4 orientations.
        
        Args:
            piece_bytes: BytesIO object containing piece image
        
        Returns:
            list: [(rotation_degrees, features), ...]
        """
        try:
            # Load image
            piece_bytes.seek(0)
            piece_image = Image.open(piece_bytes)
            
            # Convert to RGB if necessary
            if piece_image.mode != 'RGB':
                piece_image = piece_image.convert('RGB')
            
            # Resize to standard size (512x512)
            piece_image = piece_image.resize((512, 512), Image.Resampling.LANCZOS)
            
            results = []
            
            # Extract features for each rotation
            for rotation_deg in [0, 90, 180, 270]:
                # Rotate image
                if rotation_deg == 0:
                    rotated = piece_image
                else:
                    rotated = piece_image.rotate(-rotation_deg, expand=True)
                
                # Extract features
                features = self.feature_extractor.extract_piece_features(rotated)
                results.append((rotation_deg, features))
                
                logger.debug(f"Extracted features for {rotation_deg}° rotation")
                
                # Close rotated image if it's not the original
                if rotation_deg != 0:
                    rotated.close()
            
            # Cleanup
            piece_image.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error extracting piece features: {str(e)}", exc_info=True)
            return []
    
    def _match_piece_to_puzzle(self, piece_features, puzzle_features, puzzle_metadata, rotation_deg):
        """
        Match a piece (at specific orientation) against all puzzle regions.
        
        Args:
            piece_features: Extracted features from piece
            puzzle_features: Pre-computed puzzle features
            puzzle_metadata: Puzzle metadata with dimensions
            rotation_deg: Rotation applied to piece (0, 90, 180, 270)
        
        Returns:
            list: Matches with confidence scores
        """
        try:
            matches = []
            
            puzzle_regions = puzzle_features['regions']
            
            # Multi-stage matching for each region
            for region in puzzle_regions:
                # Stage 1: Color similarity (fast filter)
                color_score = self._compare_color_histograms(
                    piece_features['color_hist'],
                    region['color_hist']
                )
                
                # Skip if color is very different (< 30% similar)
                if color_score < 0.3:
                    continue
                
                # Stage 2: Shape similarity
                shape_score = self._compare_shape_features(
                    piece_features['shape'],
                    region['shape']
                )
                
                # Stage 3: Deep feature similarity
                feature_score = self._compare_deep_features(
                    piece_features['deep_features'],
                    region['deep_features']
                )
                
                # Weighted confidence score
                confidence = (
                    0.25 * color_score * 100 +      # 25% weight
                    0.25 * shape_score * 100 +      # 25% weight
                    0.50 * feature_score * 100      # 50% weight (most important)
                )
                
                # Only consider matches above 40% confidence
                if confidence >= 40:
                    # Prepare match data
                    match = {
                        'confidence': round(confidence, 1),
                        'location': {
                            'x': region['x'],
                            'y': region['y'],
                            'width': region['width'],
                            'height': region['height']
                        },
                        'rotation_needed': rotation_deg,
                        'description': self._generate_location_description(
                            region,
                            puzzle_metadata,
                            rotation_deg
                        )
                    }
                    
                    matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error matching piece to puzzle: {str(e)}", exc_info=True)
            return []
    
    def _compare_color_histograms(self, hist1, hist2):
        """
        Compare two color histograms using correlation.
        
        Args:
            hist1: First histogram
            hist2: Second histogram
        
        Returns:
            float: Similarity score (0-1)
        """
        try:
            # Use correlation method (returns value between -1 and 1)
            correlation = cv2.compareHist(
                hist1.astype(np.float32),
                hist2.astype(np.float32),
                cv2.HISTCMP_CORREL
            )
            
            # Convert to 0-1 range
            similarity = (correlation + 1) / 2
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error comparing color histograms: {str(e)}")
            return 0.0
    
    def _compare_shape_features(self, shape1, shape2):
        """
        Compare shape features (edge orientations, Hu moments).
        
        Args:
            shape1: First shape feature dict
            shape2: Second shape feature dict
        
        Returns:
            float: Similarity score (0-1)
        """
        try:
            # Compare edge orientation histograms
            edge_hist1 = shape1.get('edge_hist')
            edge_hist2 = shape2.get('edge_hist')
            
            if edge_hist1 is not None and edge_hist2 is not None:
                edge_correlation = cv2.compareHist(
                    edge_hist1.astype(np.float32),
                    edge_hist2.astype(np.float32),
                    cv2.HISTCMP_CORREL
                )
                edge_similarity = (edge_correlation + 1) / 2
            else:
                edge_similarity = 0.5
            
            # Compare Hu moments if available
            hu1 = shape1.get('hu_moments')
            hu2 = shape2.get('hu_moments')
            
            if hu1 is not None and hu2 is not None:
                # Use Euclidean distance, normalized
                hu_distance = np.linalg.norm(hu1 - hu2)
                hu_similarity = np.exp(-hu_distance)
            else:
                hu_similarity = 0.5
            
            # Average of edge and Hu moment similarities
            similarity = (edge_similarity + hu_similarity) / 2
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error comparing shape features: {str(e)}")
            return 0.5
    
    def _compare_deep_features(self, features1, features2):
        """
        Compare deep learning features using cosine similarity.
        
        Args:
            features1: First feature vector
            features2: Second feature vector
        
        Returns:
            float: Similarity score (0-1)
        """
        try:
            # Ensure features are numpy arrays
            f1 = np.array(features1).flatten()
            f2 = np.array(features2).flatten()
            
            # Check if features are valid
            if len(f1) == 0 or len(f2) == 0:
                return 0.0
            
            # Normalize features
            f1 = f1 / (np.linalg.norm(f1) + 1e-8)
            f2 = f2 / (np.linalg.norm(f2) + 1e-8)
            
            # Cosine similarity (1 - cosine distance)
            similarity = 1 - cosine(f1, f2)
            
            # Ensure in valid range
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error comparing deep features: {str(e)}")
            return 0.0
    
    def _generate_location_description(self, region, puzzle_metadata, rotation_deg):
        """
        Generate human-readable description of match location.
        
        Args:
            region: Region data with x, y coordinates
            puzzle_metadata: Puzzle metadata with dimensions
            rotation_deg: Required rotation
        
        Returns:
            str: Location description
        """
        try:
            width = puzzle_metadata['dimensions']['width']
            height = puzzle_metadata['dimensions']['height']
            
            x = region['x']
            y = region['y']
            
            # Determine horizontal position
            if x < width * 0.33:
                h_pos = "left"
            elif x < width * 0.67:
                h_pos = "center"
            else:
                h_pos = "right"
            
            # Determine vertical position
            if y < height * 0.33:
                v_pos = "upper"
            elif y < height * 0.67:
                v_pos = "middle"
            else:
                v_pos = "lower"
            
            # Combine positions
            if v_pos == "middle" and h_pos == "center":
                position = "Center area"
            elif v_pos == "middle":
                position = f"{h_pos.capitalize()} side"
            elif h_pos == "center":
                position = f"{v_pos.capitalize()} area"
            else:
                position = f"{v_pos.capitalize()}-{h_pos} quadrant"
            
            # Add rotation if needed
            if rotation_deg == 0:
                rotation_text = ""
            elif rotation_deg == 90:
                rotation_text = ", rotated 90° clockwise"
            elif rotation_deg == 180:
                rotation_text = ", rotated 180°"
            elif rotation_deg == 270:
                rotation_text = ", rotated 90° counter-clockwise"
            else:
                rotation_text = f", rotated {rotation_deg}°"
            
            return f"{position}{rotation_text}"
            
        except Exception as e:
            logger.error(f"Error generating location description: {str(e)}")
            return "Unknown location"
