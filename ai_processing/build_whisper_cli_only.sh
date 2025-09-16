#!/bin/bash

# Build Whisper.cpp CLI only (avoid server compilation issues)
# This script builds only the whisper-cli executable we need

set -e

echo "🎤 Building Whisper.cpp CLI only..."

# Check if whisper.cpp directory exists
if [ ! -d "whisper.cpp" ]; then
    echo "❌ whisper.cpp directory not found"
    echo "Please run the main build script first to clone whisper.cpp"
    exit 1
fi

cd whisper.cpp

# Create build directory
mkdir -p build
cd build

# Configure with CMake - disable server to avoid compilation issues
echo "⚙️  Configuring CMake (CLI only)..."
cmake .. \
    -DWHISPER_BUILD_EXAMPLES=ON \
    -DWHISPER_BUILD_SERVER=OFF \
    -DWHISPER_BUILD_TESTS=OFF

# Build only the CLI executable
echo "🔨 Building whisper-cli..."
make -j$(nproc) whisper-cli

# Verify build
if [ -f "bin/whisper-cli" ]; then
    echo "✅ Whisper CLI built successfully!"
    echo "📍 Executable: $(pwd)/bin/whisper-cli"
else
    echo "❌ Whisper CLI build failed"
    exit 1
fi

cd ../..

echo "🎉 Whisper.cpp CLI ready for use!"