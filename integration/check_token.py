#!/usr/bin/env python3
"""
Simple Notion Token Length Checker
Quickly verify if your Notion token has the correct length and format.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / ".env.integration"
if env_file.exists():
    load_dotenv(env_file)
else:
    env_file_parent = Path(__file__).parent.parent / ".env.integration"
    if env_file_parent.exists():
        load_dotenv(env_file_parent)
    else:
        load_dotenv()

def check_token():
    """Quick token format check"""
    token = os.getenv("NOTION_TOKEN", "").strip()

    print("🔍 Quick Token Check")
    print("=" * 30)

    if not token:
        print("❌ No NOTION_TOKEN found in environment")
        print("💡 Set your token in .env.integration file")
        return False

    print(f"Token: {token[:15]}...{token[-4:]}")
    print(f"Length: {len(token)} characters")

    if token.startswith('ntn_'):
        expected = 51
        print(f"Format: ntn_ (expected length: {expected})")
        if len(token) == expected:
            print("✅ Length is CORRECT!")
            return True
        else:
            print(f"❌ Length is WRONG! (missing {expected - len(token)} characters)")
            return False

    elif token.startswith('secret_'):
        expected = 54
        print(f"Format: secret_ (expected length: {expected})")
        if len(token) == expected:
            print("✅ Length is CORRECT!")
            return True
        else:
            print(f"❌ Length is WRONG! (missing {expected - len(token)} characters)")
            return False
    else:
        print("❌ Invalid format - should start with 'ntn_' or 'secret_'")
        return False

if __name__ == "__main__":
    check_token()
