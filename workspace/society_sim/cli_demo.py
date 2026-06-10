"""CLI demo for Society Sim."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from world import create_default_world
from simulation import Simulation
from persistence import save_world, load_world

def main():
    print("=== SOCIETY SIM DEMO ===")
    print(f"Starting with {len(create_default_world().people)} people...")

    # Create default world
    world = create_default_world()
    sim = Simulation(world)

    # Run 48 ticks, printing summary every 6 ticks
    for tick in range(1, 50):
        sim.step()
        if tick % 6 == 0:
            s = sim.summary()
            print(f"\n--- Tick {tick} (Day {s['day']}, Hour {s['hour']}) ---")
            print(f"Population: {s['population']}")
            print(f"Avg Money: ${s['average_money']:.1f}")
            print(f"Moods: {s['mood_counts']}")

    # Save game state
    save_path = BASE_DIR / 'savegame.json'
    save_world(world, save_path)
    print(f"\n=== Saved to {save_path.name} ===")

    # Load and verify
    loaded_world = load_world(save_path)
    print(f"Loaded world with {len(loaded_world.people)} people")
    s2 = Simulation(loaded_world).summary()
    print(f"Loaded summary - Day: {s2['day']}, Pop: {s2['population']}")

    print("\n=== DEMO COMPLETE ===")

if __name__ == '__main__':
    main()
