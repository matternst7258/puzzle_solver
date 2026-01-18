# PuzzleSolver AI

A locally-hosted web application that uses computer vision and deep learning to help you find where puzzle pieces belong in a complete puzzle image.

## Features

- 🧩 **Accurate Piece Matching** - Uses TensorFlow and ResNet50 for high-accuracy feature extraction
- 🔒 **Privacy-First** - Puzzle piece images are processed in memory and immediately discarded (never saved to disk)
- 💾 **Puzzle Library** - Save multiple complete puzzle images for ongoing work
- 🔄 **Auto-Orientation** - Automatically detects correct piece orientation (0°, 90°, 180°, 270°)
- ✅ **Quality Validation** - Checks image quality before processing to ensure accurate results
- 📍 **Visual Results** - Shows match locations with confidence scores overlaid on puzzle image
- 🐳 **Docker-Based** - Easy deployment with Docker and docker-compose

## Requirements

- Docker Desktop (for macOS)
- 4GB+ RAM recommended
- 2GB+ disk space for Docker images

## Quick Start

### Option 1: Using Startup Scripts (Recommended)

The easiest way to start PuzzleSolver:

```bash
# Make scripts executable (first time only)
chmod +x start.sh stop.sh

# Start the application
./start.sh
```

The script will:
- Check that Docker is installed and running
- Create necessary directories
- Build the Docker image
- Start the container
- Wait for the app to be ready
- Open your browser automatically (macOS)

**To stop the application:**

```bash
./stop.sh
```

This will gracefully shut down the container and optionally clean up data.

### Option 2: Using docker-compose

```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down
```

### Option 3: Using Docker directly

```bash
# Build the image
docker build -t puzzlesolver:latest .

# Run the container
docker run -d \
  --name puzzlesolver \
  -p 8000:8000 \
  -v $(pwd)/saved_puzzles:/app/saved_puzzles \
  -v $(pwd)/logs:/app/logs \
  puzzlesolver:latest

# Stop the container
docker stop puzzlesolver
docker rm puzzlesolver
```

### Access the Application

Once started, open your browser and navigate to:
```
http://localhost:8000/puzzle_solver/
```

## Usage Guide

### Step 1: Load Your Puzzle

Choose one of two options:
- **Upload Image** - Select a puzzle image file from your computer
- **Enter URL** - Provide a direct URL to a puzzle image

### Step 2: Confirm and Save (Optional)

- Preview the puzzle image
- Optionally name and save it for future use
- Click "Continue"

### Step 3: Upload Puzzle Piece

- Upload a photo of your puzzle piece
- Supported formats: JPEG, PNG, HEIC (iPhone), WebP
- Maximum file size: 10MB

**Tips for Best Results:**
- Use good lighting
- Place piece on a contrasting background
- Keep the piece fully visible in frame
- Avoid blurry or out-of-focus photos

### Step 4: View Results

The app will show:
- **Best match location** highlighted on the puzzle image
- **Confidence score** (0-100%)
- **Required rotation** if piece needs to be turned
- **Alternative matches** if confidence > 80%
- **Low confidence warning** if best match < 80%

### Step 5: Analyze More Pieces

- Click "Analyze Another Piece" to continue with the same puzzle
- Click "Change Puzzle" to work on a different puzzle

## Privacy & Security

### What Gets Saved:
- ✅ Complete puzzle images (when you choose to save them)
- ✅ Puzzle names and metadata

### What NEVER Gets Saved:
- ❌ Individual puzzle piece photos
- ❌ Processing history or logs of piece uploads
- ❌ Any personal information

**Your piece images are:**
- Processed entirely in server memory
- Immediately discarded after analysis
- Never written to disk
- Never logged or recorded

## Project Structure

```
puzzlesolver/
├── start.sh                    # Startup script
├── stop.sh                     # Shutdown script
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── app.py                      # Main Flask application
├── README.md                   # This file
├── .gitignore
├── .dockerignore
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── api/                    # API routes and handlers
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── puzzle_service.py
│   │   ├── matching_service.py
│   │   └── image_service.py
│   ├── models/                 # ML models and feature extraction
│   │   ├── __init__.py
│   │   └── feature_extractor.py
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── quality_check.py
│       └── validators.py
│
├── frontend/                   # Frontend application
│   └── public/
│       └── index.html
│
├── saved_puzzles/              # Stored puzzle images (created on first run)
├── temp/                       # Temporary processing (created on first run)
└── logs/                       # Application logs (created on first run)
```

## API Endpoints

### Health Check
```
GET /puzzle_solver/api/health
```

### Upload Puzzle Image
```
POST /puzzle_solver/api/puzzles/upload
Content-Type: multipart/form-data

Fields:
- file: Image file
- name: (optional) Puzzle name
```

### Download Puzzle from URL
```
POST /puzzle_solver/api/puzzles/from-url
Content-Type: application/json

Body:
{
  "url": "https://example.com/puzzle.jpg",
  "name": "My Puzzle"
}
```

### List Saved Puzzles
```
GET /puzzle_solver/api/puzzles
```

### Get Puzzle Details
```
GET /puzzle_solver/api/puzzles/{puzzle_id}
```

### Delete Puzzle
```
DELETE /puzzle_solver/api/puzzles/{puzzle_id}
```

### Analyze Puzzle Piece
```
POST /puzzle_solver/api/analyze
Content-Type: multipart/form-data

Fields:
- piece: Piece image file
- puzzle_id: Puzzle UUID
```

## Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - SECRET_KEY=your-secret-key-here
  - TF_CPP_MIN_LOG_LEVEL=2          # TensorFlow logging (0=all, 3=errors only)
  - CUDA_VISIBLE_DEVICES=-1         # -1=CPU only, 0=use GPU
```

### Resource Limits

Adjust CPU and memory limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
```

## Troubleshooting

### Application Won't Start

**Check Docker is running:**
```bash
docker info
```

**Check if port 8000 is already in use:**
```bash
lsof -i :8000
# Kill the process or change port in docker-compose.yml
```

**View logs:**
```bash
docker logs -f puzzlesolver
# or
docker-compose logs -f
```

### Slow Performance

- Close other applications to free up memory
- Increase resource limits in docker-compose.yml
- Processing 20-30 seconds per piece is normal for accuracy

### Image Quality Errors

If you receive "Image quality insufficient" errors:
- Ensure good lighting when photographing pieces
- Use a contrasting background
- Keep camera steady and in focus
- Try uploading a higher resolution image

### URL Download Fails

If downloading puzzle from URL fails:
- Verify the URL is a direct link to an image file
- Check your internet connection
- Try uploading the image file manually instead

### Container Keeps Restarting

```bash
# Check logs for errors
docker logs puzzlesolver

# Check health status
docker inspect puzzlesolver | grep Health -A 10
```

## Development

### Running in Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask development server
export FLASK_ENV=development
python app.py
```

### Running Tests

```bash
# Run unit tests (once implemented)
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

## Technical Details

### Matching Algorithm

1. **Feature Extraction** - Uses ResNet50 pre-trained on ImageNet
2. **Multi-Stage Matching:**
   - Color histogram comparison (HSV space)
   - Shape matching (edge orientation)
   - Deep feature matching (2048-dim vectors)
3. **Multi-Orientation** - Tests all 4 rotations (0°, 90°, 180°, 270°)
4. **Confidence Scoring** - Weighted combination of color, shape, and feature similarity:
   - Color similarity: 25%
   - Shape matching: 25%
   - Deep features: 50%

### Processing Time

- Puzzle upload: 2-5 seconds (one-time preprocessing)
- Piece analysis: 20-30 seconds (includes all 4 orientations)

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- HEIC (.heic) - iPhone photos
- WebP (.webp)

### Size Limits

- Maximum file size: 10MB
- Automatic resizing: Large images resized to max 2048x2048
- Minimum dimensions: 200x200 pixels

## Useful Commands

**View application logs:**
```bash
docker logs -f puzzlesolver
```

**Restart the application:**
```bash
docker restart puzzlesolver
# or
docker-compose restart
```

**Access container shell:**
```bash
docker exec -it puzzlesolver /bin/bash
```

**Clean up all data:**
```bash
# WARNING: This deletes all saved puzzles!
rm -rf saved_puzzles/* logs/* temp/*
```

**Remove everything and start fresh:**
```bash
./stop.sh  # Follow prompts to remove image and data
./start.sh  # Rebuild and restart
```

## Data Management

### Saved Puzzles Location

All saved puzzles are stored in:
```
./saved_puzzles/
```

Each puzzle has its own directory:
```
saved_puzzles/
└── {puzzle-id}/
    ├── original.jpg      # Processed puzzle image
    ├── thumbnail.jpg     # 200x200 thumbnail
    ├── features.pkl      # Pre-computed features
    └── metadata.json     # Puzzle metadata
```

### Backup Your Puzzles

To backup your saved puzzles:
```bash
tar -czf puzzles-backup-$(date +%Y%m%d).tar.gz saved_puzzles/
```

To restore from backup:
```bash
tar -xzf puzzles-backup-YYYYMMDD.tar.gz
```

## License

[Your License Here]

## Support

For issues, questions, or contributions, please open an issue on the project repository.

## Acknowledgments

- TensorFlow for deep learning capabilities
- OpenCV for computer vision operations
- Flask for the web framework
- ResNet50 architecture for feature extraction
