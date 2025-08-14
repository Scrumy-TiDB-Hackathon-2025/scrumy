// switch-env.js - Utility to switch between dev and prod environments
const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, 'config.js');

function switchEnvironment(targetEnv) {
  if (!['dev', 'prod'].includes(targetEnv)) {
    console.error('❌ Invalid environment. Use "dev" or "prod"');
    process.exit(1);
  }

  try {
    // Read current config
    let configContent = fs.readFileSync(configPath, 'utf8');
    
    // Replace environment line
    const envRegex = /const ENVIRONMENT = '[^']+';/;
    const newEnvLine = `const ENVIRONMENT = '${targetEnv}';`;
    
    if (envRegex.test(configContent)) {
      configContent = configContent.replace(envRegex, newEnvLine);
    } else {
      console.error('❌ Could not find ENVIRONMENT constant in config.js');
      process.exit(1);
    }
    
    // Write updated config
    fs.writeFileSync(configPath, configContent);
    
    console.log(`✅ Environment switched to: ${targetEnv.toUpperCase()}`);
    
    if (targetEnv === 'dev') {
      console.log('🔧 Development mode:');
      console.log('   - Mock WebSocket: ws://localhost:8081/ws');
      console.log('   - Mock REST API: http://localhost:3001');
      console.log('   - Mock transcription enabled');
      console.log('   - Debug logging enabled');
      console.log('\n💡 Run: npm run dev (to start mock servers)');
    } else {
      console.log('🚀 Production mode:');
      console.log('   - Real backend integration');
      console.log('   - Live WebSocket connection');
      console.log('   - Actual transcription service');
      console.log('   - Debug logging disabled');
      console.log('\n💡 Make sure backend is running!');
    }
    
    console.log('\n🔄 Reload the extension in Chrome to apply changes');
    
  } catch (error) {
    console.error('❌ Error switching environment:', error.message);
    process.exit(1);
  }
}

// Command line usage
const targetEnv = process.argv[2];

if (!targetEnv) {
  console.log('🔧 ScrumBot Environment Switcher');
  console.log('Usage: node switch-env.js <dev|prod>');
  console.log('');
  console.log('Examples:');
  console.log('  node switch-env.js dev   # Switch to development mode');
  console.log('  node switch-env.js prod  # Switch to production mode');
  process.exit(0);
}

switchEnvironment(targetEnv);