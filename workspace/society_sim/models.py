"""Data model classes for Society Sim."""

from __future__ import annotations
import random
from dataclasses import dataclass, field, asdict
from typing import Optional

# Constants
NEEDS = ["hunger", "energy", "social", "fun", "hygiene"]
MOOD_VALUES = {"distressed": 0.1, "lonely": 0.2, "happy": 0.3, "neutral": 0.4}

@dataclass
class Person:
    id: str
    name: str
    age: int
    money: float = 0.0
    traits: list[str] = field(default_factory=list)
    skills: dict[str, float] = field(default_factory=dict)
    needs: dict[str, float] = field(default_factory=dict)
    mood: str = "neutral"
    home_id: Optional[str] = None
    job_id: Optional[str] = None
    relationships: dict[str, float] = field(default_factory=dict)
    current_action: str = "idle"

@dataclass
class House:
    id: str
    name: str
    capacity: int
    comfort: float = 50.0
    residents: list[str] = field(default_factory=list)

@dataclass
class Job:
    id: str
    title: str
    salary_per_day: float
    required_skill: Optional[str] = None
    start_hour: int = 8
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
    people: list[Person] = field(default_factory=list)
    houses: list[House] = field(default_factory=list)
    jobs: list[Job] = field(default_factory=list)
    events: list[WorldEvent] = field(default_factory=list)
