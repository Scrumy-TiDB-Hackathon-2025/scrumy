/**
 * Test Enhanced Features
 * Tests participant detection, speaker attribution, and task extraction
 */

class EnhancedFeaturesTest {
  constructor() {
    this.config = window.SCRUMBOT_CONFIG;
    this.testResults = [];
  }

  async runAllTests() {
    console.log('🧪 Testing Enhanced ScrumBot Features...\n');
    
    await this.testParticipantDetection();
    await this.testSpeakerIdentification();
    await this.testTaskExtraction();
    await this.testMeetingAnalysis();
    await this.testUIComponents();
    
    this.printResults();
  }

  async testParticipantDetection() {
    console.log('👥 Testing participant detection...');
    
    try {
      if (window.meetingDetector) {
        const participants = window.meetingDetector.getParticipants();
        const participantCount = window.meetingDetector.getParticipantCount();
        
        console.log(`   Found ${participantCount} participants:`, participants);
        
        this.testResults.push({
          test: 'Participant Detection',
          passed: true,
          details: `Detected ${participantCount} participants`
        });
      } else {
        throw new Error('Meeting detector not available');
      }
    } catch (error) {
      console.error('   ❌ Participant detection failed:', error);
      this.testResults.push({
        test: 'Participant Detection',
        passed: false,
        details: error.message
      });
    }
  }

  async testSpeakerIdentification() {
    console.log('🗣️ Testing speaker identification...');
    
    try {
      const mockTranscript = "John: Hello everyone, welcome to our meeting. Sarah: Thanks John, I have the agenda ready.";
      
      const response = await fetch(`${this.config.BACKEND_URL}/identify-speakers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({
          text: mockTranscript,
          context: 'Team meeting with John and Sarah'
        })
      });
      
      const result = await response.json();
      
      if (result.status === 'success' && result.data.speakers) {
        console.log(`   ✅ Identified ${result.data.total_speakers} speakers`);
        console.log('   Speakers:', result.data.speakers.map(s => s.name));
        
        this.testResults.push({
          test: 'Speaker Identification',
          passed: true,
          details: `Identified ${result.data.total_speakers} speakers with ${Math.round(result.data.confidence * 100)}% confidence`
        });
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('   ❌ Speaker identification failed:', error);
      this.testResults.push({
        test: 'Speaker Identification',
        passed: false,
        details: error.message
      });
    }
  }

  async testTaskExtraction() {
    console.log('✅ Testing task extraction...');
    
    try {
      const mockTranscript = "We need to update the authentication system by Friday. John will handle the OAuth implementation. Sarah should review the security requirements.";
      
      const response = await fetch(`${this.config.BACKEND_URL}/extract-tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({
          transcript: mockTranscript,
          meeting_context: 'Sprint planning meeting'
        })
      });
      
      const result = await response.json();
      
      if (result.status === 'success' && result.data.tasks) {
        console.log(`   ✅ Extracted ${result.data.tasks.length} tasks`);
        result.data.tasks.forEach(task => {
          console.log(`   - ${task.title} (${task.priority} priority, assigned to ${task.assignee})`);
        });
        
        this.testResults.push({
          test: 'Task Extraction',
          passed: true,
          details: `Extracted ${result.data.tasks.length} tasks`
        });
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('   ❌ Task extraction failed:', error);
      this.testResults.push({
        test: 'Task Extraction',
        passed: false,
        details: error.message
      });
    }
  }

  async testMeetingAnalysis() {
    console.log('📊 Testing comprehensive meeting analysis...');
    
    try {
      const mockTranscript = "John: Let's start our sprint planning. Sarah: I've prepared the backlog. We need to prioritize the authentication feature. John: Agreed, I'll handle the OAuth implementation by Friday.";
      
      const response = await fetch(`${this.config.BACKEND_URL}/process-transcript-with-tools`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({
          text: mockTranscript,
          meeting_id: 'test-meeting-' + Date.now(),
          timestamp: new Date().toISOString(),
          platform: 'google-meet'
        })
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        console.log('   ✅ Meeting analysis completed');
        console.log(`   - Speakers: ${result.speakers?.length || 0}`);
        console.log(`   - Tasks: ${result.actions_taken?.length || 0}`);
        console.log(`   - Tools used: ${result.tools_used || 0}`);
        
        this.testResults.push({
          test: 'Meeting Analysis',
          passed: true,
          details: `Analysis completed with ${result.tools_used} tools`
        });
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('   ❌ Meeting analysis failed:', error);
      this.testResults.push({
        test: 'Meeting Analysis',
        passed: false,
        details: error.message
      });
    }
  }

  async testUIComponents() {
    console.log('🎨 Testing UI components...');
    
    try {
      if (window.scrumBotUI) {
        // Test UI creation
        const testMeetingId = 'test-ui-' + Date.now();
        window.scrumBotUI.createEnhancedUI(testMeetingId);
        
        // Test participant update
        const mockParticipants = [
          { id: '1', name: 'John Smith', status: 'active' },
          { id: '2', name: 'Sarah Johnson', status: 'active' }
        ];
        window.scrumBotUI.updateParticipants(mockParticipants);
        
        // Test transcript addition
        const mockTranscript = {
          text: 'This is a test transcript',
          speaker: 'John Smith',
          confidence: 0.95,
          timestamp: new Date().toISOString()
        };
        window.scrumBotUI.addTranscript(mockTranscript);
        
        // Test task update
        const mockAnalysis = {
          action_items: [
            {
              title: 'Test task',
              assignee: 'John Smith',
              priority: 'high',
              due_date: '2025-01-20'
            }
          ]
        };
        window.scrumBotUI.updateMeetingAnalysis(mockAnalysis);
        
        console.log('   ✅ UI components working correctly');
        
        this.testResults.push({
          test: 'UI Components',
          passed: true,
          details: 'All UI components functional'
        });
      } else {
        throw new Error('ScrumBot UI not available');
      }
    } catch (error) {
      console.error('   ❌ UI components failed:', error);
      this.testResults.push({
        test: 'UI Components',
        passed: false,
        details: error.message
      });
    }
  }

  printResults() {
    console.log('\n' + '='.repeat(50));
    console.log('🧪 ENHANCED FEATURES TEST RESULTS');
    console.log('='.repeat(50));
    
    let passed = 0;
    const total = this.testResults.length;
    
    this.testResults.forEach(result => {
      const status = result.passed ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${result.test}: ${result.details}`);
      if (result.passed) passed++;
    });
    
    console.log(`\n📊 Summary: ${passed}/${total} tests passed`);
    
    if (passed === total) {
      console.log('🎉 All enhanced features are working!');
      console.log('\n🚀 Ready for Epic B integration:');
      console.log('   ✅ Participant detection ready');
      console.log('   ✅ Speaker identification ready');
      console.log('   ✅ Task extraction ready');
      console.log('   ✅ UI components ready');
    } else {
      console.log('⚠️  Some tests failed. Please review and fix.');
    }
    
    console.log('\n💡 Next steps:');
    console.log('   1. Start mock servers: npm run dev');
    console.log('   2. Load extension in Chrome');
    console.log('   3. Test on Google Meet/Zoom/Teams');
    console.log('   4. Wait for Epic B backend to be ready');
  }
}

// Auto-run tests if script is loaded
if (typeof window !== 'undefined' && window.SCRUMBOT_CONFIG) {
  // Wait for components to load
  setTimeout(() => {
    const tester = new EnhancedFeaturesTest();
    tester.runAllTests();
  }, 2000);
} else {
  console.log('⚠️ ScrumBot config not loaded. Load this script in a meeting tab.');
}

// Make available globally for manual testing
window.testEnhancedFeatures = () => {
  const tester = new EnhancedFeaturesTest();
  tester.runAllTests();
};

console.log('✅ Enhanced Features Test loaded. Run window.testEnhancedFeatures() to test manually.');