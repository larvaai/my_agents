# Society Sim - Core Data Models

# All needs must stay in range 0.0 to 100.0
NEEDS = ['hunger', 'energy', 'social', 'fun', 'hygiene']

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import uuid

@dataclass
class Person:
    id: str = field(default_factory=lambda: f'p_{uuid.uuid4().hex[:8]}')
    name: str
    age: int
    money: float = 0.0
    traits: List[str] = field(default_factory=list)
    skills: Dict[str, float] = field(default_factory=dict)
    needs: Dict[str, float] = field(default_factory=dict)
    mood: str = 'neutral'
    home_id: Optional[str] = None
    job_id: Optional[str] = None
    relationships: Dict[str, float] = field(default_factory=dict)
    current_action: str = 'idle'

@dataclass
class House:
    id: str = field(default_factory=lambda: f'h_{uuid.uuid4().hex[:8]}')
    name: str
    capacity: int
    comfort: float = 50.0
    residents: List[str] = field(default_factory=list)

@dataclass
class Job:
    id: str = field(default_factory=lambda: f'j_{uuid.uuid4().hex[:8]}')
    title: str
    salary_per_day: float
    required_skill: Optional[str] = None
    start_hour: int = 9
    end_hour: int = 17

@dataclass
class WorldEvent:
    tick: int
    type: str
    message: str
    actor_id: Optional[str] = None
    target_id: Optional[str] = None

@dataclass
class WorldState:
    tick: int = 0
    hour: int = 6
    day: int = 1
    people: List[Person] = field(default_factory=list)
    houses: List[House] = field(default_factory=list)
    jobs: List[Job] = field(default_factory=list)
    events: List[WorldEvent] = field(default_factory=list)
