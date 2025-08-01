#!/usr/bin/env python3
"""
Test runner script for Lambda.hu backend tests.

This script provides various options for running tests,
including unit tests, integration tests, and coverage reports.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list, description: str) -> int:
    """Run a command and return its exit code."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
    else:
        print(f"❌ {description} - FAILED")
    
    return result.returncode


def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        print("""
🧪 Lambda.hu Backend Test Runner

Usage:
    python run_tests.py <command>

Commands:
    unit          - Run unit tests only
    integration   - Run integration tests only
    all           - Run all tests
    coverage      - Run tests with coverage report
    fast          - Run tests excluding slow tests
    pdf           - Run only PDF processing tests
    api           - Run only API endpoint tests
    
Examples:
    python run_tests.py unit
    python run_tests.py coverage
    python run_tests.py fast
        """)
        return 1

    command = sys.argv[1].lower()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest", "-v"]
    
    if command == "unit":
        cmd = base_cmd + ["tests/unit/"]
        return run_command(cmd, "Unit Tests")
    
    elif command == "integration":
        cmd = base_cmd + ["tests/integration/"]
        return run_command(cmd, "Integration Tests")
    
    elif command == "all":
        cmd = base_cmd + ["tests/"]
        return run_command(cmd, "All Tests")
    
    elif command == "coverage":
        cmd = base_cmd + [
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "tests/"
        ]
        return run_command(cmd, "Tests with Coverage")
    
    elif command == "fast":
        cmd = base_cmd + ["-m", "not slow", "tests/"]
        return run_command(cmd, "Fast Tests (excluding slow)")
    
    elif command == "pdf":
        cmd = base_cmd + ["-k", "pdf", "tests/"]
        return run_command(cmd, "PDF Processing Tests")
    
    elif command == "api":
        cmd = base_cmd + ["-k", "api or endpoint", "tests/"]
        return run_command(cmd, "API Endpoint Tests")
    
    elif command == "lint":
        print("\n🔍 Running Code Quality Checks")
        
        commands = [
            (["python", "-m", "ruff", "check", "."], "Ruff Linting"),
            (["python", "-m", "black", "--check", "."], "Black Formatting Check"),
            (["python", "-m", "isort", "--check-only", "."], "Import Sorting Check"),
            (["python", "-m", "mypy", "."], "Type Checking"),
        ]
        
        total_errors = 0
        for cmd, desc in commands:
            result = run_command(cmd, desc)
            total_errors += result
        
        return min(total_errors, 1)  # Return 0 or 1
    
    elif command == "fix":
        print("\n🔧 Fixing Code Quality Issues")
        
        commands = [
            (["python", "-m", "ruff", "check", "--fix", "."], "Auto-fix Ruff Issues"),
            (["python", "-m", "black", "."], "Format with Black"),
            (["python", "-m", "isort", "."], "Sort Imports"),
        ]
        
        total_errors = 0
        for cmd, desc in commands:
            result = run_command(cmd, desc)
            total_errors += result
        
        return min(total_errors, 1)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python run_tests.py' to see available commands.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)