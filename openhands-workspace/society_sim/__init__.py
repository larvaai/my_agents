"""
Society Sim - A terminal-based life simulation game engine.

A mini-project simulating a small society with:
- Multiple characters (Person)
- Physical needs (hunger, energy, social, fun, hygiene)
- Emotions and mood states
- Social relationships
- Jobs and income
- Housing system
- Day/night cycle tracking
- Automatic actions based on needs
- Random world events
- Save/load state persistence
"""

from models import Person, House, Job, WorldEvent, WorldState
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

__version__ = "1.0.0"
__all__ = [
    # Models
    "Person",
    "House",
    "Job",
    "WorldEvent",
    "WorldState",
    # Rules
    "clamp",
    "decay_needs",
    "calculate_mood",
    "choose_action",
    "apply_action",
    # World
    "create_default_world",
    "get_person",
    "get_job",
    "get_house",
    "add_event",
    # Simulation
    "Simulation",
    # Persistence
    "save_world",
    "load_world",
]
