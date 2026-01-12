# Puzzle Piece Placement Assistant - Design Document

## 1. Executive Summary

**Application Name:** PuzzleSolver AI (Local Docker Edition)

**Purpose:** A locally-hosted web application that analyzes photographs of individual puzzle pieces and matches them against complete puzzle images to determine the most likely placement location with confidence scoring.

**Deployment Model:** Docker container running on macOS, accessible via `localhost:8000/puzzle_solver`

**Core Privacy Principle:** Puzzle piece images are processed server-side but immediately discarded after analysis with no persistent storage or logging.

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Browser Client                         │
│  (React SPA)                                            │
│  - Multi-step Wizard UI                                 │
│  - Image Upload Interface                               │
│  - Results Visualization with Overlay                   │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────────────────┐
│         Python Flask Server (in Docker)                 │
│  - Image Upload Endpoints                               │
│  - TensorFlow-based Processing                          │
│  - Puzzle Management API                                │
│  - Temporary Piece Processing (immediate deletion)      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Local File System (Docker Volume)          │
│  ./saved_puzzles/                                       │
│  ├── puzzle_1/                                          │
│  │   ├── original.jpg                                   │
│  │   └── metadata.json                                  │
│  ├── puzzle_2/                                          │
│  └── ...                                                │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

**Frontend:**
- React 18+ with JavaScript
- Tailwind CSS for styling
- Axios for HTTP requests
- React Router for multi-step wizard navigation

**Backend:**
- Python 3.10+
- Flask web framework
- TensorFlow 2.x for computer vision
- OpenCV (cv2) for image processing
- NumPy for numerical operations
- Pillow (PIL) for image manipulation

**Deployment:**
- Docker container
- Base image: python:3.10-slim
- Port mapping: 8000:8000
- Volume mount: ./saved_puzzles

**Key Libraries:**
- `tensorflow` - Deep learning and feature extraction
- `opencv-python` - Computer vision operations
- `pillow` - Image processing and manipulation
- `numpy` - Array operations
- `flask` - Web server
- `flask-cors` - Cross-origin requests
- `werkzeug` - Secure file handling

## 3. Core Features & Functionality

### 3.1 Multi-Step Wizard Flow

**Step 1: Puzzle Selection**
- Option A: Upload puzzle image file
- Option B: Enter URL to download puzzle image
- Display preview of selected puzzle
- "Continue" button to proceed

**Step 2: Puzzle Management (Optional)**
- Save current puzzle to library
- Load previously saved puzzle
- View saved puzzles grid
- Delete saved puzzles

**Step 3: Piece Upload**
- Upload puzzle piece image
- Image quality validation
- Automatic resize/compress
- Loading indicator during upload

**Step 4: Processing**
- Server-side analysis with progress indicator
- Piece orientation detection and correction
- Feature extraction and matching
- "Processing..." state with estimated time

**Step 5: Results Display**
- Interactive puzzle image with highlighted match location
- Confidence score display
- Top match shown with visual overlay
- Alternative matches shown only if confidence > 80%
- Low confidence warning if best match < 80%
- "Analyze Another Piece" button
- "Change Puzzle" button

### 3.2 Puzzle Image Workflow

**Puzzle Upload Process:**
1. User uploads puzzle image or provides URL
2. Server validates image format and size
3. Server checks image quality (blur detection, contrast check)
4. If quality insufficient: reject and request re-upload
5. If quality sufficient: resize to optimal resolution (max 2048x2048)
6. Compress to reduce storage (JPEG quality 85%)
7. Extract features for matching (done once, cached)
8. Return success with puzzle ID

**Puzzle Saving:**
- User can name and save puzzle
- Stored in `./saved_puzzles/{puzzle_id}/`
- Contains: original image, metadata (name, date, dimensions)
- Pre-computed features stored for fast matching

### 3.3 Piece Image Workflow (Security-Critical)

**Piece Processing Flow:**
```
1. User uploads piece image via POST request
   ↓
2. Server receives file in request
   ↓
3. Server stores in memory (BytesIO object) - NEVER writes to disk
   ↓
4. Immediate quality check:
   - Blur detection (Laplacian variance)
   - Contrast check
   - Size validation
   ↓
5. If quality fails: return error immediately, discard image
   ↓
6. If quality passes: 
   - Resize to standard size (512x512)
   - Background removal
   - Edge detection
   - Feature extraction (TensorFlow)
   - Orientation detection (try 0°, 90°, 180°, 270°)
   ↓
7. Match against puzzle features:
   - Color histogram comparison
   - Shape matching
   - Feature descriptor matching
   - Calculate confidence scores
   ↓
8. Generate response with match locations
   ↓
9. IMMEDIATE CLEANUP:
   - Clear all variables holding image data
   - Clear TensorFlow computation graph
   - Python garbage collection
   - Return response
   ↓
10. NO logging of piece image or features
```

**Critical Security Measures:**
- Piece image NEVER written to disk
- No logging of piece uploads
- Immediate memory cleanup after processing
- No caching of piece data
- Processing happens in single request/response cycle

### 3.4 Image Quality Validation

**Quality Checks (performed immediately on upload):**

1. **Format Validation:**
   - Supported: JPEG, PNG, HEIC (iPhone), WebP
   - Magic byte verification
   - MIME type checking

2. **Size Limits:**
   - Max file size: 10MB
   - Max dimensions: 4000x4000 pixels
   - Min dimensions: 200x200 pixels

3. **Quality Assessment:**
   - Blur detection using Laplacian variance (threshold: 100)
   - Contrast check using histogram analysis
   - Lighting assessment (not too dark/bright)

4. **Auto-Processing:**
   - Resize if too large (maintain aspect ratio)
   - Compress to JPEG quality 85%
   - Strip EXIF metadata
   - Normalize orientation

**Rejection Criteria:**
- Image too blurry (variance < 100)
- Insufficient contrast
- Too dark or overexposed
- Corrupted file
- Unsupported format

**User Feedback:**
- Clear error message explaining issue
- Suggestions for improvement
- Option to retry upload

## 4. Matching Algorithm (Accuracy-Focused)

### 4.1 Feature Extraction Strategy

**Piece Analysis:**
1. **Preprocessing:**
   - Background removal using GrabCut algorithm
   - Edge detection with Canny
   - Morphological operations to clean edges
   
2. **Shape Features:**
   - Contour extraction
   - Shape descriptors (Hu moments)
   - Edge orientation histogram
   
3. **Color Features:**
   - HSV color histogram (more robust than RGB)
   - Dominant color extraction
   - Color distribution analysis
   
4. **Texture Features:**
   - Deep learning features using TensorFlow
   - Pre-trained MobileNetV2 or ResNet50 (transfer learning)
   - Extract features from final conv layer
   - 1280-dimensional feature vector

5. **Orientation Handling:**
   - Extract features at 0°, 90°, 180°, 270°
   - Store all 4 orientations
   - Match against all orientations
   - Report best match with required rotation

**Puzzle Pre-Processing:**
1. **Grid Detection:**
   - Attempt to identify piece boundaries
   - Create sliding window grid if boundaries unclear
   - Grid resolution: 50x50 pixel windows with overlap
   
2. **Feature Extraction Per Region:**
   - Extract same features for each grid cell
   - Build feature database
   - Store spatial coordinates
   
3. **Caching:**
   - Save pre-computed features with puzzle
   - Reload for subsequent piece matching
   - Reduces processing time from 30s to 5s

### 4.2 Matching Process

**Multi-Stage Matching Pipeline:**

**Stage 1: Color Pre-filtering (Fast)**
- Compare HSV histograms
- Use chi-square distance
- Keep top 20% of candidate regions
- Processing time: ~0.5 seconds

**Stage 2: Shape Matching (Medium)**
- Compare edge orientations
- Compare shape descriptors
- Keep top 10% of candidates
- Processing time: ~2 seconds

**Stage 3: Deep Feature Matching (Slow but Accurate)**
- Compare TensorFlow feature vectors
- Use cosine similarity
- Rank all candidates
- Processing time: ~5-10 seconds

**Stage 4: Multi-Orientation Matching**
- Repeat stages 1-3 for all 4 orientations
- Track best match per orientation
- Select overall best match
- Report required rotation angle
- Processing time: ~20-30 seconds total

**Confidence Scoring:**
```python
confidence = (
    0.25 * color_similarity +      # 25% weight
    0.25 * shape_similarity +      # 25% weight
    0.50 * feature_similarity      # 50% weight - most important
) * 100
```

**Result Filtering:**
- If best match > 80%: Show best match + alternatives > 80%
- If best match < 80%: Show only best match with "Low Confidence" warning
- If best match < 40%: Show "No confident match found"

### 4.3 Optimization for Accuracy

**Model Selection:**
- Use ResNet50 (more accurate) over MobileNet (faster)
- Pre-trained on ImageNet
- Fine-tune on puzzle piece dataset (if available)

**Feature Dimensions:**
- Use 2048-dim features from ResNet50
- Higher dimensionality = better discrimination

**Multiple Scales:**
- Process piece at multiple scales (0.8x, 1.0x, 1.2x)
- Helps with pieces that might be slightly different size
- Take best match across scales

**Ensemble Matching:**
- Combine results from multiple algorithms
- Vote among top candidates
- More robust to edge cases

## 5. API Specification

### 5.1 Endpoints

**Base URL:** `http://localhost:8000/puzzle_solver`

```
POST   /api/puzzles/upload
POST   /api/puzzles/from-url
GET    /api/puzzles
GET    /api/puzzles/{puzzle_id}
DELETE /api/puzzles/{puzzle_id}
POST   /api/analyze
GET    /api/health
```

### 5.2 Detailed Endpoint Specifications

#### POST /api/puzzles/upload

**Purpose:** Upload a puzzle image file

**Request:**
```
Content-Type: multipart/form-data

Fields:
- file: (binary) The puzzle image file
- name: (string, optional) Puzzle name
```

**Response (Success - 200):**
```json
{
  "success": true,
  "puzzle_id": "uuid-string",
  "name": "My Puzzle",
  "dimensions": {
    "width": 2048,
    "height": 1536
  },
  "thumbnail_url": "/api/puzzles/uuid-string/thumbnail",
  "message": "Puzzle processed successfully"
}
```

**Response (Quality Check Failed - 400):**
```json
{
  "success": false,
  "error": "Image quality insufficient",
  "details": "Image appears too blurry. Please retake photo with better focus.",
  "quality_score": 45.2
}
```

#### POST /api/puzzles/from-url

**Purpose:** Download puzzle image from URL

**Request:**
```json
{
  "url": "https://example.com/puzzle.jpg",
  "name": "My Puzzle"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "puzzle_id": "uuid-string",
  "name": "My Puzzle",
  "dimensions": {
    "width": 2048,
    "height": 1536
  },
  "thumbnail_url": "/api/puzzles/uuid-string/thumbnail"
}
```

**Response (URL Failed - 400):**
```json
{
  "success": false,
  "error": "Failed to download image from URL",
  "details": "Please upload the image file directly instead."
}
```

#### POST /api/analyze

**Purpose:** Analyze a puzzle piece and find matches

**Request:**
```
Content-Type: multipart/form-data

Fields:
- piece: (binary) The puzzle piece image
- puzzle_id: (string) The puzzle to match against
```

**Response (Success - 200):**
```json
{
  "success": true,
  "processing_time": 28.4,
  "best_match": {
    "confidence": 87.5,
    "location": {
      "x": 512,
      "y": 768,
      "width": 100,
      "height": 100
    },
    "rotation_needed": 90,
    "description": "Upper-right quadrant, rotated 90° clockwise"
  },
  "alternatives": [
    {
      "confidence": 82.1,
      "location": {
        "x": 612,
        "y": 868,
        "width": 100,
        "height": 100
      },
      "rotation_needed": 0
    }
  ],
  "warning": null
}
```

**Response (Low Confidence - 200):**
```json
{
  "success": true,
  "processing_time": 27.8,
  "best_match": {
    "confidence": 65.3,
    "location": {
      "x": 412,
      "y": 568,
      "width": 100,
      "height": 100
    },
    "rotation_needed": 180,
    "description": "Center area, rotated 180°"
  },
  "alternatives": [],
  "warning": "Low confidence match. This may not be accurate."
}
```

**Response (Quality Check Failed - 400):**
```json
{
  "success": false,
  "error": "Piece image quality insufficient",
  "details": "Image appears blurry or poorly lit. Please retake the photo.",
  "quality_score": 52.1
}
```

#### GET /api/puzzles

**Purpose:** List all saved puzzles

**Response (200):**
```json
{
  "success": true,
  "puzzles": [
    {
      "puzzle_id": "uuid-1",
      "name": "Beach Scene 1000pc",
      "date_added": "2026-01-11T10:30:00Z",
      "dimensions": {
        "width": 2048,
        "height": 1536
      },
      "thumbnail_url": "/api/puzzles/uuid-1/thumbnail"
    }
  ]
}
```

#### DELETE /api/puzzles/{puzzle_id}

**Purpose:** Delete a saved puzzle

**Response (200):**
```json
{
  "success": true,
  "message": "Puzzle deleted successfully"
}
```

## 6. Frontend UI Specification

### 6.1 Multi-Step Wizard Structure

**Page Structure:**
```
┌─────────────────────────────────────────┐
│  Header: PuzzleSolver AI                │
│  Progress: [1]─[2]─[3]─[4]─[5]          │
├─────────────────────────────────────────┤
│                                         │
│         Current Step Content            │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│  [Back]              [Next/Continue]    │
└─────────────────────────────────────────┘
```

### 6.2 Step-by-Step Screens

**Step 1: Welcome / Puzzle Selection**
```
┌─────────────────────────────────────────┐
│  Welcome to PuzzleSolver AI             │
│  Help find where puzzle pieces belong   │
│                                         │
│  Choose how to load your puzzle:        │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  📤 Upload Puzzle Image           │ │
│  │  Click or drag image here         │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  🔗 Enter URL                     │ │
│  │  [__________________________]     │ │
│  │  [Fetch Image]                    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  📚 Load Saved Puzzle             │ │
│  │  [View Saved Puzzles]             │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Step 2: Puzzle Preview & Confirm**
```
┌─────────────────────────────────────────┐
│  Confirm Your Puzzle                    │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │                                   │ │
│  │    [Puzzle Image Preview]         │ │
│  │      2048 x 1536 pixels           │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Name: [My Beach Puzzle________]        │
│                                         │
│  ☑ Save this puzzle for future use     │
│                                         │
│  [Change Puzzle]      [Continue]        │
└─────────────────────────────────────────┘
```

**Step 3: Upload Puzzle Piece**
```
┌─────────────────────────────────────────┐
│  Upload Puzzle Piece                    │
│                                         │
│  Current Puzzle: Beach Scene 1000pc     │
│  [View Full Puzzle]                     │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │                                   │ │
│  │    📤 Upload Piece Image          │ │
│  │    Click or drag here             │ │
│  │                                   │ │
│  │    Supported: JPG, PNG, HEIC      │ │
│  │    Max size: 10MB                 │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Tips for best results:                 │
│  • Good lighting                        │
│  • Contrasting background               │
│  • Piece fully visible                  │
│                                         │
│  [Back]                                 │
└─────────────────────────────────────────┘
```

**Step 4: Processing**
```
┌─────────────────────────────────────────┐
│  Analyzing Puzzle Piece...              │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │    [Piece Thumbnail Preview]      │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ⏳ Processing...                       │
│  ████████████░░░░░░░░░░░ 65%           │
│                                         │
│  • Checking image quality ✓             │
│  • Extracting features ✓                │
│  • Matching against puzzle...           │
│  • Calculating confidence...            │
│                                         │
│  Estimated time: 15 seconds             │
└─────────────────────────────────────────┘
```

**Step 5: Results Display**

*High Confidence Result:*
```
┌─────────────────────────────────────────┐
│  Match Found! ✓                         │
│  Confidence: 87.5% (High)               │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  [Puzzle Image with Highlight]    │ │
│  │                                   │ │
│  │         ┌─────┐                   │ │
│  │         │ 🟢  │  ← Match here     │ │
│  │         └─────┘                   │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Location: Upper-right quadrant         │
│  Rotation: Rotate 90° clockwise         │
│                                         │
│  Alternative Matches (>80%):            │
│  • Match #2: 82.1% confidence           │
│    [Show on puzzle]                     │
│                                         │
│  [Analyze Another Piece]                │
│  [Change Puzzle]                        │
└─────────────────────────────────────────┘
```

*Low Confidence Result:*
```
┌─────────────────────────────────────────┐
│  ⚠️  Low Confidence Match               │
│  Confidence: 65.3%                      │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  [Puzzle Image with Highlight]    │ │
│  │                                   │ │
│  │            ┌─────┐                │ │
│  │            │ 🟡  │  ← Possible    │ │
│  │            └─────┘                │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ⚠️  This match may not be accurate.    │
│  Consider retaking the piece photo      │
│  with better lighting.                  │
│                                         │
│  Location: Center area                  │
│  Rotation: Rotate 180°                  │
│                                         │
│  [Try Different Piece]                  │
│  [Retake Photo]                         │
│  [Change Puzzle]                        │
└─────────────────────────────────────────┘
```

### 6.3 Saved Puzzles Library

```
┌─────────────────────────────────────────┐
│  Saved Puzzles                          │
│  [Search: ____________]  [+ Add New]    │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ [thumb] │  │ [thumb] │  │ [thumb] │ │
│  │ Beach   │  │ Forest  │  │ Castle  │ │
│  │ 1000pc  │  │ 500pc   │  │ 2000pc  │ │
│  │ Jan 10  │  │ Jan 8   │  │ Jan 5   │ │
│  │[Select] │  │[Select] │  │[Select] │ │
│  │[Delete] │  │[Delete] │  │[Delete] │ │
│  └─────────┘  └─────────┘  └─────────┘ │
│                                         │
│  [Back]                                 │
└─────────────────────────────────────────┘
```

## 7. Docker Configuration

### 7.1 Dockerfile

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/saved_puzzles /app/temp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/puzzle_solver/api/health')"

# Run application
CMD ["python", "app.py"]
```

### 7.2 requirements.txt

```
flask==3.0.0
flask-cors==4.0.0
tensorflow==2.15.0
opencv-python==4.8.1.78
pillow==10.1.0
numpy==1.24.3
requests==2.31.0
werkzeug==3.0.1
python-magic==0.4.27
```

### 7.3 Docker Commands

**Build:**
```bash
docker build -t puzzlesolver:latest .
```

**Run:**
```bash
docker run -d \
  --name puzzlesolver \
  -p 8000:8000 \
  -v $(pwd)/saved_puzzles:/app/saved_puzzles \
  puzzlesolver:latest
```

**Stop:**
```bash
docker stop puzzlesolver
docker rm puzzlesolver
```

**View Logs:**
```bash
docker logs -f puzzlesolver
```

### 7.4 docker-compose.yml (Optional)

```yaml
version: '3.8'

services:
  puzzlesolver:
    build: .
    container_name: puzzlesolver
    ports:
      - "8000:8000"
    volumes:
      - ./saved_puzzles:/app/saved_puzzles
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/puzzle_solver/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 8. Project Structure

```
puzzlesolver/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── .gitignore
├── .dockerignore
│
├── app.py                      # Main Flask application
│
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # API route handlers
│   │   └── validators.py      # Input validation
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── puzzle_service.py  # Puzzle management logic
│   │   ├── matching_service.py # Matching algorithm
│   │   └── image_service.py   # Image processing
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── feature_extractor.py # TensorFlow models
│   │
│   └── utils/
│       ├── __init__.py
│       ├── quality_check.py   # Image quality validation
│       ├── file_utils.py      # File operations
│       └── security.py        # Security helpers
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   ├── components/
│   │   │   ├── Wizard.js
│   │   │   ├── StepPuzzleSelect.js
│   │   │   ├── StepPuzzleConfirm.js
│   │   │   ├── StepPieceUpload.js
│   │   │   ├── StepProcessing.js
│   │   │   ├── StepResults.js
│   │   │   └── SavedPuzzles.js
│   │   ├── services/
│   │   │   └── api.js
│   │   └── styles/
│   │       └── tailwind.css
│   ├── package.json
│   └── tailwind.config.js
│
├── saved_puzzles/              # Mounted volume
│   └── .gitkeep
│
└── temp/                       # Temporary processing (not in volume)
    └── .gitkeep
```

## 9. Security & Privacy Implementation

### 9.1 Piece Image Handling (Critical)

**Implementation Pattern:**

```python
@app.route('/api/analyze', methods=['POST'])
def analyze_piece():
    puzzle_id = request.form.get('puzzle_id')
    piece_file = request.files.get('piece')
    
    try:
        # Load into memory only - NEVER write to disk
        piece_bytes = BytesIO(piece_file.read())
        piece_image = Image.open(piece_bytes)
        
        # Quality check
        quality_ok, quality_msg = check_image_quality(piece_image)
        if not quality_ok:
            # Discard immediately
            piece_image.close()
            piece_bytes.close()
            return jsonify({
                'success': False,
                'error': 'Image quality insufficient',
                'details': quality_msg
            }), 400
        
        # Process
        piece_array = np.array(piece_image)
        matches = match_piece(piece_array, puzzle_id)
        
        # CRITICAL: Immediate cleanup
        piece_image.close()
        piece_bytes.close()
        del piece_image
        del piece_bytes
        del piece_array
        gc.collect()  # Force garbage collection
        
        return jsonify({
            'success': True,
            'best_match': matches[0],
            'alternatives': matches[1:]
        })
        
    except Exception as e:
        # Ensure cleanup even on error
        if 'piece_image' in locals():
            piece_image.close()
        if 'piece_bytes' in locals():
            piece_bytes.close()
        gc.collect()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**No Logging Rules:**
```python
# NEVER log piece image data
# logger.info(f"Piece uploaded: {piece_data}")  # ❌ WRONG

# Only log processing events
logger.info(f"Analysis requested for puzzle {puzzle_id}")  # ✓ OK
logger.info(f"Processing completed in {time}s")  # ✓ OK
```

### 9.2 Puzzle Storage Security

**File Permissions:**
- Puzzle directory: 755 (rwxr-xr-x)
- Puzzle files: 644 (rw-r--r--)
- No world-write permissions

**Path Validation:**
```python
def get_puzzle