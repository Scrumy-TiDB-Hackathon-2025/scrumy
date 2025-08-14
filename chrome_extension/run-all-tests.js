#!/usr/bin/env node
// run-all-tests.js - Comprehensive test runner for ScrumBot Chrome Extension

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🧪 ScrumBot Chrome Extension - Comprehensive Test Suite');
console.log('======================================================\n');

class TestRunner {
    constructor() {
        this.results = [];
        this.startTime = Date.now();
    }

    async runAllTests() {
        console.log('🚀 Starting comprehensive test suite...\n');

        // Test 1: Core Logic Tests (Node.js)
        await this.runTest('Core Logic Tests', 'npm run test:core');

        // Test 2: Mock Server Health Checks
        await this.runTest('Mock Server Health', 'curl -s http://localhost:3002/health');

        // Test 3: WebSocket Server Test
        await this.runTest('WebSocket Server Test', 'curl -s http://localhost:3002/get-meetings');

        // Test 4: Environment Configuration Test
        await this.runTest('Environment Configuration', 'node switch-env.js dev');

        // Test 5: File Structure Validation
        await this.runFileStructureTest();

        // Test 6: Manifest Validation
        await this.runManifestValidation();

        // Print final results
        this.printFinalResults();
    }

    async runTest(testName, command) {
        console.log(`📋 Running: ${testName}`);
        console.log(`   Command: ${command}`);

        try {
            const result = await this.executeCommand(command);
            const success = result.exitCode === 0;

            this.results.push({
                name: testName,
                success: success,
                output: result.output,
                error: result.error
            });

            console.log(`   Result: ${success ? '✅ PASS' : '❌ FAIL'}`);
            if (!success && result.error) {
                console.log(`   Error: ${result.error.substring(0, 100)}...`);
            }
        } catch (error) {
            this.results.push({
                name: testName,
                success: false,
                error: error.message
            });
            console.log(`   Result: ❌ FAIL - ${error.message}`);
        }

        console.log('');
    }

    async runFileStructureTest() {
        console.log('📋 Running: File Structure Validation');

        const requiredFiles = [
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
            'worker/background.js',
            'mocks/mockwebsocketserver.js',
            'mocks/mockrestserver.js',
            'test/core.js',
            'test/integration.js',
            'ARCHITECTURE.md',
            'README.md',
            'TESTING_GUIDE.md'
        ];

        let missingFiles = [];
        let presentFiles = [];

        requiredFiles.forEach(file => {
            const filePath = path.join(__dirname, file);
            if (fs.existsSync(filePath)) {
                presentFiles.push(file);
            } else {
                missingFiles.push(file);
            }
        });

        const success = missingFiles.length === 0;

        this.results.push({
            name: 'File Structure Validation',
            success: success,
            details: `Present: ${presentFiles.length}, Missing: ${missingFiles.length}`,
            missingFiles: missingFiles
        });

        console.log(`   Result: ${success ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`   Files: ${presentFiles.length}/${requiredFiles.length} present`);

        if (missingFiles.length > 0) {
            console.log(`   Missing: ${missingFiles.join(', ')}`);
        }
        console.log('');
    }

    async runManifestValidation() {
        console.log('📋 Running: Manifest Validation');

        try {
            const manifestPath = path.join(__dirname, 'manifest.json');
            const manifestContent = fs.readFileSync(manifestPath, 'utf8');
            const manifest = JSON.parse(manifestContent);

            const validations = [
                { check: 'manifest_version', expected: 3, actual: manifest.manifest_version },
                { check: 'name', expected: 'string', actual: typeof manifest.name },
                { check: 'permissions', expected: 'array', actual: Array.isArray(manifest.permissions) },
                { check: 'content_scripts', expected: 'array', actual: Array.isArray(manifest.content_scripts) },
                { check: 'background.service_worker', expected: 'string', actual: typeof manifest.background?.service_worker },
                { check: 'web_accessible_resources', expected: 'array', actual: Array.isArray(manifest.web_accessible_resources) }
            ];

            const failedValidations = validations.filter(v => {
                if (typeof v.expected === 'number') {
                    return v.actual !== v.expected;
                } else if (v.expected === 'string') {
                    return typeof v.actual !== 'string';
                } else if (v.expected === 'array') {
                    return !v.actual;
                }
                return false;
            });

            const success = failedValidations.length === 0;

            this.results.push({
                name: 'Manifest Validation',
                success: success,
                details: `${validations.length - failedValidations.length}/${validations.length} validations passed`,
                failedValidations: failedValidations
            });

            console.log(`   Result: ${success ? '✅ PASS' : '❌ FAIL'}`);
            console.log(`   Validations: ${validations.length - failedValidations.length}/${validations.length} passed`);

            if (failedValidations.length > 0) {
                failedValidations.forEach(v => {
                    console.log(`   Failed: ${v.check} - expected ${v.expected}, got ${v.actual}`);
                });
            }
        } catch (error) {
            this.results.push({
                name: 'Manifest Validation',
                success: false,
                error: error.message
            });
            console.log(`   Result: ❌ FAIL - ${error.message}`);
        }
        console.log('');
    }

    executeCommand(command) {
        return new Promise((resolve) => {
            const parts = command.split(' ');
            const cmd = parts[0];
            const args = parts.slice(1);

            let output = '';
            let error = '';

            const process = spawn(cmd, args, {
                cwd: __dirname,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            process.stdout.on('data', (data) => {
                output += data.toString();
            });

            process.stderr.on('data', (data) => {
                error += data.toString();
            });

            process.on('close', (code) => {
                resolve({
                    exitCode: code,
                    output: output,
                    error: error
                });
            });

            process.on('error', (err) => {
                resolve({
                    exitCode: 1,
                    output: output,
                    error: err.message
                });
            });
        });
    }

    printFinalResults() {
        const endTime = Date.now();
        const duration = ((endTime - this.startTime) / 1000).toFixed(2);

        console.log('🎯 Final Test Results');
        console.log('====================');

        const passed = this.results.filter(r => r.success).length;
        const total = this.results.length;

        this.results.forEach(result => {
            const status = result.success ? '✅ PASS' : '❌ FAIL';
            console.log(`${status} ${result.name}`);
            if (result.details) {
                console.log(`     ${result.details}`);
            }
        });

        console.log('');
        console.log(`📊 Summary: ${passed}/${total} tests passed`);
        console.log(`⏱️  Duration: ${duration} seconds`);

        if (passed === total) {
            console.log('🎉 All tests passed! Chrome extension is ready for deployment.');
        } else {
            console.log('⚠️  Some tests failed. Please review the issues above.');
        }

        console.log('\n🚀 Next Steps:');
        if (passed === total) {
            console.log('   1. Load extension in Chrome (chrome://extensions/)');
            console.log('   2. Test on Google Meet with multi-tab capture');
            console.log('   3. Verify audio capture and mock transcriptions');
            console.log('   4. Switch to production mode when backend is ready');
        } else {
            console.log('   1. Fix failing tests');
            console.log('   2. Re-run test suite');
            console.log('   3. Verify all components are working');
        }
    }
}

// Run the test suite
const runner = new TestRunner();
runner.runAllTests().catch(error => {
    console.error('❌ Test runner failed:', error);
    process.exit(1);
});