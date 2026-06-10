#!/usr/bin/env python
"""CLI demo for society_sim."""
import sys
sys.path.insert(0, '.')

from world import create_default_world
from simulation import Simulation
from persistence import save_world, load_world


def main():
    print("=== SOCIETY SIM DEMO ===")
    print()
    
    # Create default world
    world = create_default_world()
    print(f"Created world with {len(world['people'])} people, {len(world['houses'])} houses, {len(world['jobs'])} jobs")
    print()
    
    # Run simulation for 48 ticks
    sim = Simulation(world)
    print("Running 48 ticks...")
    print()
    
    for t in range(0, 48):
        sim.step()
        if t % 6 == 5:  # Print summary every 6 ticks (at end of each group)
            s = sim.summary()
            print(f"--- Tick {t+1}, Day {s['day']}, Hour {s['hour']} ---")
            print(f"Population: {s['population']}")
            print(f"Avg Money: ${s['average_money']:.2f}")
            print(f"Avg Needs: {s['average_needs']:.1f}")
            print(f"Moods: {s['mood_counts']}")
    
    print()
    print("Saving world to savegame.json...")
    save_world(world, 'savegame.json')
    print("Done!")


if __name__ == '__main__':
    main()