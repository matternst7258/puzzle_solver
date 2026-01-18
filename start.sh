#!/bin/bash

# PuzzleSolver AI - Startup Script
# This script builds and starts the PuzzleSolver Docker container

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  PuzzleSolver AI - Startup${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    print_success "Docker is installed"
}

# Check if Docker is running
check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker is not running!"
        echo "Please start Docker Desktop and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "docker-compose is not available!"
        echo "Please install Docker Compose or update Docker Desktop."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p saved_puzzles
    mkdir -p logs
    mkdir -p temp
    mkdir -p frontend/build
    print_success "Directories created"
}

# Stop existing container
stop_existing() {
    if docker ps -a --format '{{.Names}}' | grep -q '^puzzlesolver$'; then
        print_info "Stopping existing container..."
        docker stop puzzlesolver 2>/dev/null || true
        docker rm puzzlesolver 2>/dev/null || true
        print_success "Existing container stopped"
    fi
}

# Build and start with docker-compose
start_with_compose() {
    print_info "Building and starting with docker-compose..."
    $COMPOSE_CMD down 2>/dev/null || true
    $COMPOSE_CMD up -d --build
    print_success "Container started with docker-compose"
}

# Build Docker image
build_image() {
    print_info "Building Docker image (this may take a few minutes)..."
    docker build -t puzzlesolver:latest .
    print_success "Docker image built successfully"
}

# Start Docker container
start_container() {
    print_info "Starting PuzzleSolver container..."
    docker run -d \
        --name puzzlesolver \
        -p 8000:8000 \
        -v "$(pwd)/saved_puzzles:/app/saved_puzzles" \
        -v "$(pwd)/logs:/app/logs" \
        --restart unless-stopped \
        puzzlesolver:latest
    print_success "Container started successfully"
}

# Wait for application to be ready
wait_for_app() {
    print_info "Waiting for application to start..."
    
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -s http://localhost:8000/puzzle_solver/api/health > /dev/null 2>&1; then
            print_success "Application is ready!"
            return 0
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        echo -n "."
        sleep 2
    done
    
    echo ""
    print_warning "Application may still be starting. Check logs with: docker logs puzzlesolver"
}

# Show final instructions
show_instructions() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  PuzzleSolver AI is Running!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "🌐 Open in browser: ${BLUE}http://localhost:8000/puzzle_solver/${NC}"
    echo ""
    echo "Useful commands:"
    echo -e "  View logs:    ${YELLOW}docker logs -f puzzlesolver${NC}"
    echo -e "  Stop app:     ${YELLOW}docker stop puzzlesolver${NC}"
    echo -e "  Restart app:  ${YELLOW}docker restart puzzlesolver${NC}"
    echo -e "  Remove app:   ${YELLOW}docker stop puzzlesolver && docker rm puzzlesolver${NC}"
    echo ""
    echo "Data locations:"
    echo -e "  Puzzles:      ${BLUE}$(pwd)/saved_puzzles/${NC}"
    echo -e "  Logs:         ${BLUE}$(pwd)/logs/${NC}"
    echo ""
}

# Open browser (macOS)
open_browser() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Opening browser..."
        sleep 2
        open http://localhost:8000/puzzle_solver/ 2>/dev/null || true
    fi
}

# Main execution
main() {
    print_header
    
    # Pre-flight checks
    check_docker
    check_docker_running
    
    # Create directories
    create_directories
    
    # Stop existing container if running
    stop_existing
    
    # Check if docker-compose.yml exists
    if [ -f "docker-compose.yml" ]; then
        check_docker_compose
        start_with_compose
    else
        # Fallback to docker commands
        build_image
        start_container
    fi
    
    # Wait for app to be ready
    wait_for_app
    
    # Show instructions
    show_instructions
    
    # Open browser
    open_browser
    
    print_success "Startup complete!"
}

# Run main function
main