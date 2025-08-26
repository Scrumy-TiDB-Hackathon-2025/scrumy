#!/bin/bash

# Staging Build Script for ScrumBot Frontend Dashboard
set -e

echo "🧪 Building ScrumBot Frontend Dashboard - Staging Environment"
echo "=================================================="

# Set environment
ENV="staging"
echo "📝 Environment: $ENV"

# Switch to staging environment
echo "🔄 Switching to staging environment..."
node scripts/switch-env.js staging

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
    echo "   Environment: Staging"
    echo "   Debug: Enabled (Info level)"
    echo "   Mock Data: Disabled"
    echo "   Backend URL: https://staging-api.scrumy.app"
    echo "   WebSocket URL: wss://staging-api.scrumy.app/ws/audio"

    echo ""
    echo "🚀 To start the production server:"
    echo "   npm run start"

    echo ""
    echo "📋 Staging Checklist:"
    echo "   - Ensure staging backend is running"
    echo "   - Verify SSL certificates are valid"
    echo "   - Test WebSocket connections"
    echo "   - Check API endpoints are accessible"

else
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "🎉 Staging build completed successfully!"
