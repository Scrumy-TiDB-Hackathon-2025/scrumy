#!/usr/bin/env python3
"""
Notion Token Validation Helper
Helps validate and troubleshoot Notion API tokens, especially new ntn_ format tokens.
"""

import os
import re
import asyncio
import aiohttp
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

class NotionTokenValidator:
    """Validates Notion API tokens and provides troubleshooting guidance"""

    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN", "").strip()
        self.base_url = "https://api.notion.com/v1"

    def analyze_token_format(self):
        """Analyze token format and provide guidance"""
        print("🔍 Token Format Analysis:")
        print("=" * 40)

        if not self.token:
            print("❌ No token found in NOTION_TOKEN environment variable")
            print("\n💡 Setup Instructions:")
            print("1. Go to https://www.notion.so/my-integrations")
            print("2. Create or select your integration")
            print("3. Copy the 'Internal Integration Token'")
            print("4. Set it in your .env.integration file:")
            print("   NOTION_TOKEN=ntn_your_token_here")
            return False

        print(f"Token length: {len(self.token)} characters")
        print(f"First 10 characters: {self.token[:10]}")
        print(f"Last 4 characters: ...{self.token[-4:]}")

        # Check for common issues
        issues = []

        # Format validation
        if self.token.startswith('ntn_'):
            print("✅ Token uses new ntn_ format (post Sept 2024)")
        elif self.token.startswith('secret_'):
            print("✅ Token uses legacy secret_ format (still valid)")
        else:
            print("❌ Token doesn't start with 'ntn_' or 'secret_'")
            issues.append("Invalid token prefix")

        # Length validation - tokens can vary in length, so just check reasonable bounds
        min_length = 40
        max_length = 60

        if len(self.token) < min_length:
            print(f"⚠️  Token seems too short (length: {len(self.token)})")
            issues.append("Token too short")
        elif len(self.token) > max_length:
            print(f"⚠️  Token seems too long (length: {len(self.token)})")
            issues.append("Token too long")
        else:
            print(f"✅ Token length appears reasonable ({len(self.token)} characters)")

        # Character validation
        if self.token.startswith(('ntn_', 'secret_')):
            token_body = self.token.split('_', 1)[1]
            if not re.match(r'^[A-Za-z0-9]+$', token_body):
                print("❌ Token contains invalid characters (should be alphanumeric)")
                issues.append("Invalid characters in token")
            else:
                print("✅ Token contains valid characters")

        # Common copy-paste issues
        if ' ' in self.token:
            print("❌ Token contains spaces")
            issues.append("Token contains spaces")

        if '\n' in self.token or '\r' in self.token:
            print("❌ Token contains line breaks")
            issues.append("Token contains line breaks")

        if self.token != self.token.strip():
            print("❌ Token has leading/trailing whitespace")
            issues.append("Leading/trailing whitespace")

        print(f"\nFormat Issues Found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")

        # Don't fail validation for minor length variations
        critical_issues = [issue for issue in issues if "too short" in issue or "too long" in issue or "Invalid" in issue or "contains" in issue]
        return len(critical_issues) == 0

    async def test_token_validity(self):
        """Test if token is valid by making API call"""
        print("\n🔐 Token Validity Test:")
        print("=" * 40)

        if not self.token:
            print("❌ No token to test")
            return False

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28"
        }

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/users", headers=headers) as response:
                    print(f"API Response Status: {response.status}")

                    if response.status == 200:
                        data = await response.json()
                        print("✅ Token is VALID!")
                        print(f"Bot user ID: {data.get('bot', {}).get('id', 'Unknown')}")
                        print(f"Workspace ID: {data.get('bot', {}).get('workspace', {}).get('id', 'Unknown')}")
                        return True

                    elif response.status == 401:
                        try:
                            error_data = await response.json()
                            error_code = error_data.get('code', 'unknown')
                            error_message = error_data.get('message', 'Unknown error')

                            print("❌ Token is INVALID")
                            print(f"Error Code: {error_code}")
                            print(f"Error Message: {error_message}")

                            if error_code == 'unauthorized':
                                print("\n💡 Common Causes:")
                                print("1. Token was copied incorrectly")
                                print("2. Integration was deleted/recreated")
                                print("3. Token was regenerated")
                                print("4. Integration is disabled")

                        except:
                            print("❌ Token is INVALID (unable to parse error)")

                        return False

                    else:
                        print(f"❌ Unexpected response: {response.status}")
                        try:
                            error_data = await response.json()
                            print(f"Error: {error_data}")
                        except:
                            print(f"Response text: {await response.text()}")
                        return False

        except aiohttp.ClientError as e:
            print(f"❌ Network error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False

    def get_integration_info(self):
        """Extract integration information from token if possible"""
        print("\n📋 Integration Information:")
        print("=" * 40)

        if not self.token:
            print("❌ No token available for analysis")
            return

        # Basic info we can determine
        if self.token.startswith('ntn_'):
            print("🆕 New format token (ntn_)")
            print("📅 Created: After September 2024")
        elif self.token.startswith('secret_'):
            print("📜 Legacy format token (secret_)")
            print("📅 Created: Before September 2024")

        print(f"🔗 Token type: Integration token")
        print(f"📏 Token length: {len(self.token)} chars")

        # Note: We can't decode the token content as it's not JWT
        print("\n💡 Note: Notion tokens are opaque and cannot be decoded")
        print("   To get detailed integration info, the token must be valid")

    def provide_troubleshooting_steps(self):
        """Provide step-by-step troubleshooting guide"""
        print("\n🛠️  Troubleshooting Steps:")
        print("=" * 40)

        print("\n1. 🔄 Regenerate Token:")
        print("   a. Go to https://www.notion.so/my-integrations")
        print("   b. Click on 'ScrumBot Test Integration'")
        print("   c. Go to 'Secrets' tab")
        print("   d. Click 'Regenerate Token'")
        print("   e. Copy the new token (will start with ntn_)")
        print("   f. Update your .env.integration file")

        print("\n2. 🔍 Verify Integration Status:")
        print("   a. Check integration is not disabled")
        print("   b. Verify workspace permissions")
        print("   c. Confirm integration type (Internal/Public)")

        print("\n3. ✅ Test Environment Setup:")
        print("   a. Check .env.integration file exists")
        print("   b. Verify NOTION_TOKEN variable name")
        print("   c. Ensure no extra quotes around token")
        print("   d. Restart application after changes")

        print("\n4. 🗄️  Database Sharing (if token is valid):")
        print("   a. Open your Notion database")
        print("   b. Click '...' menu → 'Connections'")
        print("   c. Add 'ScrumBot Test Integration'")
        print("   d. Grant read/write permissions")

        print("\n5. 🧪 Test with curl:")
        print("   Run this command to test directly:")
        if self.token:
            print(f'   curl -H "Authorization: Bearer {self.token[:15]}..." \\')
            print('        -H "Notion-Version: 2022-06-28" \\')
            print('        https://api.notion.com/v1/users')
        else:
            print('   curl -H "Authorization: Bearer YOUR_TOKEN" \\')
            print('        -H "Notion-Version: 2022-06-28" \\')
            print('        https://api.notion.com/v1/users')

async def main():
    """Main validation routine"""
    print("🚀 Notion Token Validator")
    print("Validates Notion API tokens and provides troubleshooting guidance")
    print("=" * 60)

    validator = NotionTokenValidator()

    # Step 1: Analyze token format
    format_valid = validator.analyze_token_format()

    # Step 2: Test token validity
    if format_valid:
        token_valid = await validator.test_token_validity()
    else:
        print("\n⚠️  Skipping validity test due to format issues")
        token_valid = False

    # Step 3: Show integration info
    validator.get_integration_info()

    # Step 4: Provide troubleshooting if needed
    if not format_valid or not token_valid:
        validator.provide_troubleshooting_steps()
    else:
        print("\n🎉 Token is valid and working correctly!")
        print("You can proceed with your integration tests.")

    print("\n" + "=" * 60)
    print("For more help, visit: https://developers.notion.com/docs/getting-started")

if __name__ == "__main__":
    asyncio.run(main())
