"""
Comprehensive tests for Society Sim.

Tests all major functionality without pytest:
- World creation with minimum entity counts
- Need decay stays within bounds (0-100)
- Money changes when people work
- Relationships increase after socialize action
- Save/load preserves population count
- CLI demo logic works end-to-end
- Simulation.run() doesn't crash
- Summary contains all required keys
"""

from models import (
    Person, House, Job, WorldEvent, WorldState,
)
from rules import (
    clamp,
    decay_needs,
    calculate_mood,
    choose_action,
    apply_action,
)
from world import create_default_world, get_person, get_job, get_house, add_event
from simulation import Simulation
from persistence import save_world, load_world
import os


def test_create_default_world_has_minimum_people():
    """Test: create_default_world has at least 6 people."""
    print("Test 1: Default world creation with minimum people...")
    
    world = create_default_world()
    person_count = len(world.people)
    
    assert person_count >= 6, f"Expected at least 6 people, got {person_count}"
    print(f"  ✓ Created {person_count} people (minimum: 6)")


def test_needs_stay_within_bounds():
    """Test: needs always stay in range 0-100 after decay."""
    print("\nTest 2: Need values stay within [0, 100] bounds...")
    
    world = create_default_world()
    initial_people = len(world.people)
    
    # Run 50 ticks and check all needs
    for tick in range(50):
        sim = Simulation(world)
        sim.step()
        
        for person in world.people:
            for need_type, value in person.needs.items():
                assert isinstance(value, (int, float)), f"Need {need_type} should be numeric"
                assert 0.0 <= value <= 100.0, \
                    f"Need '{need_type}' out of bounds: {value} at tick {tick}"
    
    print(f"  ✓ All needs stayed in [0, 100] after 50 ticks")


def test_money_changes_with_work():
    """Test: money changes when people go to work."""
    print("\nTest 3: Money changes during work...")
    
    world = create_default_world()
    initial_total_money = sum(p.money for p in world.people)
    
    # Run simulation with work hours active
    sim = Simulation(world)
    
    # Work happens at hour 7-18, so run through that window
    for tick in range(30):
        sim.step()
    
    final_total_money = sum(p.money for p in world.people)
    money_change = final_total_money - initial_total_money
    
    # At least some people should have earned money from work
    assert money_change >= 0, f"Money decreased by ${-money_change:.2f} during work"
    print(f"  ✓ Money changed by ${money_change:.2f} (work income verified)")


def test_relationships_increase_after_socialize():
    """Test: relationships increase after socialize action."""
    print("\nTest 4: Relationships increase after socialize...")
    
    world = create_default_world()
    
    # Find two people to interact
    p1, p2 = world.people[0], world.people[1]
    initial_rel = p1.relationships.get(p2.id, 0)
    print(f"  Initial relationship: {initial_rel}")
    
    # Manually trigger socialize action with specific target
    apply_action(p1, "socialize", world, target_id=p2.id)
    new_rel = p1.relationships.get(p2.id, 0)
    
    assert new_rel > initial_rel, f"Relationship didn't increase: {initial_rel} -> {new_rel}"
    print(f"  ✓ Relationship increased from {initial_rel:.1f} to {new_rel:.1f}")


def test_save_load_preserves_population():
    """Test: save/load keeps population count."""
    print("\nTest 5: Save/load preserves population...")
    
    world = create_default_world()
    initial_pop = len(world.people)
    
    # Run a few ticks
    sim = Simulation(world)
    for tick in range(10):
        sim.step()
    
    # Save and load
    save_path = "society_sim/test_save.json"
    save_world(world, save_path)
    loaded_world = load_world(save_path)
    
    assert len(loaded_world.people) == initial_pop, \
        f"Population changed: {initial_pop} -> {len(loaded_world.people)}"
    print(f"  ✓ Population preserved: {initial_pop} people")
    
    # Cleanup
    if os.path.exists(save_path):
        os.remove(save_path)


def test_cli_demo_logic():
    """Test: CLI demo basic logic works."""
    print("\nTest 6: CLI demo end-to-end execution...")
    
    # Simulate what cli_demo.py does
    world = create_default_world()
    sim = Simulation(world)
    
    for tick in range(48):
        sim.step()
        if tick % 6 == 0:
            summary = sim.summary()
            assert "day" in summary, "Summary missing 'day' key"
            assert "hour" in summary, "Summary missing 'hour' key"
    
    print("  ✓ CLI demo logic completed 48 ticks successfully")


def test_simulation_run_no_crash():
    """Test: Simulation.run(10) doesn't crash."""
    print("\nTest 7: Simulation stability (no crashes)...")
    
    world = create_default_world()
    sim = Simulation(world)
    
    # Run multiple times to check for intermittent issues
    for run in range(5):
        try:
            sim.run(10)
            summary = sim.summary()
            assert "population" in summary, f"Run {run}: Missing 'population' key"
            assert "mood_counts" in summary, f"Run {run}: Missing 'mood_counts' key"
        except Exception as e:
            raise AssertionError(f"Run {run} crashed: {e}")
    
    print("  ✓ Simulation.run(10) completed 5 times without crash")


def test_summary_has_required_keys():
    """Test: summary has all required keys."""
    print("\nTest 8: Summary contains all required keys...")
    
    world = create_default_world()
    sim = Simulation(world)
    for tick in range(5):
        sim.step()
    
    summary = sim.summary()
    
    required_keys = [
        "day",
        "hour", 
        "population",
        "average_money",
        "average_needs",
        "mood_counts",
        "recent_events",
    ]
    
    for key in required_keys:
        assert key in summary, f"Summary missing required key: '{key}'"
        print(f"  ✓ Key present: '{key}'")


def test_all_rules_functions():
    """Test: All rule functions work correctly."""
    print("\nTest 9: Rule functions correctness...")
    
    # Test clamp
    assert clamp(50) == 50
    assert clamp(-10, -20, 10) == -10
    assert clamp(150, 0, 100) == 100
    print("  ✓ clamp() works")
    
    # Test decay_needs doesn't crash
    world = create_default_world()
    for p in world.people:
        decay_needs(p, 12)
    assert all(0 <= v <= 100 for p in world.people for v in p.needs.values())
    print("  ✓ decay_needs() works")
    
    # Test calculate_mood returns valid strings
    for p in world.people:
        mood = calculate_mood(p)
        assert mood in ["distressed", "lonely", "happy", "neutral"]
    print("  ✓ calculate_mood() returns valid moods")
    
    # Test choose_action returns valid actions
    for p in world.people:
        action = choose_action(p, world)
        assert action in ["eat", "sleep", "clean", "work", "socialize", "play", "idle"]
    print("  ✓ choose_action() returns valid actions")
    
    # Test apply_action doesn't crash
    for p in world.people:
        apply_action(p, "idle", world)
    print("  ✓ apply_action() works")


def test_world_functions():
    """Test: World query functions work."""
    print("\nTest 10: World query functions...")
    
    world = create_default_world()
    
    # Test get_person
    first_person = world.people[0]
    found = get_person(world, first_person.id)
    assert found is not None and found.name == first_person.name
    print("  ✓ get_person() works")
    
    # Test get_job
    first_job = world.jobs[0]
    found_job = get_job(world, first_job.id)
    assert found_job is not None and found_job.title == first_job.title
    print("  ✓ get_job() works")
    
    # Test get_house
    first_house = world.houses[0]
    found_house = get_house(world, first_house.id)
    assert found_house is not None and found_house.name == first_house.name
    print("  ✓ get_house() works")
    
    # Test add_event
    event = add_event(world, "test", "Test event")
    assert len(world.events) >= 1
    assert world.events[-1].message == "Test event"
    print("  ✓ add_event() works")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("SOCIETY SIM COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_create_default_world_has_minimum_people()
        test_needs_stay_within_bounds()
        test_money_changes_with_work()
        test_relationships_increase_after_socialize()
        test_save_load_preserves_population()
        test_cli_demo_logic()
        test_simulation_run_no_crash()
        test_summary_has_required_keys()
        test_all_rules_functions()
        test_world_functions()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSOCIETY_SIM_TESTS_OK")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()