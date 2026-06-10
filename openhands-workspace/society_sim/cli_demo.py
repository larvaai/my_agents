"""
Command-line demonstration for Society Sim.

When run with:
    python society_sim/cli_demo.py

This will:
- Create a default world
- Run 48 ticks of simulation
- Print summary every 6 ticks
- Save to society_sim/savegame.json
- Load and verify the saved state
"""

from models import WorldState, Person, House, Job, WorldEvent
from rules import clamp
from world import create_default_world, get_person, get_job, get_house, add_event
from simulation import Simulation
from persistence import save_world, load_world
import os


def print_separator():
    """Print a visual separator."""
    print("=" * 60)


def print_header(title: str):
    """Print a section header."""
    print_separator()
    print(f"\n>>> {title}")
    print_separator()


def main():
    # Create default world
    print_header("Creating Default World")
    
    world = create_default_world()
    print(f"Created world with:")
    print(f"  - {len(world.people)} people")
    print(f"  - {len(world.houses)} houses")
    print(f"  - {len(world.jobs)} jobs")
    
    # Show first few people
    for i, p in enumerate(world.people[:3]):
        print(f"\n  Person {i+1}: {p.name} (ID: {p.id})")
        print(f"    Money: ${p.money:.2f}")
        print(f"    Mood: {p.mood}")
        print(f"    Home: {p.home_id if p.home_id else 'None'}")
        print(f"    Job: {p.job_id if p.job_id else 'None'}")
    
    # Run simulation for 48 ticks
    print_header("Running Simulation (48 ticks)")
    print("Showing summary every 6 ticks...\n")
    
    sim = Simulation(world)
    
    for tick in range(1, 49):
        # Run one step
        sim.step()
        
        # Print summary every 6 ticks
        if tick % 6 == 0:
            summary = sim.summary()
            print(f"Tick {tick} | Day {summary['day']} Hour {summary['hour']}")
            print(f"  Population: {summary['population']}")
            print(f"  Avg Money: ${summary['average_money']:.2f}")
            print(f"  Avg Needs - Hunger: {summary['average_needs']['hunger']:.1f}, "
                  f"Energy: {summary['average_needs']['energy']:.1f}, "
                  f"Social: {summary['average_needs']['social']:.1f}")
            print(f"  Moods: {summary['mood_counts']}")
    
    # Final summary
    print_header("Final Simulation Summary")
    final_summary = sim.summary()
    print(f"Day: {final_summary['day']}, Hour: {final_summary['hour']}")
    print(f"Population: {final_summary['population']}")
    print(f"Average Money: ${final_summary['average_money']:.2f}")
    for need, avg in final_summary['average_needs'].items():
        print(f"  Avg {need.capitalize()}: {avg:.1f}")
    print(f"Mood Distribution: {final_summary['mood_counts']}")
    
    # Save world
    save_path = "society_sim/savegame.json"
    save_world(world, save_path)
    print(f"\nWorld saved to: {save_path}")
    
    # Load and verify
    print_header("Loading Saved World")
    loaded_world = load_world(save_path)
    
    print(f"Loaded world has:")
    print(f"  - Tick: {loaded_world.tick} (expected: {world.tick})")
    print(f"  - Day: {loaded_world.day} (expected: {world.day})")
    print(f"  - Hour: {loaded_world.hour} (expected: {world.hour})")
    print(f"  - Population: {len(loaded_world.people)} (expected: {len(world.people)})")
    
    # Verify population match
    if len(loaded_world.people) == len(world.people):
        print("\n✓ Population count matches!")
    else:
        print(f"\n⚠ Population mismatch! Expected {len(world.people)}, got {len(loaded_world.people)}")
    
    # Show a few loaded people
    for i, p in enumerate(loaded_world.people[:3]):
        print(f"\n  Loaded Person {i+1}: {p.name} (ID: {p.id})")
        print(f"    Money: ${p.money:.2f}")
        print(f"    Mood: {p.mood}")
    
    # Create a new simulation from loaded world
    print_header("Running New Simulation from Loaded State")
    sim2 = Simulation(loaded_world)
    
    for tick in range(1, 13):
        sim2.step()
        if tick % 4 == 0:
            summary = sim2.summary()
            print(f"Tick {tick} | Day {summary['day']} Hour {summary['hour']}")
            print(f"  Population: {summary['population']}, Avg Money: ${summary['average_money']:.2f}")
    
    # Final summary from loaded state
    final_summary2 = sim2.summary()
    print_header("Final Summary (from Loaded State)")
    print(f"Day: {final_summary2['day']}, Hour: {final_summary2['hour']}")
    print(f"Population: {final_summary2['population']}")
    print(f"Average Money: ${final_summary2['average_money']:.2f}")
    for need, avg in final_summary2['average_needs'].items():
        print(f"  Avg {need.capitalize()}: {avg:.1f}")
    print(f"Mood Distribution: {final_summary2['mood_counts']}")


if __name__ == "__main__":
    main()