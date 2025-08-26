#!/bin/bash

# Production Build Script for ScrumBot Frontend Dashboard
set -e

echo "🚀 Building ScrumBot Frontend Dashboard - Production Environment"
echo "=================================================="

# Set environment
ENV="prod"
echo "📝 Environment: $ENV"

# Switch to production environment
echo "🔄 Switching to production environment..."
node scripts/switch-env.js prod

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm ci --only=production
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf .next
rm -rf out

# Build the application
echo "🏗️  Building application..."
NODE_ENV=production npm run build

# Verify build
if [ -d ".next" ]; then
    echo "✅ Build completed successfully!"
    echo "📁 Build output: .next/"

    # Display build info
    echo ""
    echo "📊 Build Information:"
    echo "   Environment: Production"
    echo "   Debug: Disabled"
    echo "   Mock Data: Disabled"
    echo "   Backend URL: https://b5462b7bbb65.ngrok-free.app"
    echo "   WebSocket URL: wss://b5462b7bbb65.ngrok-free.app/ws/audio-stream"
    echo "   Optimization: Enabled"
    echo "   Minification: Enabled"

    echo ""
    echo "🚀 To start the production server:"
    echo "   npm run start"

    echo ""
    echo "📋 Production Checklist:"
    echo "   - Ensure production backend is running"
    echo "   - Verify SSL certificates are valid"
    echo "   - Test WebSocket connections"
    echo "   - Check API endpoints are accessible"
    echo "   - Monitor performance metrics"
    echo "   - Verify error logging is working"

    echo ""
    echo "🔒 Security Notes:"
    echo "   - All debug logging is disabled"
    echo "   - Mock data is disabled"
    echo "   - Only error logs are captured"
    echo "   - Optimized for performance"

else
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "🎉 Production build completed successfully!"
