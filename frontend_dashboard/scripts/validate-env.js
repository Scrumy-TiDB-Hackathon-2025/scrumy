// validate-env.js - Validate environment configuration and connectivity
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const envFilePath = path.join(__dirname, '..', '.env.local');

function loadCurrentEnvironment() {
  if (!fs.existsSync(envFilePath)) {
    console.log('❌ No environment configuration found');
    console.log('Run: npm run env:dev to set up development environment');
    process.exit(1);
  }

  const envContent = fs.readFileSync(envFilePath, 'utf8');
  const config = {};

  envContent.split('\n').forEach(line => {
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

function validateRequiredFields(config) {
  console.log('🔍 Validating required configuration fields...');

  const requiredFields = [
    'NEXT_PUBLIC_ENVIRONMENT',
    'NEXT_PUBLIC_BACKEND_URL',
    'NEXT_PUBLIC_WEBSOCKET_URL',
    'NEXT_PUBLIC_FRONTEND_URL',
    'NEXT_PUBLIC_VERSION'
  ];

  const missingFields = requiredFields.filter(field => !config[field]);

  if (missingFields.length > 0) {
    console.log('❌ Missing required fields:');
    missingFields.forEach(field => {
      console.log(`   - ${field}`);
    });
    return false;
  }

  console.log('✅ All required fields present');
  return true;
}

function validateUrlFormat(config) {
  console.log('🔍 Validating URL formats...');

  const urlFields = [
    { field: 'NEXT_PUBLIC_BACKEND_URL', name: 'Backend URL' },
    { field: 'NEXT_PUBLIC_WEBSOCKET_URL', name: 'WebSocket URL' },
    { field: 'NEXT_PUBLIC_FRONTEND_URL', name: 'Frontend URL' }
  ];

  let allValid = true;

  urlFields.forEach(({ field, name }) => {
    const url = config[field];
    if (!url) return;

    try {
      new URL(url);
      console.log(`✅ ${name}: Valid format`);
    } catch (error) {
      console.log(`❌ ${name}: Invalid URL format - ${url}`);
      allValid = false;
    }
  });

  return allValid;
}

function validateBooleanFields(config) {
  console.log('🔍 Validating boolean fields...');

  const booleanFields = [
    'NEXT_PUBLIC_DEBUG',
    'NEXT_PUBLIC_MOCK_DATA',
    'NEXT_PUBLIC_ENABLE_WEBSOCKET',
    'NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES',
    'NEXT_PUBLIC_ENABLE_MOCK_TRANSCRIPTION'
  ];

  let allValid = true;

  booleanFields.forEach(field => {
    const value = config[field];
    if (!value) return;

    if (!['true', 'false'].includes(value.toLowerCase())) {
      console.log(`❌ ${field}: Must be 'true' or 'false', got '${value}'`);
      allValid = false;
    }
  });

  if (allValid) {
    console.log('✅ All boolean fields valid');
  }

  return allValid;
}

function validateNumericFields(config) {
  console.log('🔍 Validating numeric fields...');

  const numericFields = [
    { field: 'NEXT_PUBLIC_REFRESH_INTERVAL', min: 100, max: 60000 },
    { field: 'NEXT_PUBLIC_TIMEOUT', min: 1000, max: 300000 }
  ];

  let allValid = true;

  numericFields.forEach(({ field, min, max }) => {
    const value = config[field];
    if (!value) return;

    const num = parseInt(value, 10);
    if (isNaN(num)) {
      console.log(`❌ ${field}: Must be a number, got '${value}'`);
      allValid = false;
      return;
    }

    if (num < min || num > max) {
      console.log(`❌ ${field}: Must be between ${min} and ${max}, got ${num}`);
      allValid = false;
      return;
    }
  });

  if (allValid) {
    console.log('✅ All numeric fields valid');
  }

  return allValid;
}

function testHttpConnection(url, timeout = 10000) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;

    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: '/health',
      method: 'GET',
      timeout: timeout,
      headers: {
        'User-Agent': 'ScrumBot-Frontend-Validator/1.0'
      }
    };

    const req = client.request(options, (res) => {
      resolve({
        success: true,
        statusCode: res.statusCode,
        statusMessage: res.statusMessage
      });
    });

    req.on('error', (error) => {
      resolve({
        success: false,
        error: error.message
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        success: false,
        error: 'Connection timeout'
      });
    });

    req.end();
  });
}

async function testConnectivity(config) {
  console.log('🔍 Testing connectivity...');

  const backendUrl = config.NEXT_PUBLIC_BACKEND_URL;
  if (!backendUrl) {
    console.log('⚠️  No backend URL configured');
    return false;
  }

  console.log(`🔗 Testing connection to: ${backendUrl}`);

  const result = await testHttpConnection(backendUrl, 10000);

  if (result.success) {
    console.log(`✅ Backend connection successful (${result.statusCode})`);
    return true;
  } else {
    console.log(`❌ Backend connection failed: ${result.error}`);

    // Provide environment-specific guidance
    const env = config.NEXT_PUBLIC_ENVIRONMENT;
    if (env === 'dev') {
      console.log('💡 Development troubleshooting:');
      console.log('   - Make sure your backend server is running');
      console.log('   - Check if port 8000 is available');
      console.log('   - Try: curl http://localhost:8000/health');
    } else if (env === 'staging') {
      console.log('💡 Staging troubleshooting:');
      console.log('   - Verify staging server is deployed and running');
      console.log('   - Check DNS resolution');
      console.log('   - Verify SSL certificates');
    } else if (env === 'prod') {
      console.log('💡 Production troubleshooting:');
      console.log('   - Check production server status');
      console.log('   - Verify domain and SSL certificates');
      console.log('   - Check firewall and security settings');
    }

    return false;
  }
}

function displayConfiguration(config) {
  console.log('📋 Current Configuration:');
  console.log(`   Environment: ${config.NEXT_PUBLIC_ENVIRONMENT}`);
  console.log(`   Version: ${config.NEXT_PUBLIC_VERSION}`);
  console.log(`   Backend: ${config.NEXT_PUBLIC_BACKEND_URL}`);
  console.log(`   WebSocket: ${config.NEXT_PUBLIC_WEBSOCKET_URL}`);
  console.log(`   Debug: ${config.NEXT_PUBLIC_DEBUG}`);
  console.log(`   Mock Data: ${config.NEXT_PUBLIC_MOCK_DATA}`);
  console.log('');
}

async function main() {
  console.log('🔧 ScrumBot Frontend Dashboard - Environment Validation');
  console.log('======================================================');
  console.log('');

  try {
    // Load configuration
    const config = loadCurrentEnvironment();
    displayConfiguration(config);

    let allValid = true;

    // Run validation checks
    allValid = validateRequiredFields(config) && allValid;
    console.log('');

    allValid = validateUrlFormat(config) && allValid;
    console.log('');

    allValid = validateBooleanFields(config) && allValid;
    console.log('');

    allValid = validateNumericFields(config) && allValid;
    console.log('');

    // Test connectivity (optional - only for non-dev or if explicitly requested)
    const testConnectivity_arg = process.argv.includes('--test-connectivity');
    const env = config.NEXT_PUBLIC_ENVIRONMENT;

    if (testConnectivity_arg || (env !== 'dev' && !config.NEXT_PUBLIC_MOCK_DATA)) {
      const connectivityOk = await testConnectivity(config);
      allValid = connectivityOk && allValid;
      console.log('');
    } else if (env === 'dev') {
      console.log('ℹ️  Skipping connectivity test for development environment');
      console.log('   Use --test-connectivity flag to force connectivity testing');
      console.log('');
    }

    // Final result
    if (allValid) {
      console.log('✅ Environment validation passed!');
      console.log('🚀 Your configuration is ready for use.');

      console.log('');
      console.log('Next steps:');
      if (env === 'dev') {
        console.log('  npm run dev    # Start development server');
      } else {
        console.log('  npm run build  # Build the application');
        console.log('  npm run start  # Start production server');
      }
    } else {
      console.log('❌ Environment validation failed!');
      console.log('🔧 Please fix the issues above before proceeding.');
      process.exit(1);
    }

  } catch (error) {
    console.log('❌ Validation error:', error.message);
    process.exit(1);
  }
}

// Command line usage
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Unexpected error:', error);
    process.exit(1);
  });
}

module.exports = {
  loadCurrentEnvironment,
  validateRequiredFields,
  validateUrlFormat,
  validateBooleanFields,
  validateNumericFields,
  testConnectivity
};
