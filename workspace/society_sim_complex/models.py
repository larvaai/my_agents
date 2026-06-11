# Society Sim Complex - Domain Models
# Core entity definitions for the life simulation engine.

from __future__ import annotations
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import random
import uuid

@dataclass
class Location:
    """A physical location in the simulation world."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = 'Unnamed'
    type: str = 'generic'  # home, work, public, etc.
    capacity: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.name:
            self.name = f"{self.type.capitalize()} {random.randint(1, 999)}"

@dataclass
class Job:
    """A job or occupation in the simulation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = 'Generic Job'
    type: str = 'generic'
    salary_range: Tuple[float, float] = (0.0, 100.0)
    requirements: Dict[str, Any] = field(default_factory=dict)
    schedule: Dict[int, bool] = field(default_factory=dict)  # day_of_week -> available
    
    def __post_init__(self):
        if not self.name:
            job_types = ['Factory', 'Office', 'Retail', 'Service', 'Tech', 'Healthcare']
            self.name = f"{random.choice(job_types)} Worker"

@dataclass
class Person:
    """A person/entity in the simulation world."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = 'Person'
    age: int = 25
    gender: Optional[str] = None
    
    # Resources and stats (0-100 scale)
    money: float = 0.0
    food: int = 50
    hygiene: int = 30
    energy: int = 100
    satisfaction: int = 70
    health: int = 80
    
    # Relationships and affiliations
    household_id: Optional[str] = None
    home_id: Optional[str] = None
    job_id: Optional[str] = None
    relationships: Dict[str, 'Relationship'] = field(default_factory=dict)
    event_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.name:
            first_names = ['Alex', 'Jordan', 'Taylor', 'Casey', 'Morgan', 'Riley']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia']
            self.name = f"{random.choice(first_names)} {random.choice(last_names)}"

@dataclass
class Household:
    """A household unit containing people and resources."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = 'Unnamed Household'
    members: List[str] = field(default_factory=list)  # person IDs
    budget: float = 0.0
    shared_resources: Dict[str, Any] = field(default_factory=dict)
    schedule: Dict[int, bool] = field(default_factory=dict)  # day_of_week -> available
    
    def __post_init__(self):
        if not self.name:
            self.name = f"Household {random.randint(1, 99)}"

@dataclass
class Home:
    """A physical home/property in the simulation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = 'Unnamed Home'
    type: str = 'residential'
    address: str = ''
    capacity: int = 0
    current_occupants: List[str] = field(default_factory=list)  # person IDs
    rooms: Dict[str, Any] = field(default_factory=dict)
    utilities: Dict[str, float] = field(default_factory=dict)  # cost per tick
    
    def __post_init__(self):
        if not self.name:
            self.name = f"{self.type.capitalize()} {random.randint(1, 999)}"

@dataclass
class Relationship:
    """A relationship between two people."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    person_a_id: str
    person_b_id: str
    type: str = 'acquaintance'  # family, friend, partner, colleague, etc.
    strength: int = 0  # 0-100
    last_interaction: Optional[int] = None  # tick number
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.type:
            relationship_types = ['family', 'friend', 'partner', 'colleague', 'neighbor']
            self.type = random.choice(relationship_types)
