# Frontend Dashboard Environment Management

This document describes the environment management system for the ScrumBot Frontend Dashboard, which provides dev, staging, and production configurations mirroring the Chrome extension setup.

## 🌍 Overview

The frontend dashboard supports three environments:
- **Development** (`dev`) - Local development with mock data and debugging
- **Staging** (`staging`) - Pre-production testing environment
- **Production** (`prod`) - Live production environment

## 📁 Structure

```
frontend_dashboard/
├── config/
│   ├── dev.env          # Development environment variables
│   ├── staging.env      # Staging environment variables
│   └── prod.env         # Production environment variables
├── scripts/
│   ├── switch-env.js    # Environment switcher
│   ├── env-status.js    # Environment status checker
│   ├── validate-env.js  # Environment validator
│   ├── build-dev.sh     # Development build script
│   ├── build-staging.sh # Staging build script
│   └── build-prod.sh    # Production build script
├── lib/config/
│   └── environment.ts   # TypeScript configuration module
└── .env.local           # Active environment variables (auto-generated)
```

## 🚀 Quick Start

### Switch Environment
```bash
# Switch to development
npm run env:dev

# Switch to staging  
npm run env:staging

# Switch to production
npm run env:prod
```

### Check Current Status
```bash
# View current environment and configuration
npm run env:status

# Validate configuration
npm run env:validate

# Validate with connectivity test
npm run env:validate:connectivity
```

### Build for Environment
```bash
# Build for development
npm run build:dev

# Build for staging
npm run build:staging

# Build for production
npm run build:prod
```

### Deploy
```bash
# Build and start for current environment
npm run deploy:dev      # Development
npm run deploy:staging  # Staging
npm run deploy:prod     # Production
```

## 🔧 Environment Configurations

### Development Environment
- **Backend URL**: `http://localhost:8000`
- **WebSocket**: `ws://localhost:8000/ws/audio`
- **Debug**: Enabled
- **Mock Data**: Enabled
- **Log Level**: Debug
- **Features**: All debugging and mock features enabled

### Staging Environment
- **Backend URL**: `https://staging-api.scrumy.app`
- **WebSocket**: `wss://staging-api.scrumy.app/ws/audio`
- **Debug**: Info level logging
- **Mock Data**: Disabled
- **Features**: Production-like but with enhanced logging

### Production Environment
- **Backend URL**: `https://b5462b7bbb65.ngrok-free.app`
- **WebSocket**: `wss://b5462b7bbb65.ngrok-free.app/ws/audio-stream`
- **Debug**: Error logging only
- **Mock Data**: Disabled
- **Features**: Optimized for performance and security

## 📝 Environment Variables

### Required Variables
- `NEXT_PUBLIC_ENVIRONMENT` - Current environment (dev/staging/prod)
- `NEXT_PUBLIC_BACKEND_URL` - Backend API URL
- `NEXT_PUBLIC_WEBSOCKET_URL` - WebSocket server URL
- `NEXT_PUBLIC_FRONTEND_URL` - Frontend application URL
- `NEXT_PUBLIC_VERSION` - Application version

### API Endpoints
All API endpoints are configurable:
- `NEXT_PUBLIC_API_HEALTH` - Health check endpoint
- `NEXT_PUBLIC_API_SAVE_TRANSCRIPT` - Save transcript endpoint
- `NEXT_PUBLIC_API_GET_MEETINGS` - Get meetings endpoint
- `NEXT_PUBLIC_API_PROCESS_TRANSCRIPT` - Process transcript endpoint
- And more...

### Feature Flags
- `NEXT_PUBLIC_ENABLE_WEBSOCKET` - Enable WebSocket functionality
- `NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES` - Enable real-time updates
- `NEXT_PUBLIC_ENABLE_MOCK_TRANSCRIPTION` - Enable mock transcription

### Performance Settings
- `NEXT_PUBLIC_REFRESH_INTERVAL` - Data refresh interval (ms)
- `NEXT_PUBLIC_TIMEOUT` - Request timeout (ms)

## 💻 Development Workflow

### 1. Setup Development Environment
```bash
# Switch to development environment
npm run env:dev

# Validate configuration
npm run env:validate

# Start development server
npm run dev
```

### 2. Testing with Different Environments
```bash
# Test with staging configuration
npm run env:staging
npm run build:staging
npm run start

# Test with production configuration
npm run env:prod
npm run build:prod
npm run start
```

### 3. Pre-deployment Validation
```bash
# Validate configuration and connectivity
npm run env:validate:connectivity

# Check environment status
npm run env:status
```

## 🔍 TypeScript Integration

Import the environment configuration in your TypeScript files:

```typescript
import { config, isProduction, buildApiUrl, log } from '@/lib/config/environment';

// Use configuration
const apiUrl = buildApiUrl('getMeetings');
const websocketUrl = buildWebSocketUrl();

// Environment checks
if (isDevelopment()) {
  log.debug('Running in development mode');
}

// Feature flags
if (config.FEATURE_FLAGS.enableWebSocket) {
  // Initialize WebSocket
}

// API calls with environment-specific URLs
fetch(buildApiUrl('health'))
  .then(response => response.json())
  .then(data => log.info('Health check:', data));
```

## 🛠️ Script Commands

### Environment Management
- `npm run env:dev` - Switch to development environment
- `npm run env:staging` - Switch to staging environment  
- `npm run env:prod` - Switch to production environment
- `npm run env:status` - Show current environment status
- `npm run env:validate` - Validate current configuration
- `npm run env:validate:connectivity` - Validate with connectivity test

### Build Commands
- `npm run build:dev` - Build for development
- `npm run build:staging` - Build for staging
- `npm run build:prod` - Build for production

### Deploy Commands
- `npm run deploy:dev` - Build and deploy development
- `npm run deploy:staging` - Build and deploy staging
- `npm run deploy:prod` - Build and deploy production

## 🔒 Security Considerations

### Development
- Debug logging enabled
- Mock data for testing
- Local backend connections
- No sensitive data exposure

### Staging
- Limited debug information
- Real backend integration
- SSL/TLS validation
- Production-like security

### Production
- Error logging only
- No debug information
- Full security measures
- Performance optimizations

## 🚨 Troubleshooting

### Environment Not Loading
```bash
# Check if environment file exists
npm run env:status

# Recreate environment
npm run env:dev  # or staging/prod
```

### Configuration Validation Errors
```bash
# Validate configuration
npm run env:validate

# Check specific connectivity
npm run env:validate:connectivity
```

### Backend Connection Issues
```bash
# Development: Check if backend is running
curl http://localhost:8000/health

# Staging/Production: Check DNS and SSL
curl https://your-backend-url/health
```

### WebSocket Connection Problems
- Verify WebSocket URL in environment config
- Check firewall settings
- Ensure backend WebSocket server is running
- Test with browser developer tools

## 📊 Environment Comparison

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| Backend | localhost:8000 | staging-api.scrumy.app | b5462b7bbb65.ngrok-free.app |
| Debug Logging | ✅ Full | ⚠️ Info Level | ❌ Errors Only |
| Mock Data | ✅ Enabled | ❌ Disabled | ❌ Disabled |
| Hot Reload | ✅ Enabled | ❌ Disabled | ❌ Disabled |
| SSL/TLS | ❌ HTTP | ✅ HTTPS | ✅ HTTPS |
| Performance | 🐌 Debug Mode | ⚡ Optimized | 🚀 Maximum |
| Error Reporting | 📝 Console | 📊 Enhanced | 🔔 Production |

## 🔄 Migration from Legacy Setup

If you're migrating from a previous setup:

1. Backup existing configuration
2. Run environment setup: `npm run env:dev`
3. Update imports to use new config module
4. Test with: `npm run env:validate`
5. Update deployment scripts to use new build commands

## 📚 Related Documentation

- [Chrome Extension Environment Setup](../chrome_extension/README.md)
- [Backend API Documentation](../backend/README.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Integration Implementation Guide](./INTEGRATION_IMPLEMENTATION_GUIDE.md)

## 🆘 Support

If you encounter issues with environment setup:

1. Check this documentation
2. Run `npm run env:status` to diagnose
3. Validate with `npm run env:validate`
4. Check backend connectivity
5. Review environment configuration files
6. Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintainer**: ScrumBot Development Team