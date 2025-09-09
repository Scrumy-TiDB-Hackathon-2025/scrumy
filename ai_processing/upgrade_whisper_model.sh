#!/bin/bash

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

log_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Configuration
WHISPER_MODEL_DIR="whisper.cpp/models"
CURRENT_MODEL="ggml-base.en.bin"
NEW_MODEL="ggml-medium.en.bin"

log_section "Whisper Model Upgrade"

# Check if we're in the right directory
if [ ! -d "$WHISPER_MODEL_DIR" ]; then
    log_error "Whisper models directory not found. Please run from ai_processing directory."
fi

# Check current model
if [ -f "$WHISPER_MODEL_DIR/$CURRENT_MODEL" ]; then
    log_info "Current model found: $CURRENT_MODEL"
else
    log_warning "Current model not found: $CURRENT_MODEL"
fi

# Check if new model already exists
if [ -f "$WHISPER_MODEL_DIR/$NEW_MODEL" ]; then
    log_success "New model already exists: $NEW_MODEL"
    log_info "Skipping download"
else
    log_info "Downloading new model: $NEW_MODEL"
    
    # Change to whisper.cpp directory
    cd whisper.cpp || log_error "Failed to change to whisper.cpp directory"
    
    # Download the medium model
    log_info "Running download script..."
    ./models/download-ggml-model.sh medium.en || log_error "Failed to download medium.en model"
    
    # Return to original directory
    cd .. || log_error "Failed to return to parent directory"
    
    log_success "Model downloaded successfully"
fi

# Update environment variable (if .env exists)
if [ -f ".env" ]; then
    log_info "Updating .env file..."
    
    # Check if WHISPER_MODEL_PATH exists in .env
    if grep -q "WHISPER_MODEL_PATH" .env; then
        # Update existing entry
        sed -i.bak "s|WHISPER_MODEL_PATH=.*|WHISPER_MODEL_PATH=./whisper.cpp/models/$NEW_MODEL|" .env
        log_success "Updated WHISPER_MODEL_PATH in .env"
    else
        # Add new entry
        echo "WHISPER_MODEL_PATH=./whisper.cpp/models/$NEW_MODEL" >> .env
        log_success "Added WHISPER_MODEL_PATH to .env"
    fi
else
    log_warning ".env file not found. Creating one..."
    echo "WHISPER_MODEL_PATH=./whisper.cpp/models/$NEW_MODEL" > .env
    log_success "Created .env with WHISPER_MODEL_PATH"
fi

# Verify the new model
if [ -f "$WHISPER_MODEL_DIR/$NEW_MODEL" ]; then
    MODEL_SIZE=$(du -h "$WHISPER_MODEL_DIR/$NEW_MODEL" | cut -f1)
    log_success "Model upgrade complete!"
    log_info "New model: $NEW_MODEL ($MODEL_SIZE)"
    log_info "Expected improvements: Better accuracy, reduced hallucinations"
    log_warning "Note: Processing will be ~2x slower but significantly more accurate"
else
    log_error "Model upgrade failed - new model not found"
fi

log_section "Upgrade Complete"
log_info "Restart your services to use the new model:"
log_info "  For PM2: ../restart_pm2_with_env_fixed.sh"
log_info "  For manual: ./clean_start_backend.sh"

# Auto-restart PM2 if it's running
if command -v pm2 >/dev/null 2>&1 && pm2 list | grep -q "scrumbot"; then
    log_info "PM2 processes detected. Auto-restarting..."
    cd .. && ./restart_pm2_with_env_fixed.sh
else
    log_info "No PM2 processes found. Manual restart required."
fi