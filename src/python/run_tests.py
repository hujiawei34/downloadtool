#!/usr/bin/env python3
"""
Test runner for downloadtool project.
Run all tests and generate a coverage report.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run all tests with pytest."""
    print("🚀 Running downloadtool tests...")
    
    # Change to the python directory
    os.chdir(Path(__file__).parent)
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Please install testing dependencies:")
        print("pip install -r requirements.txt")
        return False

def run_specific_test(test_file):
    """Run a specific test file."""
    print(f"🚀 Running tests in {test_file}...")
    
    os.chdir(Path(__file__).parent)
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/{test_file}",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ Tests in {test_file} passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests in {test_file} failed with exit code: {e.returncode}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        if not test_file.startswith("test_"):
            test_file = f"test_{test_file}"
        if not test_file.endswith(".py"):
            test_file = f"{test_file}.py"
        
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)