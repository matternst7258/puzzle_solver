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

### 1. Clone or Download

```bash
git clone <repository-url>
cd puzzlesolver
```

### 2. Build and Run

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or using docker directly
docker build -t puzzlesolver:latest .
docker run -d --name puzzlesolver -p 8000:8000 -v $(pwd)/saved_puzzles:/app/saved_puzzles puzzlesolver:latest
```

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:8000/puzzle_solver/
```

### 4. Stop the Application

```bash
# Using docker-compose
docker-compose down

# Or using docker directly
docker stop puzzlesolver
docker rm puzzlesolver
```

## Usage Guide

### Step 1: Load Your Puzzle

Choose one of three options:
- **Upload Image** - Select a puzzle image file from your computer
- **Enter URL** - Provide a direct URL to a puzzle image
- **Load Saved** - Select from previously saved puzzles

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
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── app.py                      # Main Flask application
├── README.md                   # This file
│
├── src/                        # Source code
│   ├── api/                    # API routes and handlers
│   ├── services/               # Business logic
│   ├── models/                 # ML models and feature extraction
│   └── utils/                  # Utility functions
│
├── frontend/                   # React frontend application
│   ├── src/
│   └── public/
│
├── saved_puzzles/              # Stored puzzle images (mounted volume)
├── temp/                       # Temporary processing (not persisted)
└── logs/                       # Application logs
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

**Check if port 8000 is already in use:**
```bash
lsof -i :8000
# Kill the process using the port or change port in docker-compose.yml
```

**View logs:**
```bash
docker-compose logs -f puzzlesolver
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

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Running Tests

```bash
# Run unit tests
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
4. **Confidence Scoring** - Weighted combination of color, shape, and feature similarity

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

## License

[Your License Here]

## Support

For issues, questions, or contributions, please [open an issue](your-repo-url/issues).

## Acknowledgments

- TensorFlow for deep learning capabilities
- OpenCV for computer vision operations
- Flask for the web framework
- React for the frontend interface
