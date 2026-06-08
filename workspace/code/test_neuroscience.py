#!/usr/bin/env python
"""Test script for neuroscience_system.py"""
import sys
sys.path.insert(0, '..')
from neuroscience_system import BrainSystem

def test_basic_execution():
    """Test that the brain system runs without errors."""
    print("\n=== Test 1: Basic Execution ===")
    try:
        brain = BrainSystem()
        result = brain.run("A snake is approaching!")
        assert isinstance(result, str)
        print(f"✓ Result type OK: {type(result)}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_neutral_scenario():
    """Test neutral scenario."""
    print("\n=== Test 2: Neutral Scenario ===")
    try:
        brain = BrainSystem()
        result = brain.run("A sunny day.")
        assert isinstance(result, str)
        print(f"✓ Result type OK: {type(result)}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_output_content():
    """Test that output contains expected keywords."""
    print("\n=== Test 3: Output Content ===")
    try:
        brain = BrainSystem()
        result1 = brain.run("A snake is approaching!")
        result2 = brain.run("A sunny day.")
        
        # Check for expected patterns
        assert "flee" in result1.lower() or "explore" in result1.lower()
        print(f"✓ Output contains expected decision")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    results = []
    
    results.append(test_basic_execution())
    results.append(test_neutral_scenario())
    results.append(test_output_content())
    
    print("\n=== Summary ===")
    if all(results):
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed.")
        sys.exit(1)