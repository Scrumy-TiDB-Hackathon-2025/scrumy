import pytest
import asyncio
import json
import os
import datetime
from app.db import DatabaseManager

# Needed for async test support
pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for pytest-asyncio."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def reset_db_state():
    """
    Automatically clear the DB before each test to prevent duplicate Meeting ID errors.
    """
    db = DatabaseManager()
    db.clear_all()  
    yield
    db.clear_all() 

# Global list to collect test results
test_results = []

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to collect per-test results reliably"""
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":  # Only capture the actual test run
        test_results.append({
            "test": item.name,
            "outcome": result.outcome.upper(),   # PASSED / FAILED / SKIPPED
            "nodeid": item.nodeid,
            "time": datetime.datetime.utcnow().isoformat(),
            "duration": getattr(result, "duration", 0),
            "longrepr": str(result.longrepr) if result.failed else None
        })

def pytest_sessionfinish(session, exitstatus):
    """Save results after all tests finish"""
    results_dir = "tests"
    os.makedirs(results_dir, exist_ok=True)
    results_file = os.path.join(results_dir, "test_results.json")

    # Summary
    passed = sum(1 for r in test_results if r["outcome"] == "PASSED")
    failed = sum(1 for r in test_results if r["outcome"] == "FAILED")
    skipped = sum(1 for r in test_results if r["outcome"] == "SKIPPED")

    final_results = {
        "summary": {
            "total": len(test_results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "exit_status": exitstatus,
            "timestamp": datetime.datetime.utcnow().isoformat()
        },
        "tests": test_results
    }

    with open(results_file, "w") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n📊 Test results saved to {results_file}")
    print(f"📈 Summary: {passed} passed, {failed} failed, {skipped} skipped, {len(test_results)} total")

# ---- Run tests ----
# When you run:
# pytest -q
# Your DB will be wiped before each test.
# If you want even more detailed output during the run, you can also use:
# pytest -v -s

# Results will be saved into tests/test_results.json