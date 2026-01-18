#!/bin/bash

# PuzzleSolver AI - Stop Script
# This script stops and optionally removes the PuzzleSolver Docker container

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
    echo -e "${BLUE}  PuzzleSolver AI - Stop${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

# Check if docker-compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        return 0
    elif docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        return 0
    else
        return 1
    fi
}

# Stop with docker-compose
stop_with_compose() {
    print_info "Stopping with docker-compose..."
    $COMPOSE_CMD down
    print_success "Stopped with docker-compose"
}

# Stop Docker container
stop_container() {
    if docker ps --format '{{.Names}}' | grep -q '^puzzlesolver$'; then
        print_info "Stopping PuzzleSolver container..."
        docker stop puzzlesolver
        print_success "Container stopped"
    else
        print_warning "Container is not running"
    fi
}

# Remove Docker container
remove_container() {
    if docker ps -a --format '{{.Names}}' | grep -q '^puzzlesolver$'; then
        print_info "Removing PuzzleSolver container..."
        docker rm puzzlesolver
        print_success "Container removed"
    fi
}

# Remove Docker image
remove_image() {
    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q '^puzzlesolver:latest$'; then
        echo ""
        read -p "Do you also want to remove the Docker image? (y/N) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing Docker image..."
            docker rmi puzzlesolver:latest
            print_success "Image removed"
        else
            print_info "Keeping Docker image for faster restarts"
        fi
    fi
}

# Show data preservation message
show_data_message() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  Shutdown Complete${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "Your saved puzzles are preserved in:"
    echo -e "  ${BLUE}$(pwd)/saved_puzzles/${NC}"
    echo ""
    echo "To restart PuzzleSolver:"
    echo -e "  ${YELLOW}./start.sh${NC}"
    echo ""
    echo "To completely remove all data:"
    echo -e "  ${YELLOW}rm -rf saved_puzzles/ logs/ temp/${NC}"
    echo -e "  ${RED}(Warning: This will delete all saved puzzles!)${NC}"
    echo ""
}

# Ask for cleanup options
ask_cleanup() {
    echo ""
    read -p "Do you want to remove all saved puzzles and data? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        print_warning "This will permanently delete all saved puzzles!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing data directories..."
            rm -rf saved_puzzles/*
            rm -rf logs/*
            rm -rf temp/*
            print_success "Data cleaned up"
        else
            print_info "Keeping saved data"
        fi
    fi
}

# Main execution
main() {
    print_header
    
    # Check if docker-compose.yml exists and try to use it
    if [ -f "docker-compose.yml" ] && check_docker_compose; then
        stop_with_compose
    else
        # Fallback to docker commands
        stop_container
        remove_container
        remove_image
    fi
    
    # Ask about cleanup
    ask_cleanup
    
    # Show final message
    show_data_message
    
    print_success "Stop complete!"
}

# Run main function
main