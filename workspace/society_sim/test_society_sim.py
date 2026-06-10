#!/usr/bin/env python
"""Test suite for society_sim."""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from world import create_default_world, get_person, get_job, get_house, add_event
from simulation import Simulation
from persistence import save_world, load_world
from rules import clamp, decay_needs, calculate_mood, choose_action, apply_action


def test_create_default_world():
    """Test: create_default_world has at least 6 people."""
    world = create_default_world()
    assert len(world['people']) >= 6, f"Expected >= 6 people, got {len(world['people'])}"
    print("OK test_create_default_world: population check passed")


def test_needs_in_range():
    """Test: needs stay in 0..100 after 50 ticks."""
    world = create_default_world()
    sim = Simulation(world)
    
    for t in range(50):
        sim.step()
    
    for person in world['people']:
        for need_name, value in person['needs'].items():
            assert 0.0 <= value <= 100.0, f"Need {need_name} out of range: {value}"
    print("OK test_needs_in_range: all needs within [0,100] after 50 ticks")


def test_money_changes():
    """Test: money changes when people work."""
    world = create_default_world()
    
    # Find a working person
    worker = None
    for p in world['people']:
        if p.get('job_id'):
            worker = p
            break
    
    initial_money = worker['money']
    sim = Simulation(world)
    
    # Run some ticks where work can happen (hours 6-18)
    for t in range(20):
        sim.step()
    
    final_money = worker['money']
    assert abs(final_money - initial_money) > 1.0, "Money should have changed after working"
    print("OK test_money_changes: money flow verified")


def test_relationships_increase():
    """Test: relationships increase after socialize."""
    world = create_default_world()
    
    # Find two people to interact
    p1, p2 = None, None
    for i in range(len(world['people'])):
        for j in range(i+1, len(world['people'])):
            p1 = world['people'][i]
            p2 = world['people'][j]
            break
        if p1 and p2:
            break
    
    initial_rel_p1_to_p2 = p1['relationships'].get(p2['id'], 0)
    sim = Simulation(world)
    
    # Run ticks to trigger socialize
    for t in range(30):
        sim.step()
    
    final_rel_p1_to_p2 = p1['relationships'].get(p2['id'], 0)
    assert final_rel_p1_to_p2 > initial_rel_p1_to_p2, "Relationships should increase after socializing"
    print("OK test_relationships_increase: relationships grew correctly")


def test_save_load():
    """Test: save/load preserves population."""
    world = create_default_world()
    
    # Run some ticks
    sim = Simulation(world)
    for t in range(10):
        sim.step()
    
    initial_pop = len(world['people'])
    
    # Save and load
    save_world(world, 'test_savegame.json')
    loaded = load_world('test_savegame.json')
    
    assert len(loaded['people']) == initial_pop, f"Population mismatch: {initial_pop} vs {len(loaded['people'])}"
    print("OK test_save_load: population preserved")


def test_cli_demo_logic():
    """Test: cli_demo basic logic runs without crash."""
    import subprocess
    result = subprocess.run(
        [sys.executable, 'cli_demo.py'],
        cwd=str(Path(__file__).parent),
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"CLI demo crashed: {result.stderr}"
    print("OK test_cli_demo_logic: CLI runs without crash")


def test_simulation_run():
    """Test: Simulation.run(10) doesn't crash."""
    world = create_default_world()
    sim = Simulation(world)
    
    try:
        for t in range(10):
            sim.step()
        print("OK test_simulation_run: 10 ticks completed")
    except Exception as e:
        raise AssertionError(f"Simulation crashed after {t} ticks: {e}")


def test_summary_keys():
    """Test: summary has all required keys."""
    world = create_default_world()
    sim = Simulation(world)
    
    for t in range(5):
        sim.step()
    
    s = sim.summary()
    required_keys = ['day', 'hour', 'population', 'average_money', 'average_needs', 'mood_counts', 'recent_events']
    for key in required_keys:
        assert key in s, f"Missing key: {key}"
    print("OK test_summary_keys: all required keys present")


def main():
    """Run all tests."""
    print("=== SOCIETY SIM TESTS ===\n")
    
    try:
        test_create_default_world()
        test_needs_in_range()
        test_money_changes()
        test_relationships_increase()
        test_save_load()
        test_cli_demo_logic()
        test_simulation_run()
        test_summary_keys()
        
        print("\n=== ALL TESTS PASSED ===")
        print("SOCIETY_SIM_TESTS_OK")
    except AssertionError as e:
        print(f"\n=== TEST FAILED: {e} ===")
        raise


if __name__ == '__main__':
    main()
