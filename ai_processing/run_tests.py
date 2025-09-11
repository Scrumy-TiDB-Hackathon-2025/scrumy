#!/usr/bin/env python3
"""
Test runner for duplicate prevention fixes
"""
import sys
import os
import subprocess

def run_tests():
    """Run all duplicate prevention tests"""
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    print("🧪 Running Duplicate Prevention Tests...")
    print("=" * 50)
    
    test_files = [
        "tests/test_duplicate_prevention.py",
        "tests/test_websocket_integration.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        test_path = os.path.join(current_dir, test_file)
        if os.path.exists(test_path):
            print(f"\n📋 Running {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"
                ], cwd=current_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                    print(result.stdout)
                else:
                    print(f"❌ {test_file} - FAILED")
                    print(result.stdout)
                    print(result.stderr)
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ Error running {test_file}: {e}")
                all_passed = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests PASSED! Duplicate prevention fixes validated.")
        return 0
    else:
        print("💥 Some tests FAILED! Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())