// env-status.js - Check current environment status and configuration
const fs = require('fs');
const path = require('path');

const envFilePath = path.join(__dirname, '..', '.env.local');
const configDir = path.join(__dirname, '..', 'config');

function getCurrentEnvironment() {
  try {
    if (!fs.existsSync(envFilePath)) {
      return null;
    }

    const envContent = fs.readFileSync(envFilePath, 'utf8');
    const envMatch = envContent.match(/NEXT_PUBLIC_ENVIRONMENT=(\w+)/);

    return envMatch ? envMatch[1] : null;
  } catch (error) {
    return null;
  }
}

function getEnvironmentConfig(env) {
  const configFile = path.join(configDir, `${env}.env`);

  if (!fs.existsSync(configFile)) {
    return null;
  }

  const content = fs.readFileSync(configFile, 'utf8');
  const config = {};

  content.split('\n').forEach(line => {
    line = line.trim();
    if (line && !line.startsWith('#')) {
      const [key, value] = line.split('=', 2);
      if (key && value) {
        config[key.trim()] = value.trim();
      }
    }
  });

  return config;
}

function displayStatus() {
  console.log('🔧 ScrumBot Frontend Dashboard - Environment Status');
  console.log('==================================================');

  const currentEnv = getCurrentEnvironment();

  if (!currentEnv) {
    console.log('❌ No environment is currently active');
    console.log('');
    console.log('To set an environment, run:');
    console.log('  npm run env:dev      # Development');
    console.log('  npm run env:staging  # Staging');
    console.log('  npm run env:prod     # Production');
    return;
  }

  console.log(`📍 Current Environment: ${currentEnv.toUpperCase()}`);
  console.log('');

  const config = getEnvironmentConfig(currentEnv);
  if (!config) {
    console.log(`❌ Configuration file not found for environment: ${currentEnv}`);
    return;
  }

  // Display key configuration
  console.log('🔗 API Configuration:');
  console.log(`   Backend URL: ${config.NEXT_PUBLIC_BACKEND_URL}`);
  console.log(`   WebSocket URL: ${config.NEXT_PUBLIC_WEBSOCKET_URL}`);
  console.log(`   Frontend URL: ${config.NEXT_PUBLIC_FRONTEND_URL}`);
  console.log('');

  console.log('⚙️  Settings:');
  console.log(`   Debug Mode: ${config.NEXT_PUBLIC_DEBUG}`);
  console.log(`   Mock Data: ${config.NEXT_PUBLIC_MOCK_DATA}`);
  console.log(`   Log Level: ${config.NEXT_PUBLIC_LOG_LEVEL}`);
  console.log('');

  console.log('🚀 Feature Flags:');
  console.log(`   WebSocket: ${config.NEXT_PUBLIC_ENABLE_WEBSOCKET}`);
  console.log(`   Real-time Updates: ${config.NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES}`);
  console.log(`   Mock Transcription: ${config.NEXT_PUBLIC_ENABLE_MOCK_TRANSCRIPTION}`);
  console.log('');

  console.log('⚡ Performance:');
  console.log(`   Refresh Interval: ${config.NEXT_PUBLIC_REFRESH_INTERVAL}ms`);
  console.log(`   Timeout: ${config.NEXT_PUBLIC_TIMEOUT}ms`);
  console.log('');

  console.log('📋 Available Commands:');
  console.log(`   npm run dev           # Start development server`);
  console.log(`   npm run build:${currentEnv}       # Build for ${currentEnv}`);
  console.log(`   npm run deploy:${currentEnv}      # Build and deploy for ${currentEnv}`);
  console.log('');

  // Environment-specific notes
  if (currentEnv === 'dev') {
    console.log('🔧 Development Notes:');
    console.log('   - Make sure backend server is running on port 8000');
    console.log('   - WebSocket mock server should be available');
    console.log('   - Hot reload is enabled for faster development');
  } else if (currentEnv === 'staging') {
    console.log('🧪 Staging Notes:');
    console.log('   - Ensure staging backend is accessible');
    console.log('   - SSL certificates should be valid');
    console.log('   - Test all integrations before promoting to prod');
  } else if (currentEnv === 'prod') {
    console.log('🚀 Production Notes:');
    console.log('   - All debugging is disabled');
    console.log('   - Performance monitoring is active');
    console.log('   - Error logging only');
    console.log('   - Ensure backend uptime and monitoring');
  }
}

// Display available environments
function listAvailableEnvironments() {
  console.log('');
  console.log('🌍 Available Environments:');

  try {
    const envFiles = fs.readdirSync(configDir)
      .filter(file => file.endsWith('.env'))
      .map(file => file.replace('.env', ''));

    envFiles.forEach(env => {
      const isCurrent = env === getCurrentEnvironment();
      const marker = isCurrent ? '👉' : '  ';
      console.log(`${marker} ${env}${isCurrent ? ' (current)' : ''}`);
    });
  } catch (error) {
    console.log('   - dev, staging, prod (expected)');
  }

  console.log('');
  console.log('To switch environments:');
  console.log('  npm run env:dev      # Switch to development');
  console.log('  npm run env:staging  # Switch to staging');
  console.log('  npm run env:prod     # Switch to production');
}

// Main execution
if (require.main === module) {
  displayStatus();
  listAvailableEnvironments();
}

module.exports = {
  getCurrentEnvironment,
  getEnvironmentConfig,
  displayStatus,
  listAvailableEnvironments
};
