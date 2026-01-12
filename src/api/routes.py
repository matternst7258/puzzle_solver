"""
API Routes for PuzzleSolver
Handles all HTTP endpoints for puzzle management and piece analysis.
"""

import os
import gc
import logging
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from src.services.puzzle_service import PuzzleService
from src.services.matching_service import MatchingService
from src.services.image_service import ImageService
from src.utils.quality_check import check_image_quality
from src.utils.validators import validate_puzzle_upload, validate_piece_upload, validate_url

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize services
puzzle_service = PuzzleService()
matching_service = MatchingService()
image_service = ImageService()


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Docker healthcheck.
    Returns application status.
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'PuzzleSolver AI'
    }), 200


@api_bp.route('/puzzles/upload', methods=['POST'])
def upload_puzzle():
    """
    Upload a puzzle image file.
    
    Form data:
        file: Image file (required)
        name: Puzzle name (optional)
    
    Returns:
        JSON with puzzle_id and metadata
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        puzzle_name = request.form.get('name', 'Untitled Puzzle')
        
        # Validate file
        is_valid, error_msg = validate_puzzle_upload(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Read file into memory
        file_bytes = BytesIO(file.read())
        
        # Check image quality
        quality_ok, quality_msg, quality_score = check_image_quality(file_bytes)
        if not quality_ok:
            file_bytes.close()
            return jsonify({
                'success': False,
                'error': 'Image quality insufficient',
                'details': quality_msg,
                'quality_score': quality_score
            }), 400
        
        # Reset file pointer
        file_bytes.seek(0)
        
        # Process and save puzzle
        logger.info(f"Processing puzzle upload: {puzzle_name}")
        puzzle_data = puzzle_service.save_puzzle(file_bytes, puzzle_name)
        
        # Cleanup
        file_bytes.close()
        
        logger.info(f"Puzzle saved successfully: {puzzle_data['puzzle_id']}")
        return jsonify({
            'success': True,
            'puzzle_id': puzzle_data['puzzle_id'],
            'name': puzzle_data['name'],
            'dimensions': puzzle_data['dimensions'],
            'thumbnail_url': f"/puzzle_solver/api/puzzles/{puzzle_data['puzzle_id']}/thumbnail",
            'message': 'Puzzle processed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading puzzle: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to process puzzle',
            'details': str(e)
        }), 500


@api_bp.route('/puzzles/from-url', methods=['POST'])
def upload_puzzle_from_url():
    """
    Download and save a puzzle image from URL.
    
    JSON body:
        url: Image URL (required)
        name: Puzzle name (optional)
    
    Returns:
        JSON with puzzle_id and metadata
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'No URL provided'
            }), 400
        
        url = data['url']
        puzzle_name = data.get('name', 'Untitled Puzzle')
        
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Download image
        logger.info(f"Downloading puzzle from URL: {url}")
        file_bytes = image_service.download_from_url(url)
        
        if file_bytes is None:
            return jsonify({
                'success': False,
                'error': 'Failed to download image from URL',
                'details': 'Please upload the image file directly instead.'
            }), 400
        
        # Check image quality
        quality_ok, quality_msg, quality_score = check_image_quality(file_bytes)
        if not quality_ok:
            file_bytes.close()
            return jsonify({
                'success': False,
                'error': 'Image quality insufficient',
                'details': quality_msg,
                'quality_score': quality_score
            }), 400
        
        # Reset file pointer
        file_bytes.seek(0)
        
        # Process and save puzzle
        logger.info(f"Processing puzzle from URL: {puzzle_name}")
        puzzle_data = puzzle_service.save_puzzle(file_bytes, puzzle_name)
        
        # Cleanup
        file_bytes.close()
        
        logger.info(f"Puzzle saved successfully: {puzzle_data['puzzle_id']}")
        return jsonify({
            'success': True,
            'puzzle_id': puzzle_data['puzzle_id'],
            'name': puzzle_data['name'],
            'dimensions': puzzle_data['dimensions'],
            'thumbnail_url': f"/puzzle_solver/api/puzzles/{puzzle_data['puzzle_id']}/thumbnail"
        }), 200
        
    except Exception as e:
        logger.error(f"Error downloading puzzle from URL: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to download and process puzzle',
            'details': str(e)
        }), 500


@api_bp.route('/puzzles', methods=['GET'])
def list_puzzles():
    """
    Get list of all saved puzzles.
    
    Returns:
        JSON with array of puzzle metadata
    """
    try:
        puzzles = puzzle_service.list_puzzles()
        
        return jsonify({
            'success': True,
            'puzzles': puzzles
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing puzzles: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to list puzzles',
            'details': str(e)
        }), 500


@api_bp.route('/puzzles/<puzzle_id>', methods=['GET'])
def get_puzzle(puzzle_id):
    """
    Get details for a specific puzzle.
    
    Args:
        puzzle_id: UUID of the puzzle
    
    Returns:
        JSON with puzzle metadata
    """
    try:
        puzzle = puzzle_service.get_puzzle(puzzle_id)
        
        if puzzle is None:
            return jsonify({
                'success': False,
                'error': 'Puzzle not found'
            }), 404
        
        return jsonify({
            'success': True,
            'puzzle': puzzle
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting puzzle {puzzle_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get puzzle',
            'details': str(e)
        }), 500


@api_bp.route('/puzzles/<puzzle_id>/image', methods=['GET'])
def get_puzzle_image(puzzle_id):
    """
    Get the full puzzle image file.
    
    Args:
        puzzle_id: UUID of the puzzle
    
    Returns:
        Image file
    """
    try:
        image_path = puzzle_service.get_puzzle_image_path(puzzle_id)
        
        if image_path is None or not os.path.exists(image_path):
            return jsonify({
                'success': False,
                'error': 'Puzzle image not found'
            }), 404
        
        return send_file(image_path, mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Error serving puzzle image {puzzle_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to serve puzzle image'
        }), 500


@api_bp.route('/puzzles/<puzzle_id>/thumbnail', methods=['GET'])
def get_puzzle_thumbnail(puzzle_id):
    """
    Get the puzzle thumbnail image.
    
    Args:
        puzzle_id: UUID of the puzzle
    
    Returns:
        Thumbnail image file
    """
    try:
        thumbnail_path = puzzle_service.get_puzzle_thumbnail_path(puzzle_id)
        
        if thumbnail_path is None or not os.path.exists(thumbnail_path):
            return jsonify({
                'success': False,
                'error': 'Puzzle thumbnail not found'
            }), 404
        
        return send_file(thumbnail_path, mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Error serving puzzle thumbnail {puzzle_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to serve puzzle thumbnail'
        }), 500


@api_bp.route('/puzzles/<puzzle_id>', methods=['DELETE'])
def delete_puzzle(puzzle_id):
    """
    Delete a saved puzzle.
    
    Args:
        puzzle_id: UUID of the puzzle
    
    Returns:
        JSON confirmation
    """
    try:
        success = puzzle_service.delete_puzzle(puzzle_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Puzzle not found'
            }), 404
        
        logger.info(f"Puzzle deleted: {puzzle_id}")
        return jsonify({
            'success': True,
            'message': 'Puzzle deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting puzzle {puzzle_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to delete puzzle',
            'details': str(e)
        }), 500


@api_bp.route('/analyze', methods=['POST'])
def analyze_piece():
    """
    Analyze a puzzle piece and find matches in the puzzle.
    
    CRITICAL: Piece image is processed in memory only and immediately discarded.
    No piece images are ever saved to disk or logged.
    
    Form data:
        piece: Piece image file (required)
        puzzle_id: Puzzle UUID (required)
    
    Returns:
        JSON with match locations and confidence scores
    """
    piece_image = None
    piece_bytes = None
    piece_array = None
    
    try:
        # Validate request
        if 'piece' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No piece image provided'
            }), 400
        
        if 'puzzle_id' not in request.form:
            return jsonify({
                'success': False,
                'error': 'No puzzle_id provided'
            }), 400
        
        piece_file = request.files['piece']
        puzzle_id = request.form['puzzle_id']
        
        # Validate piece upload
        is_valid, error_msg = validate_piece_upload(piece_file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Verify puzzle exists
        puzzle = puzzle_service.get_puzzle(puzzle_id)
        if puzzle is None:
            return jsonify({
                'success': False,
                'error': 'Puzzle not found'
            }), 404
        
        # CRITICAL: Load piece into memory ONLY - never write to disk
        logger.info(f"Processing piece for puzzle {puzzle_id}")
        piece_bytes = BytesIO(piece_file.read())
        
        # Check piece image quality
        quality_ok, quality_msg, quality_score = check_image_quality(piece_bytes)
        if not quality_ok:
            # Immediate cleanup on quality failure
            piece_bytes.close()
            del piece_bytes
            gc.collect()
            
            return jsonify({
                'success': False,
                'error': 'Piece image quality insufficient',
                'details': quality_msg,
                'quality_score': quality_score
            }), 400
        
        # Reset file pointer
        piece_bytes.seek(0)
        
        # Process piece and find matches
        import time
        start_time = time.time()
        
        matches = matching_service.find_matches(piece_bytes, puzzle_id)
        
        processing_time = time.time() - start_time
        
        # CRITICAL: Immediate cleanup of piece data
        if piece_bytes:
            piece_bytes.close()
        del piece_bytes
        del piece_file
        gc.collect()
        
        # Prepare response
        if not matches or len(matches) == 0:
            logger.info(f"No matches found for piece")
            return jsonify({
                'success': True,
                'processing_time': round(processing_time, 2),
                'best_match': None,
                'alternatives': [],
                'warning': 'No confident match found. Please try a different piece or retake the photo.'
            }), 200
        
        best_match = matches[0]
        
        # Filter alternatives: only show if confidence > 80%
        alternatives = []
        if best_match['confidence'] >= 80:
            alternatives = [m for m in matches[1:] if m['confidence'] >= 80]
        
        # Prepare response based on confidence
        response = {
            'success': True,
            'processing_time': round(processing_time, 2),
            'best_match': best_match,
            'alternatives': alternatives,
            'warning': None
        }
        
        # Add warning if low confidence
        if best_match['confidence'] < 80:
            response['warning'] = 'Low confidence match. This may not be accurate.'
            logger.info(f"Low confidence match: {best_match['confidence']}%")
        else:
            logger.info(f"Match found with {best_match['confidence']}% confidence")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error analyzing piece: {str(e)}", exc_info=True)
        
        # CRITICAL: Ensure cleanup even on error
        if piece_bytes:
            try:
                piece_bytes.close()
            except:
                pass
        if piece_image:
            try:
                piece_image.close()
            except:
                pass
        del piece_bytes
        del piece_image
        del piece_array
        gc.collect()
        
        return jsonify({
            'success': False,
            'error': 'Failed to analyze piece',
            'details': str(e)
        }), 500