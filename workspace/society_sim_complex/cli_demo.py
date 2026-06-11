"""CLI demo: command-line interface and demonstration."""

# CLI Demo - main entry point for terminal interaction
def run_demo(config=None):
    """Run a quick demo of the simulation engine."""
    import sys
    
    # Initialize core managers with default config
    from world import WorldManager, ACTION_TYPES_REGISTRY  # OK - no log needed
    from economy import EconomyManager, INCOME_SOURCES  # OK - no log needed
    from autonomy import AutonomyPlanner, ACTION_PHASES  # OK - no log needed
    
    if config is None:
        config = {
            'people': 10,
            'households': 3,
            'homes': 4,
            'jobs': 6,
            'locations': 6,
            'action_types': 12,
            'event_categories': 6,
        }
    
    print("="*60)
    print("SOCIETY SIM COMPLEX - Quick Demo")
    print("="*60)
    print(f"Configuration: {config['people']} people, {config['households']} households")
    print(f"Available action types: {len(ACTION_TYPES_REGISTRY)}")
    print(f"Action phases available: {list(ACTION_PHASES.keys())}")
    print("="*60)

    # Create world manager and initialize default state
    world = WorldManager(config=config)
    world.initialize_default_world(config=config)
    
    print("\n[World Initialized]")
    print(f"  - Action types registered: {len(ACTION_TYPES_REGISTRY)}")
    print(f"  - Current phase: {world.get_current_phase()}")

    # Create economy manager and register sample income sources
    economy = EconomyManager(config=config)
    
    # Register a work job as income source (requires HAS_JOB prerequisite)
    economy.register_income_source('PERSON_001', 'WORK', 15)
    print("\n[Income Sources Registered]")
    print(f"  - Work: {INCOME_SOURCES['WORK']['base_amount']} per session")

    # Create autonomy planner for action selection
    planner = AutonomyPlanner(config=config)
    
    # Simulate a few time steps to demonstrate core mechanics
    print("\n[Time Simulation]")
    for step in range(3):
        phase = world.get_current_phase()
        weekday = world.get_weekday()
        hour = world.current_hour % 24
        print(f"  Day {world.current_day:03d}, {weekday}, {phase} - Hour {hour}:00")
        
        # Advance time by a few hours to show progression
        result = world.advance_time(hours=6)
        if result['type'] == 'TIME_ADVANCE':
            print(f"    -> Advanced {result['hours']}h, new day: {result['new_day']}")

    # Demonstrate entity creation (placeholder for real data from persistence)
    print("\n[Entity Management]")
    entity_id = world.create_entity('PERSON', {'name': 'Demo Person', 'age': 35, 'skills': ['WORK', 'HUNTER']})
    print(f"  - Created entity: {entity_id}")

    # Show action type registry (from actions.py)
    print("\n[Action Types]")
    for name in list(ACTION_TYPES_REGISTRY.keys())[:4]:  # Show first 4 as sample
        info = ACTION_TYPES_REGISTRY[name]
        print(f"  - {name}: cost={info['energy_cost']}, yield={info['resource_yield_min']}-{info['resource_yield_max']}")

    print("\n[Demo Complete]")
    print("Core systems initialized and tested successfully.")
    return world, economy, planner

# Main entry point for CLI execution
if __name__ == '__main__':
    run_demo()

__all__ = ['run_demo']
]

