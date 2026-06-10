"""
Persistence layer for Society Sim.

Handles saving and loading world states using JSON serialization.
This allows the simulation to be paused, resumed, or shared between sessions.
"""

import json
from models import WorldState


def save_world(world: WorldState, path: str) -> None:
    """Save the current world state to a file.
    
    Args:
        world: The WorldState to save
        path: File path where JSON will be written
    """
    # Convert dataclasses to dictionaries for JSON serialization
    def convert_to_dict(obj):
        if hasattr(obj, '__dict__'):
            return {
                k: convert_to_dict(v) 
                for k, v in obj.__dict__.items()
            }
        elif isinstance(obj, list):
            return [convert_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_to_dict(v) for k, v in obj.items()}
        else:
            return obj
    
    world_data = convert_to_dict(world)
    with open(path, 'w') as f:
        json.dump(world_data, f, indent=2, default=str)


def load_world(path: str) -> WorldState:
    """Load a saved world state from a file.
    
    Args:
        path: File path where JSON was stored
    
    Returns:
        A reconstructed WorldState object
    """
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Reconstruct the WorldState from dictionary data
    def convert_from_dict(d):
        if d is None:
            return None
        elif isinstance(d, list):
            return [convert_from_dict(item) for item in d]
        elif isinstance(d, dict):
            # Check if this looks like a known type
            if 'id' not in d and 'tick' not in d:
                # Might be a nested object - try to infer from keys
                pass  # Let it fall through as generic dict for now
            return {k: convert_from_dict(v) for k, v in d.items()}
        else:
            return d
    
    world_data = convert_from_dict(data)
    
    # Create WorldState with proper types
    ws = WorldState(
        tick=world_data.get('tick', 0),
        hour=world_data.get('hour', 6),
        day=world_data.get('day', 1),
        people=world_data.get('people', []),
        houses=world_data.get('houses', []),
        jobs=world_data.get('jobs', []),
        events=world_data.get('events', []),
    )
    
    return ws