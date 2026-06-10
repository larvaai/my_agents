"""Data models for Society Sim."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict

# ============ PERSON MODEL ============

@dataclass
class Person:
    """A person in the simulation with needs, traits, and relationships."""
    id: str
    name: str
    age: int
    money: float
    traits: List[str] = field(default_factory=list)
    skills: Dict[str, float] = field(default_factory=dict)
    # Needs: 0.0 to 100.0 range
    needs: Dict[str, float] = field(default_factory=lambda: {
        'hunger': 50.0,
        'energy': 80.0,
        'social': 50.0,
        'fun': 40.0,
        'hygiene': 60.0
    })
    mood: str = 'neutral'
    home_id: Optional[str] = None
    job_id: Optional[str] = None
    relationships: Dict[str, float] = field(default_factory=dict)
    current_action: str = 'idle'

# ============ HOUSE MODEL ============

@dataclass
class House:
    """A house with capacity and comfort level."""
    id: str
    name: str
    capacity: int
    comfort: float  # 0.0 to 100.0, affects residents' needs
    residents: List[str] = field(default_factory=list)

# ============ JOB MODEL ============

@dataclass
class Job:
    """A job with salary and skill requirements."""
    id: str
    title: str
    salary_per_day: float
    required_skill: Optional[str] = None  # If set, person needs this skill
    start_hour: int
    end_hour: int

# ============ WORLD EVENT MODEL ============

@dataclass
class WorldEvent:
    """An event that happens in the world."""
    tick: int
    type: str  # 'daily', 'special', etc.
    message: str
    actor_id: Optional[str] = None
    target_id: Optional[str] = None

# ============ WORLD STATE MODEL ============

@dataclass
class WorldState:
    """The complete state of the simulation world."""
    tick: int = 0
    hour: int = 6  # Start at 6 AM
    day: int = 1
    people: List[Person] = field(default_factory=list)
    houses: List[House] = field(default_factory=list)
    jobs: List[Job] = field(default_factory=list)
    events: List[WorldEvent] = field(default_factory=list)
