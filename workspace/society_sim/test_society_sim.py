"""Tests for Society Sim."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from world import create_default_world
from models import Person, House, Job, WorldState, WorldEvent
from simulation import Simulation
from persistence import save_world, load_world
from rules import decay_needs, choose_action, apply_action, calculate_mood

# Test 1: Create default world has at least 6 people
def test_create_default_world():
    world = create_default_world()
    assert len(world.people) >= 6, f"Expected >= 6 people, got {len(world.people)}"
    print("PASS: World has", len(world.people), "people")

# Test 2: Needs stay in 0..100 after 50 ticks
def test_needs_bounds():
    world = create_default_world()
    sim = Simulation(world)
    for tick in range(50):
        sim.step()
        for p in world.people:
            for need, val in p.needs.items():
                assert 0.0 <= val <= 100.0, f"Need {need} out of bounds: {val}"
    print("PASS: All needs within [0, 100] after 50 ticks")

# Test 3: Money changes when people work
def test_money_changes():
    world = create_default_world()
    initial_total = sum(p.money for p in world.people)
    sim = Simulation(world)
    # Run some ticks with potential work
    for tick in range(20):
        sim.step()
    final_total = sum(p.money for p in world.people)
    # At least one person should have worked and earned money
    assert final_total != initial_total, "Money didn't change - check job assignment"
    print("PASS: Money changed after work ticks")

# Test 4: Relationships increase after socialize
def test_relationships_increase():
    world = create_default_world()
    # Find two people in same house who can socialize
    candidates = [(p1, p2) for p1 in world.people for p2 in world.people if p1.id != p2.id and p1.home_id == p2.home_id]
    assert len(candidates) > 0, "No pairs found to socialize"
    p1, p2 = candidates[0]
    initial_rel = p1.relationships.get(p2.id, 0)
    sim = Simulation(world)
    # Run enough ticks to ensure at least one socialize action occurs
    for tick in range(20):
        sim.step()
    new_rel = p1.relationships.get(p2.id, 0)
    assert new_rel > initial_rel, f"Relationship didn't increase: {initial_rel} -> {new_rel}"
    print("PASS: Relationships increased after socialize")

# Test 5: Save/load preserves population
def test_save_load():
    world = create_default_world()
    sim = Simulation(world)
    for tick in range(10):
        sim.step()
    initial_pop = len(world.people)
    save_path = BASE_DIR / 'test_save.json'
    save_world(world, save_path)
    loaded = load_world(save_path)
    assert len(loaded.people) == initial_pop, f"Population changed: {initial_pop} -> {len(loaded.people)}"
    print("PASS: Save/load preserves population")

# Test 6: CLI demo logic works (basic integration test)
def test_cli_demo_logic():
    # Simulate what cli_demo.py does
    world = create_default_world()
    sim = Simulation(world)
    for tick in range(48):
        sim.step()
        if tick % 6 == 0:
            s = sim.summary()
            assert 'day' in s and 'hour' in s, "Summary missing required keys"
    print("PASS: CLI demo logic runs without crash")

# Test 7: Simulation.run(10) doesn't crash
def test_simulation_run():
    world = create_default_world()
    sim = Simulation(world)
    events = sim.run(10)
    assert len(events) >= 0, "Run should complete"
    print("PASS: Simulation.run(10) completed")

# Test 8: Summary has all required keys
def test_summary_keys():
    world = create_default_world()
    sim = Simulation(world)
    for tick in range(5):
        sim.step()
    s = sim.summary()
    required_keys = ['day', 'hour', 'population', 'average_money', 'average_needs', 'mood_counts', 'recent_events']
    for key in required_keys:
        assert key in s, f"Missing key: {key}"
    print("PASS: Summary has all required keys")

# Run all tests
if __name__ == '__main__':
    print("=== SOCIETY SIM TESTS ===\n")
    test_create_default_world()
    test_needs_bounds()
    test_money_changes()
    test_relationships_increase()
    test_save_load()
    test_cli_demo_logic()
    test_simulation_run()
    test_summary_keys()

    print("\n=== ALL TESTS PASSED ===")
    print("SOCIETY_SIM_TESTS_OK")
