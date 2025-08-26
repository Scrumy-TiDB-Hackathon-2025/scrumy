#!/usr/bin/env node

/**
 * Frontend Dashboard Test Suite
 * Tests the Next.js frontend dashboard components and functionality
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Frontend Dashboard Test Suite');
console.log('================================\n');

// Test results tracking
let passed = 0;
let failed = 0;
const results = [];

function test(name, testFn) {
  try {
    testFn();
    console.log(`✅ ${name}`);
    passed++;
    results.push({ name, status: 'PASS' });
  } catch (error) {
    console.log(`❌ ${name}: ${error.message}`);
    failed++;
    results.push({ name, status: 'FAIL', error: error.message });
  }
}

// Test 1: Check if all required files exist
test('Required files exist', () => {
  const requiredFiles = [
    'package.json',
    'next.config.mjs',
    'app/page.js',
    'app/layout.js',
    'app/globals.css',
    'components/Sidebar.js',
    'components/Topbar.js',
    'components/MeetingCard.js',
    'components/CalendarSection.js',
    'components/ChatSection.js'
  ];

  requiredFiles.forEach(file => {
    if (!fs.existsSync(file)) {
      throw new Error(`Missing required file: ${file}`);
    }
  });
});

// Test 2: Check package.json structure
test('Package.json has required dependencies', () => {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  
  const requiredDeps = [
    'next',
    'react',
    'react-dom',
    'antd',
    'lucide-react',
    'react-icons',
    'dayjs'
  ];

  requiredDeps.forEach(dep => {
    if (!packageJson.dependencies[dep]) {
      throw new Error(`Missing dependency: ${dep}`);
    }
  });

  const requiredScripts = ['dev', 'build', 'start'];
  requiredScripts.forEach(script => {
    if (!packageJson.scripts[script]) {
      throw new Error(`Missing script: ${script}`);
    }
  });
});

// Test 3: Check component imports and exports
test('Components have proper imports/exports', () => {
  const components = [
    'components/Sidebar.js',
    'components/Topbar.js',
    'components/MeetingCard.js',
    'components/CalendarSection.js',
    'components/ChatSection.js'
  ];

  components.forEach(component => {
    const content = fs.readFileSync(component, 'utf8');
    
    // Check for export default
    if (!content.includes('export default')) {
      throw new Error(`${component} missing default export`);
    }
  });
});

// Test 4: Check main page structure
test('Main page has required structure', () => {
  const pageContent = fs.readFileSync('app/page.js', 'utf8');
  
  const requiredElements = [
    'useState',
    'useEffect',
    'CalendarSection',
    'ChatSection',
    'MeetingCard',
    'apiCall',
    'backendUrl'
  ];

  requiredElements.forEach(element => {
    if (!pageContent.includes(element)) {
      throw new Error(`Main page missing: ${element}`);
    }
  });
});

// Test 5: Check layout structure
test('Layout has proper structure', () => {
  const layoutContent = fs.readFileSync('app/layout.js', 'utf8');
  
  const requiredElements = [
    'Sidebar',
    'Topbar',
    'metadata',
    'RootLayout'
  ];

  requiredElements.forEach(element => {
    if (!layoutContent.includes(element)) {
      throw new Error(`Layout missing: ${element}`);
    }
  });
});

// Test 6: Check CSS and styling setup
test('Styling setup is correct', () => {
  const tailwindConfig = fs.readFileSync('tailwind.config.js', 'utf8');
  const globalsCss = fs.readFileSync('app/globals.css', 'utf8');
  
  if (!tailwindConfig.includes('tailwindcss')) {
    throw new Error('Tailwind config incomplete');
  }
  
  if (!globalsCss.includes('@tailwind')) {
    throw new Error('Tailwind directives missing in globals.css');
  }
});

// Test 7: Check API integration setup
test('API integration is properly configured', () => {
  const pageContent = fs.readFileSync('app/page.js', 'utf8');
  
  // Check for proper API call structure
  if (!pageContent.includes('ngrok-skip-browser-warning')) {
    throw new Error('Missing ngrok header configuration');
  }
  
  if (!pageContent.includes('/health') || !pageContent.includes('/get-meetings')) {
    throw new Error('Missing required API endpoints');
  }
  
  if (!pageContent.includes('NEXT_PUBLIC_API_URL')) {
    throw new Error('Missing environment variable configuration');
  }
});

// Test 8: Check responsive design elements
test('Components have responsive design', () => {
  const components = [
    'components/Sidebar.js',
    'app/page.js',
    'components/CalendarSection.js'
  ];

  components.forEach(component => {
    const content = fs.readFileSync(component, 'utf8');
    
    // Check for responsive classes
    const responsivePatterns = [
      /md:/,
      /lg:/,
      /sm:/,
      /flex/,
      /grid/
    ];

    const hasResponsive = responsivePatterns.some(pattern => pattern.test(content));
    if (!hasResponsive) {
      throw new Error(`${component} lacks responsive design elements`);
    }
  });
});

// Test 9: Check error handling
test('Error handling is implemented', () => {
  const pageContent = fs.readFileSync('app/page.js', 'utf8');
  
  if (!pageContent.includes('try') || !pageContent.includes('catch')) {
    throw new Error('Missing try-catch error handling');
  }
  
  if (!pageContent.includes('setError')) {
    throw new Error('Missing error state management');
  }
});

// Test 10: Check accessibility features
test('Basic accessibility features present', () => {
  const sidebarContent = fs.readFileSync('components/Sidebar.js', 'utf8');
  const topbarContent = fs.readFileSync('components/Topbar.js', 'utf8');
  
  if (!sidebarContent.includes('aria-label')) {
    throw new Error('Sidebar missing aria-label attributes');
  }
  
  if (!topbarContent.includes('placeholder')) {
    throw new Error('Search input missing placeholder');
  }
});

console.log('\n📊 Test Results Summary');
console.log('======================');
console.log(`✅ Passed: ${passed}`);
console.log(`❌ Failed: ${failed}`);
console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%\n`);

if (failed > 0) {
  console.log('❌ Failed Tests:');
  results.filter(r => r.status === 'FAIL').forEach(r => {
    console.log(`   • ${r.name}: ${r.error}`);
  });
  console.log('');
}

// Test 11: Create a simple component test
test('Components can be syntax-checked', () => {
  const { execSync } = require('child_process');
  
  const components = [
    'app/page.js',
    'app/layout.js',
    'components/Sidebar.js',
    'components/Topbar.js'
  ];

  components.forEach(component => {
    try {
      execSync(`node --check ${component}`, { stdio: 'pipe' });
    } catch (error) {
      throw new Error(`Syntax error in ${component}`);
    }
  });
});

console.log('🎯 Recommendations:');
console.log('==================');

if (passed === (passed + failed)) {
  console.log('🎉 All tests passed! Your frontend is ready for development.');
  console.log('');
  console.log('Next steps:');
  console.log('1. Install dependencies: npm install');
  console.log('2. Start development server: npm run dev');
  console.log('3. Test API connectivity with backend');
  console.log('4. Add unit tests with Jest/React Testing Library');
} else {
  console.log('🔧 Fix the failing tests above before proceeding.');
  console.log('');
  console.log('Common fixes:');
  console.log('1. Ensure all files are in correct locations');
  console.log('2. Check import/export statements');
  console.log('3. Verify package.json dependencies');
}

process.exit(failed > 0 ? 1 : 0);