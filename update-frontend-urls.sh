#!/bin/bash

# Update Frontend URLs with Current Ngrok Tunnels
# Run this after starting ngrok tunnels

echo "🔍 Getting current ngrok URLs..."

# Check if ngrok is running
if ! curl -s http://localhost:4040/api/tunnels > /dev/null; then
    echo "❌ Ngrok not running on port 4040"
    echo "   Start ngrok first with: ./deployment/setup_ngrok.sh"
    exit 1
fi

# Get ngrok tunnels info
NGROK_INFO=$(curl -s http://localhost:4040/api/tunnels)

# Extract API URL (assuming port 8080 for backend)
API_URL=$(echo "$NGROK_INFO" | jq -r '.tunnels[] | select(.config.addr | contains("8080")) | .public_url')

# Convert to WebSocket URL
WS_URL=$(echo "$API_URL" | sed 's/https:/wss:/')

if [ -z "$API_URL" ] || [ "$API_URL" = "null" ]; then
    echo "❌ Could not find ngrok tunnel for port 8080"
    echo "   Available tunnels:"
    echo "$NGROK_INFO" | jq -r '.tunnels[] | "   \(.config.addr) -> \(.public_url)"'
    exit 1
fi

echo "📡 Found API URL: $API_URL"
echo "🔌 WebSocket URL: $WS_URL"

# Update frontend production environment
echo "📝 Updating frontend_dashboard/.env.production..."

cat > frontend_dashboard/.env.production << EOF
# Production Environment Variables - Auto-generated
NEXT_PUBLIC_API_URL=$API_URL
NEXT_PUBLIC_WEBSOCKET_URL=$WS_URL
NEXT_PUBLIC_ENV=production

# Production API endpoints
NEXT_PUBLIC_HEALTH_ENDPOINT=/health
NEXT_PUBLIC_MEETINGS_ENDPOINT=/get-meetings
NEXT_PUBLIC_TASKS_ENDPOINT=/api/tasks
NEXT_PUBLIC_TRANSCRIPTS_ENDPOINT=/api/transcripts
NEXT_PUBLIC_INTEGRATIONS_ENDPOINT=/api/integration-status
EOF

echo "✅ Frontend URLs updated!"
echo ""
echo "🚀 To use production URLs:"
echo "   cd frontend_dashboard"
echo "   npm run build"
echo "   npm start"
echo ""
echo "🧪 To test:"
echo "   curl $API_URL/health"
echo ""
echo "🔗 Frontend will be available at: http://localhost:3000"
echo "   (connecting to: $API_URL)"