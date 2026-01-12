"""
PuzzleSolver AI - Main Application
A web application for matching puzzle pieces to their location in complete puzzles.
"""

import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = 'temp'
app.config['PUZZLE_FOLDER'] = 'saved_puzzles'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PUZZLE_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Import routes after app creation to avoid circular imports
from src.api.routes import api_bp

# Register blueprints with prefix
app.register_blueprint(api_bp, url_prefix='/puzzle_solver/api')

# Serve React frontend
@app.route('/puzzle_solver/', defaults={'path': ''})
@app.route('/puzzle_solver/<path:path>')
def serve_frontend(path):
    """Serve the React frontend application."""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Root redirect
@app.route('/')
def root():
    """Redirect root to puzzle_solver."""
    from flask import redirect
    return redirect('/puzzle_solver/')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return {'success': False, 'error': 'Resource not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return {'success': False, 'error': 'Internal server error'}, 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors."""
    return {
        'success': False, 
        'error': 'File too large',
        'details': 'Maximum file size is 10MB'
    }, 413

if __name__ == '__main__':
    logger.info("Starting PuzzleSolver AI application...")
    logger.info(f"Puzzle storage: {app.config['PUZZLE_FOLDER']}")
    logger.info(f"Temporary storage: {app.config['UPLOAD_FOLDER']}")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False,
        threaded=True
    )