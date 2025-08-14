#!/usr/bin/env node
// quick-test.js - Fast validation of ScrumBot Chrome Extension

const fs = require('fs');
const path = require('path');
const http = require('http');

console.log('⚡ ScrumBot Chrome Extension - Quick Validation');
console.log('===============================================\n');

class QuickValidator {
  constructor() {
    this.results = [];
  }

  async runValidation() {
    console.log('🚀 Running quick validation...\n');

    // Test 1: File Structure
    this.validateFileStructure();

    // Test 2: Manifest Validation
    this.validateManifest();

    // Test 3: Configuration
    this.validateConfiguration();

    // Test 4: Mock Server Health (if running)
    await this.validateMockServers();

    // Test 5: Test Scripts
    this.validateTestScripts();

    this.printResults();
  }

  validateFileStructure() {
    console.log('📁 Validating file structure...');
    
    const criticalFiles = [
      'manifest.json',
      'config.js',
      'content.js',
      'capture.html',
      'capture.js',
      'popup.html',
      'popup.js',
      'core/meetingdetector.js',
      'core/audiocapture.js',
      'core/scrumbotcontroller.js',
      'services/websocketclient.js',
      'worker/background.js'
    ];

    let missing = [];
    let present = [];

    criticalFiles.forEach(file => {
      const filePath = path.join(__dirname, file);
      if (fs.existsSync(filePath)) {
        present.push(file);
      } else {
        missing.push(file);
      }
    });

    const success = missing.length === 0;
    this.results.push({
      name: 'File Structure',
      success: success,
      details: `${present.length}/${criticalFiles.length} critical files present`
    });

    console.log(`   Result: ${success ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`   Files: ${present.length}/${criticalFiles.length} present`);
    if (missing.length > 0) {
      console.log(`   Missing: ${missing.join(', ')}`);
    }
    console.log('');
  }

  validateManifest() {
    console.log('📋 Validating manifest.json...');
    
    try {
      const manifestPath = path.join(__dirname, 'manifest.json');
      const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

      const checks = [
        { name: 'Manifest Version', pass: manifest.manifest_version === 3 },
        { name: 'Extension Name', pass: typeof manifest.name === 'string' && manifest.name.length > 0 },
        { name: 'Permissions', pass: Array.isArray(manifest.permissions) && manifest.permissions.length > 0 },
        { name: 'Content Scripts', pass: Array.isArray(manifest.content_scripts) && manifest.content_scripts.length > 0 },
        { name: 'Background Worker', pass: typeof manifest.background?.service_worker === 'string' },
        { name: 'Web Resources', pass: Array.isArray(manifest.web_accessible_resources) }
      ];

      const passed = checks.filter(c => c.pass).length;
      const success = passed === checks.length;

      this.results.push({
        name: 'Manifest Validation',
        success: success,
        details: `${passed}/${checks.length} checks passed`
      });

      console.log(`   Result: ${success ? '✅ PASS' : '❌ FAIL'}`);
      console.log(`   Checks: ${passed}/${checks.length} passed`);
      
      checks.forEach(check => {
        const status = check.pass ? '✅' : '❌';
        console.log(`     ${status} ${check.name}`);
      });
    } catch (error) {
      this.results.push({
        name: 'Manifest Validation',
        success: false,
        details: `Error: ${error.message}`
      });
      console.log(`   Result: ❌ FAIL - ${error.message}`);
    }
    console.log('');
  }

  validateConfiguration() {
    console.log('⚙️  Validating configuration...');
    
    try {
      const configPath = path.join(__dirname, 'config.js');
      const configContent = fs.readFileSync(configPath, 'utf8');

      const checks = [
        { name: 'Environment Variable', pass: configContent.includes('const ENVIRONMENT') },
        { name: 'Dev Config', pass: configContent.includes('dev:') },
        { name: 'Prod Config', pass: configContent.includes('prod:') },
        { name: 'Backend URL', pass: configContent.includes('BACKEND_URL') },
        { name: 'WebSocket URL', pass: configContent.includes('WEBSOCKET_URL') },
        { name: 'Mock Transcription', pass: configContent.includes('MOCK_TRANSCRIPTION') }
      ];

      const passed = checks.filter(c => c.pass).length;
      const success = passed === checks.length;

      this.results.push({
        name: 'Configuration',
        success: success,
        details: `${passed}/${checks.length} config elements found`
      });

      console.log(`   Result: ${success ? '✅ PASS' : '❌ FAIL'}`);
      console.log(`   Elements: ${passed}/${checks.length} found`);
    } catch (error) {
      this.results.push({
        name: 'Configuration',
        success: false,
        details: `Error: ${error.message}`
      });
      console.log(`   Result: ❌ FAIL - ${error.message}`);
    }
    console.log('');
  }

  async validateMockServers() {
    console.log('🖥️  Validating mock servers...');
    
    try {
      // Test REST API server
      const restHealthy = await this.checkHttpEndpoint('http://localhost:3002/health');
      const restMeetings = await this.checkHttpEndpoint('http://localhost:3002/get-meetings');

      const success = restHealthy && restMeetings;
      
      this.results.push({
        name: 'Mock Servers',
        success: success,
        details: `REST API: ${restHealthy ? 'healthy' : 'offline'}, Meetings: ${restMeetings ? 'accessible' : 'offline'}`
      });

      console.log(`   Result: ${success ? '✅ PASS' : '⚠️  PARTIAL'}`);
      console.log(`   REST API Health: ${restHealthy ? '✅' : '❌'}`);
      console.log(`   Meetings Endpoint: ${restMeetings ? '✅' : '❌'}`);
      
      if (!success) {
        console.log('   Note: Run "npm run dev" to start mock servers');
      }
    } catch (error) {
      this.results.push({
        name: 'Mock Servers',
        success: false,
        details: `Error: ${error.message}`
      });
      console.log(`   Result: ❌ FAIL - ${error.message}`);
    }
    console.log('');
  }

  validateTestScripts() {
    console.log('🧪 Validating test scripts...');
    
    const testFiles = [
      'test-controller.js',
      'test-extension.js', 
      'test-multitab.js',
      'test/core.js',
      'test/integration.js'
    ];

    let present = [];
    let missing = [];

    testFiles.forEach(file => {
      const filePath = path.join(__dirname, file);
      if (fs.existsSync(filePath)) {
        present.push(file);
      } else {
        missing.push(file);
      }
    });

    const success = missing.length === 0;
    
    this.results.push({
      name: 'Test Scripts',
      success: success,
      details: `${present.length}/${testFiles.length} test files present`
    });

    console.log(`   Result: ${success ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`   Test Files: ${present.length}/${testFiles.length} present`);
    if (missing.length > 0) {
      console.log(`   Missing: ${missing.join(', ')}`);
    }
    console.log('');
  }

  checkHttpEndpoint(url) {
    return new Promise((resolve) => {
      const request = http.get(url, (response) => {
        resolve(response.statusCode === 200);
      });
      
      request.on('error', () => {
        resolve(false);
      });
      
      request.setTimeout(2000, () => {
        request.destroy();
        resolve(false);
      });
    });
  }

  printResults() {
    console.log('🎯 Validation Results');
    console.log('====================');
    
    const passed = this.results.filter(r => r.success).length;
    const total = this.results.length;
    
    this.results.forEach(result => {
      const status = result.success ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${result.name}: ${result.details}`);
    });
    
    console.log('');
    console.log(`📊 Summary: ${passed}/${total} validations passed`);
    
    if (passed === total) {
      console.log('🎉 Chrome extension is properly configured and ready!');
      console.log('\n🚀 Next Steps:');
      console.log('   1. Start dev servers: npm run dev');
      console.log('   2. Load extension in Chrome');
      console.log('   3. Test multi-tab capture on Google Meet');
    } else {
      console.log('⚠️  Some validations failed. Please fix the issues above.');
    }
    
    console.log('\n💡 Available Commands:');
    console.log('   npm run dev          # Start mock servers');
    console.log('   npm run test:core    # Run core logic tests');
    console.log('   npm run env:dev      # Switch to dev mode');
    console.log('   npm run env:prod     # Switch to prod mode');
  }
}

// Run validation
const validator = new QuickValidator();
validator.runValidation().catch(error => {
  console.error('❌ Validation failed:', error);
  process.exit(1);
});