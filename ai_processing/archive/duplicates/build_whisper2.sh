#!/bin/bash

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions for logging
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
    return 1
}

handle_error() {
    log_error "$1"
    exit 1
}

log_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Detect operating system
OS=$(uname -s)
case "$OS" in
    Linux*)  PLATFORM=Linux ;;
    Darwin*) PLATFORM=macOS ;;
    *)       handle_error "Unsupported OS: $OS" ;;
esac
log_info "Detected platform: $PLATFORM"

# Install package manager if not present
install_package_manager() {
    if [ "$PLATFORM" = "Linux" ]; then
        if ! command -v apt >/dev/null 2>&1; then
            handle_error "apt package manager not found. Please install it manually."
        fi
        log_info "Using apt for package management"
    elif [ "$PLATFORM" = "macOS" ]; then
        if ! command -v brew >/dev/null 2>&1; then
            log_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            # Add Homebrew to PATH
            if [ -f /opt/homebrew/bin/brew ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [ -f /usr/local/bin/brew ]; then
                eval "$(/usr/local/bin/brew shellenv)"
            fi
        fi
        log_info "Using brew for package management"
    fi
}

# Install dependencies based on platform
install_dependencies() {
    log_info "Installing required dependencies..."
    if [ "$PLATFORM" = "Linux" ]; then
        sudo apt update && sudo apt install -y build-essential cmake clang libssl-dev || handle_error "Failed to install dependencies on Linux"
    elif [ "$PLATFORM" = "macOS" ]; then
        brew install libomp llvm cmake || handle_error "Failed to install dependencies on macOS"
    fi
    log_success "Dependencies installed successfully"
}

# Main script
log_section "Starting Whisper.cpp Build Process"

log_info "Updating git submodules..."
git submodule update --init --recursive || handle_error "Failed to update git submodules"

log_info "Checking for whisper.cpp directory..."
if [ ! -d "whisper.cpp" ]; then
    handle_error "Directory 'whisper.cpp' not found. Please make sure you're in the correct directory and the submodule is initialized"
fi

log_info "Changing to whisper.cpp directory..."
cd whisper.cpp || handle_error "Failed to change to whisper.cpp directory"

log_info "Checking for custom server directory..."
if [ ! -d "../whisper-custom/server" ]; then
    handle_error "Directory '../whisper-custom/server' not found. Please make sure the custom server files exist"
fi

log_info "Copying custom server files..."
cp -r ../whisper-custom/server/* "examples/server/" || handle_error "Failed to copy custom server files"
log_success "Custom server files copied successfully"

log_info "Verifying server files..."
ls "examples/server/" || handle_error "Failed to list server files"

log_section "Building Whisper Server"
install_package_manager
install_dependencies

log_info "Building whisper.cpp..."
rm -rf build
mkdir build && cd build || handle_error "Failed to create build directory"

# Configure CMake with simple warning suppression
log_info "Configuring CMake..."
cmake -DCMAKE_C_FLAGS="-w" -DCMAKE_CXX_FLAGS="-w" .. || handle_error "CMake configuration failed"

make -j4 || handle_error "Make failed"
cd ..
log_success "Build completed successfully"

# Configuration
PACKAGE_NAME="whisper-server-package"
MODEL_NAME="ggml-small.bin"
MODEL_DIR="$PACKAGE_NAME/models"

log_section "Package Configuration"
log_info "Package name: $PACKAGE_NAME"
log_info "Model name: $MODEL_NAME"
log_info "Model directory: $MODEL_DIR"

# Create necessary directories
log_info "Creating package directories..."
mkdir -p "$PACKAGE_NAME" || handle_error "Failed to create package directory"
mkdir -p "$MODEL_DIR" || handle_error "Failed to create models directory"
log_success "Package directories created successfully"

# Copy server binary
log_info "Copying server binary..."
cp build/bin/whisper-server "$PACKAGE_NAME/" || handle_error "Failed to copy server binary"
log_success "Server binary copied successfully"

# Copy model file
log_section "Model Management"
log_info "Checking for existing Whisper models..."

EXISTING_MODELS=$(find "$MODEL_DIR" -name "ggml-*.bin" -type f)

if [ -n "$EXISTING_MODELS" ]; then
    log_info "Found existing models:"
    echo -e "${BLUE}$EXISTING_MODELS${NC}"
else
    log_warning "No existing models found"
fi

# Whisper models
models="tiny tiny.en tiny-q5_1 tiny.en-q5_1 tiny-q8_0 base base.en base-q5_1 base.en-q5_1 base-q8_0 small small.en small.en-tdrz small-q5_1 small.en-q5_1 small-q8_0 medium medium.en medium-q5_0 medium.en-q5_0 medium-q8_0 large-v1 large-v2 large-v2-q5_0 large-v2-q8_0 large-v3 large-v3-q5_0 large-v3-turbo large-v3-turbo-q5_0 large-v3-turbo-q8_0"

# Ask user which model to use if the argument is not provided
if [ -z "$1" ]; then
    log_info "Available models: $models"
    read -p "Enter a model name (e.g. small): " MODEL_SHORT_NAME
else
    MODEL_SHORT_NAME=$1
fi

# Check if the model is valid
if ! echo "$models" | grep -qw "$MODEL_SHORT_NAME"; then
    handle_error "Invalid model: $MODEL_SHORT_NAME"
fi

MODEL_NAME="ggml-$MODEL_SHORT_NAME.bin"

# Check if the modelname exists in directory
if [ -f "$MODEL_DIR/$MODEL_NAME" ]; then
    log_info "Model file exists: $MODEL_DIR/$MODEL_NAME"
else
    log_warning "Model file does not exist: $MODEL_DIR/$MODEL_NAME"
    log_info "Trying to download model..."
    ./models/download-ggml-model.sh $MODEL_SHORT_NAME || handle_error "Failed to download model"
    mv "./models/$MODEL_NAME" "$MODEL_DIR/" || handle_error "Failed to move model to models directory"
fi

# Create run script
log_info "Creating run script..."
cat > "$PACKAGE_NAME/run-server.sh" << 'EOL'
#!/bin/bash

# Default configuration
HOST="127.0.0.1"
PORT="8178"
MODEL="models/ggml-large-v3.bin"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run the server
./whisper-server \
    --model "$MODEL" \
    --host "$HOST" \
    --port "$PORT" \
    --diarize \
    --print-progress
EOL
log_success "Run script created successfully"

log_info "Making script executable: $PACKAGE_NAME/run-server.sh"
chmod +x "$PACKAGE_NAME/run-server.sh" || handle_error "Failed to make script executable"

log_info "Listing files..."
ls || handle_error "Failed to list files"

# Check if package directory already exists
if [ -d "../$PACKAGE_NAME" ]; then
    log_info "Listing parent directory..."
    log_warning "Package directory already exists: ../$PACKAGE_NAME"
    log_info "Listing package directory..."
else
    log_info "Creating package directory: ../$PACKAGE_NAME"
    mkdir "../$PACKAGE_NAME" || handle_error "Failed to create package directory"
    log_success "Package directory created successfully"
fi

# Move whisper-server package out of whisper.cpp
if [ -d "../$PACKAGE_NAME" ]; then
    log_info "Copying package contents to existing directory..."
    cp -r "$PACKAGE_NAME/"* "../$PACKAGE_NAME" || handle_error "Failed to copy package contents"
else
    log_info "Copying whisper-server and model to ../$PACKAGE_NAME"
    cp "$MODEL_DIR/$MODEL_NAME" "../$PACKAGE_NAME/models/" || handle_error "Failed to copy model"
    cp "$PACKAGE_NAME/run-server.sh" "../$PACKAGE_NAME" || handle_error "Failed to copy run script"
    cp -r "$PACKAGE_NAME/public" "../$PACKAGE_NAME" || handle_error "Failed to copy public directory"
    cp "$PACKAGE_NAME/whisper-server" "../$PACKAGE_NAME" || handle_error "Failed to copy whisper-server"
fi

log_section "Environment Setup"
log_info "Setting up environment variables..."
# Adjust for platform-specific paths
if [ "$PLATFORM" = "Linux" ]; then
    ENV_SRC="ai_processing/.env"
    ENV_DEST="ai_processing/.env"
elif [ "$PLATFORM" = "macOS" ]; then
    ENV_SRC="ai_processing/.env"
    ENV_DEST="ai_processing/.env"
fi
cd ../.. && cp "$ENV_SRC" "$ENV_DEST" || log_warning "Environment file copy skipped (already in place)"

log_info "If you want to use Models hosted on Anthropic, OpenAI or GROQ, add the API keys to the $ENV_DEST file."

log_section "Build Process Complete"
log_success "Whisper.cpp server build and setup completed successfully!"

log_section "Script Permissions"
log_info "Making script executable: clean_start_backend.sh"
chmod +x ai_processing/clean_start_backend.sh || handle_error "Failed to make script executable"
log_success "Permission set successfully!"

log_section "Installing Python Dependencies"
log_info "Installing Python dependencies..."
cd ai_processing || handle_error "Failed to change to ai_processing directory"
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv || handle_error "Failed to create virtual environment"
    source venv/bin/activate || handle_error "Failed to activate virtual environment"
    pip install -r requirements.txt || handle_error "Failed to install dependencies"
else
    log_info "Virtual environment already exists"
    source venv/bin/activate || handle_error "Failed to activate virtual environment"
    pip install -r requirements.txt || handle_error "Failed to install dependencies"
fi
log_success "Dependencies installed successfully"

echo -e "${GREEN}You can now proceed with running the server by running './clean_start_backend.sh'${NC}"