"""
Data models for Society Sim.

Defines all dataclasses used throughout the simulation engine:
- Person: Individual character with needs, traits, skills, relationships
- House: Residential building with capacity and comfort level
- Job: Employment opportunity with salary and skill requirements
- WorldEvent: Events that occur during simulation ticks
- WorldState: Complete snapshot of the world at any point in time
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


def generate_id() -> str:
    """Generate a unique ID for entities."""
    return f"{uuid.uuid4().hex[:8]}"


@dataclass
class Person:
    """An individual person in the simulation.
    
    Attributes:
        id: Unique identifier
        name: Display name
        age: Current age (years)
        money: Current currency amount
        traits: List of personality/behavioral traits
        skills: Dictionary mapping skill names to proficiency levels (0-100)
        needs: Dictionary of current need levels (hunger, energy, social, fun, hygiene)
        mood: Current emotional state string
        home_id: Reference to their residence house
        job_id: Reference to their employment
        relationships: Dict mapping other person IDs to relationship scores (0-100)
        current_action: What they're currently doing
    """
    id: str = field(default_factory=generate_id)
    name: str = "Person"
    age: int = 25
    money: float = 0.0
    traits: list[str] = field(default_factory=list)
    skills: dict[str, float] = field(default_factory=dict)
    needs: dict[str, float] = field(
        default_factory=lambda: {
            "hunger": 50.0,
            "energy": 100.0,
            "social": 50.0,
            "fun": 50.0,
            "hygiene": 80.0,
        }
    )
    mood: str = "neutral"
    home_id: Optional[str] = None
    job_id: Optional[str] = None
    relationships: dict[str, float] = field(default_factory=dict)
    current_action: str = "idle"


@dataclass
class House:
    """A residential building in the simulation.
    
    Attributes:
        id: Unique identifier
        name: Display name
        capacity: Maximum number of residents allowed
        comfort: Current comfort level (0-100)
        residents: List of person IDs currently living here
    """
    id: str = field(default_factory=generate_id)
    name: str = "House"
    capacity: int = 4
    comfort: float = 75.0
    residents: list[str] = field(default_factory=list)


@dataclass
class Job:
    """An employment opportunity in the simulation.
    
    Attributes:
        id: Unique identifier
        title: Job title/name
        salary_per_day: Daily earnings (currency units)
        required_skill: Skill name needed to qualify for this job
        start_hour: Work shift start time (0-23)
        end_hour: Work shift end time (0-23)
    """
    id: str = field(default_factory=generate_id)
    title: str = "Job"
    salary_per_day: float = 100.0
    required_skill: Optional[str] = None
    start_hour: int = 8
    end_hour: int = 17


@dataclass
class WorldEvent:
    """An event that occurs during the simulation.
    
    Attributes:
        tick: The simulation tick when this occurred
        type: Event category (social, work, daily, random, etc.)
        message: Human-readable description of what happened
        actor_id: Optional ID of who caused/acted in the event
        target_id: Optional ID of who was affected by the event
    """
    tick: int = 0
    type: str = "unknown"
    message: str = "Unknown event"
    actor_id: Optional[str] = None
    target_id: Optional[str] = None


@dataclass
class WorldState:
    """Complete snapshot of the world at any point in time.
    
    Attributes:
        tick: Current simulation tick counter
        hour: Current hour (0-23)
        day: Current day number
        people: List of Person objects
        houses: List of House objects
        jobs: List of Job objects
        events: List of WorldEvent objects (recent history)
    """
    tick: int = 0
    hour: int = 6
    day: int = 1
    people: list[Person] = field(default_factory=list)
    houses: list[House] = field(default_factory=list)
    jobs: list[Job] = field(default_factory=list)
    events: list[WorldEvent] = field(default_factory=list)
