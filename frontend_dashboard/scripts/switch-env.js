// switch-env.js - Utility to switch between dev, staging, and prod environments
const fs = require('fs');
const path = require('path');

const configDir = path.join(__dirname, '..', 'config');
const envFilePath = path.join(__dirname, '..', '.env.local');

function switchEnvironment(targetEnv) {
  if (!['dev', 'staging', 'prod'].includes(targetEnv)) {
    console.error('❌ Invalid environment. Use "dev", "staging", or "prod"');
    process.exit(1);
  }

  const sourceEnvFile = path.join(configDir, `${targetEnv}.env`);

  try {
    // Check if source environment file exists
    if (!fs.existsSync(sourceEnvFile)) {
      console.error(`❌ Environment file not found: ${sourceEnvFile}`);
      process.exit(1);
    }

    // Read the source environment file
    const envContent = fs.readFileSync(sourceEnvFile, 'utf8');

    // Write to .env.local (Next.js will automatically load this)
    fs.writeFileSync(envFilePath, envContent);

    console.log(`✅ Environment switched to: ${targetEnv.toUpperCase()}`);

    // Display environment-specific information
    if (targetEnv === 'dev') {
      console.log('🔧 Development mode:');
      console.log('   - Backend: http://localhost:8000');
      console.log('   - WebSocket: ws://localhost:8000/ws/audio');
      console.log('   - Mock data enabled');
      console.log('   - Debug logging enabled');
      console.log('   - Hot reload enabled');
      console.log('\n💡 Run: npm run dev (to start development server)');
    } else if (targetEnv === 'staging') {
      console.log('🧪 Staging mode:');
      console.log('   - Backend: https://staging-api.scrumy.app');
      console.log('   - WebSocket: wss://staging-api.scrumy.app/ws/audio');
      console.log('   - Real backend integration');
      console.log('   - Debug logging enabled');
      console.log('   - Production-like data');
      console.log('\n💡 Run: npm run build && npm run start');
    } else {
      console.log('🚀 Production mode:');
      console.log('   - Backend: https://b5462b7bbb65.ngrok-free.app');
      console.log('   - WebSocket: wss://b5462b7bbb65.ngrok-free.app/ws/audio-stream');
      console.log('   - Live backend integration');
      console.log('   - Error logging only');
      console.log('   - Optimized performance');
      console.log('\n💡 Run: npm run build && npm run start');
    }

    console.log(`\n📝 Environment variables loaded from: config/${targetEnv}.env`);
    console.log('🔄 Restart the development server to apply changes');

  } catch (error) {
    console.error('❌ Error switching environment:', error.message);
    process.exit(1);
  }
}

// Command line usage
const targetEnv = process.argv[2];

if (!targetEnv) {
  console.log('🔧 ScrumBot Frontend Environment Switcher');
  console.log('Usage: node scripts/switch-env.js <dev|staging|prod>');
  console.log('');
  console.log('Examples:');
  console.log('  node scripts/switch-env.js dev      # Switch to development mode');
  console.log('  node scripts/switch-env.js staging  # Switch to staging mode');
  console.log('  node scripts/switch-env.js prod     # Switch to production mode');
  console.log('');
  console.log('Available environments:');

  // List available environment files
  try {
    const envFiles = fs.readdirSync(configDir)
      .filter(file => file.endsWith('.env'))
      .map(file => file.replace('.env', ''));

    envFiles.forEach(env => {
      console.log(`  - ${env}`);
    });
  } catch (error) {
    console.log('  - dev, staging, prod (expected)');
  }

  process.exit(0);
}

switchEnvironment(targetEnv);
