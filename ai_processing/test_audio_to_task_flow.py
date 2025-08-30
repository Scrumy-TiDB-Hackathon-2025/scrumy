#!/usr/bin/env python3
"""
Complete Audio-to-Task Flow Test

Tests the full pipeline:
Audio -> Transcript -> Extract Tasks -> Create Tasks

Uses mock meeting transcript since test audio may not contain tasks
"""

import asyncio
import sys
import os
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
def load_env():
    """Load GROQ API key from .env file"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"\'')
        print(f"✅ Loaded environment from {env_path}")
    else:
        print(f"⚠️  .env file not found at {env_path}")

# Load environment at startup
load_env()

from app.task_extractor import TaskExtractor
from app.ai_processor import AIProcessor
from app.integration_bridge import create_integration_bridge

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



async def test_audio_to_task_flow():
    """Test complete audio-to-task creation flow"""
    
    print("🎵 COMPLETE AUDIO-TO-TASK FLOW TEST")
    print("=" * 60)
    
    # Check if GROQ API key is available
    if not os.getenv('GROQ_API_KEY'):
        print("❌ GROQ_API_KEY not found in environment")
        print("💡 Run: ./setup_groq_key.sh to set up your API key")
        return
    
    # Step 1: Real Audio Transcription
    print("\n🔄 STEP 1: Audio Transcription")
    print("-" * 40)
    
    audio_file = "tests/data/meeting-test.wav"
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    print(f"📁 Using recorded audio: {audio_file}")
    
    # Use whisper.cpp directly for transcription
    try:
        import subprocess
        whisper_cmd = [
            "whisper.cpp/build/bin/whisper-cli",
            "-m", "whisper.cpp/models/ggml-base.en.bin",
            "-f", audio_file,
            "--output-txt"
        ]
        
        result = subprocess.run(whisper_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Whisper transcription failed: {result.stderr}")
            return
        
        # Extract transcript from output
        transcript = result.stdout.strip()
        if not transcript:
            print("❌ Empty transcription result")
            return
            
        print(f"✅ Transcription successful!")
        print(f"📝 Transcript length: {len(transcript)} characters")
        print(f"📄 Preview: {transcript[:200]}...")
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return
    
    # Step 2: Extract Tasks from Transcript
    print("\n🔄 STEP 2: Task Extraction")
    print("-" * 40)
    
    try:
        ai_processor = AIProcessor()
        task_extractor = TaskExtractor(ai_processor)
        
        # Extract tasks using AI
        extraction_result = await task_extractor.extract_comprehensive_tasks(
            transcript=transcript,
            meeting_context={
                "title": "Sprint Planning Meeting",
                "participants": ["Sarah (PM)", "John (Dev)", "Mike (DevOps)", "Lisa (QA)"],
                "platform": "mock_meeting"
            }
        )
        
        tasks = extraction_result.get('tasks', [])
        if not tasks:
            error = extraction_result.get('extraction_metadata', {}).get('error')
            if error:
                print(f"❌ Task extraction failed: {error}")
            else:
                print("⚠️  No tasks found in transcript")
            return
        print(f"✅ Task extraction successful!")
        print(f"📋 Tasks found: {len(tasks)}")
        
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task.get('title', 'No title')}")
            print(f"      👤 Assignee: {task.get('assignee', 'Unassigned')}")
            print(f"      🔥 Priority: {task.get('priority', 'medium')}")
        
    except Exception as e:
        print(f"❌ Task extraction error: {e}")
        return
    
    # Step 3: Create Tasks in Integration Platforms
    print("\n🔄 STEP 3: Task Creation")
    print("-" * 40)
    
    try:
        # Initialize integration bridge
        bridge = create_integration_bridge()
        
        if not bridge.enabled:
            print("⚠️  Integration bridge disabled - tasks will not be created")
            print("✅ Transcript-to-extraction flow completed successfully")
            return
        
        print("📡 Creating tasks in Notion and ClickUp...")
        
        # Create tasks
        creation_result = await bridge.create_tasks_from_ai_results(
            ai_tasks=tasks,
            meeting_context={
                "meeting_id": "sprint_planning_test",
                "title": "Sprint Planning Meeting"
            }
        )
        
        print(f"✅ Task creation completed!")
        print(f"📊 Results:")
        print(f"   • Tasks processed: {creation_result.get('tasks_processed', 0)}")
        print(f"   • Tasks created: {creation_result.get('tasks_created', 0)}")
        print(f"   • Successful platforms: {creation_result.get('successful_integrations', [])}")
        
        # Show task URLs if available
        task_urls = creation_result.get('task_urls', {})
        if task_urls:
            print(f"\n🔗 Created Task URLs:")
            for platform, urls in task_urls.items():
                print(f"   {platform.upper()}:")
                for url in urls:
                    print(f"     • {url}")
        
        if creation_result.get('errors'):
            print(f"\n⚠️  Errors encountered:")
            for error in creation_result['errors']:
                print(f"   • {error}")
        
    except Exception as e:
        print(f"❌ Task creation error: {e}")
        return
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎉 COMPLETE FLOW TEST SUCCESSFUL!")
    print(f"✅ Transcript processed: {len(transcript)} characters")
    print(f"✅ Tasks extracted: {len(tasks)}")
    print(f"✅ Tasks created: {creation_result.get('tasks_created', 0)}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_audio_to_task_flow())