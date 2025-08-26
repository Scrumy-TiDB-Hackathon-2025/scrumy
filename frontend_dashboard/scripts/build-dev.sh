#!/bin/bash

# Development Build Script for ScrumBot Frontend Dashboard
set -e

echo "🔧 Building ScrumBot Frontend Dashboard - Development Environment"
echo "=================================================="

# Set environment
ENV="dev"
echo "📝 Environment: $ENV"

# Switch to development environment
echo "🔄 Switching to development environment..."
node scripts/switch-env.js dev

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf .next
rm -rf out

# Build the application
echo "🏗️  Building application..."
npm run build

# Verify build
if [ -d ".next" ]; then
    echo "✅ Build completed successfully!"
    echo "📁 Build output: .next/"

    # Display build info
    echo ""
    echo "📊 Build Information:"
    echo "   Environment: Development"
    echo "   Debug: Enabled"
    echo "   Mock Data: Enabled"
    echo "   Backend URL: http://localhost:8000"
    echo "   WebSocket URL: ws://localhost:8000/ws/audio"

    echo ""
    echo "🚀 To start the development server:"
    echo "   npm run dev"

    echo ""
    echo "🏃 To start the production server:"
    echo "   npm run start"

else
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "🎉 Development build completed successfully!"
