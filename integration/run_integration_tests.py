#!/usr/bin/env python3
"""
Integration Test Runner for ScrumBot
Runs integration tests for ClickUp and Notion APIs with real credentials
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    env_file = Path(__file__).parent.parent / ".env.integration"

    if not env_file.exists():
        logger.error(f"❌ Environment file not found: {env_file}")
        logger.info("💡 Please copy .env.integration.template to .env.integration and fill in real values")
        return False

    load_dotenv(env_file)

    # Check for required variables
    required_vars = []
    optional_vars = []

    # Check if we're in mock mode
    use_mock = os.getenv("USE_MOCK_INTEGRATIONS", "false").lower() == "true"

    if not use_mock:
        # Real API testing - need credentials
        if not os.getenv("NOTION_TOKEN") and not os.getenv("CLICKUP_TOKEN"):
            logger.error("❌ No API tokens found and not in mock mode")
            logger.info("💡 Either set USE_MOCK_INTEGRATIONS=true or provide real API tokens")
            return False

        if os.getenv("NOTION_TOKEN"):
            if not os.getenv("NOTION_DATABASE_ID"):
                logger.error("❌ NOTION_TOKEN provided but NOTION_DATABASE_ID missing")
                return False
            optional_vars.extend(["NOTION_TOKEN", "NOTION_DATABASE_ID"])

        if os.getenv("CLICKUP_TOKEN"):
            if not os.getenv("CLICKUP_LIST_ID") or not os.getenv("CLICKUP_TEAM_ID"):
                logger.error("❌ CLICKUP_TOKEN provided but CLICKUP_LIST_ID or CLICKUP_TEAM_ID missing")
                return False
            optional_vars.extend(["CLICKUP_TOKEN", "CLICKUP_LIST_ID", "CLICKUP_TEAM_ID"])

    logger.info(f"🔧 Environment check passed")
    logger.info(f"📝 Mock mode: {'enabled' if use_mock else 'disabled'}")

    if not use_mock:
        platforms = []
        if os.getenv("NOTION_TOKEN"):
            platforms.append("Notion")
        if os.getenv("CLICKUP_TOKEN"):
            platforms.append("ClickUp")
        logger.info(f"🔗 Testing platforms: {', '.join(platforms)}")

    return True

def run_pytest(args):
    """Run pytest with specified arguments"""
    cmd = ["python", "-m", "pytest"]

    # Add test directory
    cmd.append("integration/tests/")

    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    if args.very_verbose:
        cmd.append("-vv")

    # Add specific test markers
    if args.notion_only:
        cmd.extend(["-m", "notion"])
    elif args.clickup_only:
        cmd.extend(["-m", "clickup"])
    elif args.integration_only:
        cmd.extend(["-m", "integration"])

    # Add specific test file
    if args.test_file:
        cmd = cmd[:-1] + [f"integration/tests/{args.test_file}"]

    # Add specific test function
    if args.test_function:
        if args.test_file:
            cmd[-1] += f"::{args.test_function}"
        else:
            cmd.extend(["-k", args.test_function])

    # Skip slow tests unless explicitly requested
    if not args.include_slow:
        cmd.extend(["-m", "not slow"])

    # Add other pytest options
    if args.stop_on_failure:
        cmd.append("-x")

    if args.capture == "no":
        cmd.append("-s")

    if args.tb_style:
        cmd.extend(["--tb", args.tb_style])

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])

    logger.info(f"🚀 Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test execution interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        return 1

def install_dependencies():
    """Install required test dependencies"""
    logger.info("📦 Installing test dependencies...")

    deps = [
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.0"
    ]

    cmd = ["pip", "install"] + deps

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Run ScrumBot integration tests for ClickUp and Notion APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integration_tests.py                    # Run all tests
  python run_integration_tests.py --notion-only      # Run only Notion tests
  python run_integration_tests.py --clickup-only     # Run only ClickUp tests
  python run_integration_tests.py --mock             # Run in mock mode
  python run_integration_tests.py --verbose          # Run with verbose output
  python run_integration_tests.py --install-deps     # Install dependencies first

  # Run specific test file
  python run_integration_tests.py --test-file test_notion_integration.py

  # Run specific test function
  python run_integration_tests.py --test-function test_notion_create_basic_task
        """
    )

    # Test selection
    parser.add_argument(
        "--notion-only",
        action="store_true",
        help="Run only Notion integration tests"
    )
    parser.add_argument(
        "--clickup-only",
        action="store_true",
        help="Run only ClickUp integration tests"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only integration tests (skip unit tests)"
    )
    parser.add_argument(
        "--test-file",
        help="Run specific test file (e.g., test_notion_integration.py)"
    )
    parser.add_argument(
        "--test-function",
        help="Run specific test function (e.g., test_notion_create_basic_task)"
    )
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow-running tests"
    )

    # Output options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-vv", "--very-verbose",
        action="store_true",
        help="Very verbose output"
    )
    parser.add_argument(
        "--capture",
        choices=["yes", "no"],
        default="yes",
        help="Capture output (default: yes)"
    )
    parser.add_argument(
        "--tb-style",
        choices=["short", "long", "no"],
        default="short",
        help="Traceback style (default: short)"
    )

    # Execution options
    parser.add_argument(
        "-x", "--stop-on-failure",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report"
    )

    # Environment options
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force mock mode (override environment settings)"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install required dependencies before running tests"
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Only check environment configuration, don't run tests"
    )

    args = parser.parse_args()

    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            return 1

    # Set mock mode if requested
    if args.mock:
        os.environ["USE_MOCK_INTEGRATIONS"] = "true"

    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        logger.info("\n💡 Setup instructions:")
        logger.info("1. Copy .env.integration.template to .env.integration")
        logger.info("2. Fill in real API credentials or set USE_MOCK_INTEGRATIONS=true")
        logger.info("3. Run with --install-deps if needed")
        return 1

    # If only checking environment, exit here
    if args.check_env:
        logger.info("✅ Environment check passed - ready for testing")
        return 0

    # Validate exclusive options
    exclusive_count = sum([args.notion_only, args.clickup_only, args.integration_only])
    if exclusive_count > 1:
        logger.error("❌ Cannot specify multiple exclusive test selection options")
        return 1

    # Change to project root directory
    os.chdir(Path(__file__).parent.parent)

    # Run tests
    logger.info("🧪 Starting integration tests...")

    exit_code = run_pytest(args)

    if exit_code == 0:
        logger.info("🎉 All tests passed!")
    elif exit_code == 130:
        logger.info("⚠️  Tests interrupted")
    else:
        logger.error(f"❌ Tests failed with exit code: {exit_code}")

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
