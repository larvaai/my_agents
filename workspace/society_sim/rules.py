"""Rule functions for Society Sim."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

# Import actual classes (not just type hints)
from models import Person, House, Job, WorldEvent, WorldState

if TYPE_CHECKING:
    from models import Person, WorldState

# Constants for decay rates
DECAY_RATES = {
    "hunger": 2.0,
    "energy": 1.5,
    "social": 3.0,
    "fun": 0.8,
    "hygiene": 0.5
}

def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, value))

def decay_needs(person: Person, hour: int, interacted: bool = False) -> None:
    for need in ["hunger", "energy", "social", "fun", "hygiene"]:
        rate = DECAY_RATES.get(need, 1.0)
        if need == "energy" and hour >= 6:
            rate *= 3
        elif not interacted and need == "social":
            rate = 3.0
        person.needs[need] = max(0.0, person.needs[need] - rate)

def calculate_mood(person: Person) -> str:
    if any(v < 20 for v in [person.needs.get("hunger", 0),
                           person.needs.get("energy", 0)]):
        return "distressed"
    if any(v < 25 for v in [person.needs.get("social", 0),
                           person.needs.get("fun", 0)]):
        return "lonely"
    avg = sum(person.needs.values()) / len(person.needs)
    if avg > 70:
        return "happy"
    return "neutral"

def choose_action(person: Person, world: WorldState, hour: int = 6) -> str:
    # Priority actions
    if person.needs.get("hunger", 100) < 35:
        return "eat"
    if person.needs.get("energy", 100) < 30:
        return "sleep"
    if person.needs.get("hygiene", 100) < 30:
        return "clean"
    # Work time
    for job in world.jobs:
        if person.job_id == job.id and job.start_hour <= hour < job.end_hour:
            return "work"
    # Social needs - check both need level AND relationship depth
    others = [p for p in world.people if p.id != person.id and p.home_id == person.home_id]
    avg_relationship = sum(person.relationships.get(o.id, 0) for o in others) / len(others) if others else 100
    # If average relationship is low, prioritize socializing even if need isn't critical
    if person.needs.get("social", 100) < 40 or avg_relationship < 20:
        return "socialize"
    if person.needs.get("fun", 100) < 40:
        return "play"
    return "idle"

def apply_action(person: Person, action: str, world: WorldState, hour: int = None) -> WorldEvent | None:
    event = None
    if action == "eat":
        cost = 5.0 + random.uniform(0, 3)
        person.money = max(0, person.money - cost)
        person.needs["hunger"] = min(100, person.needs["hunger"] + 25)
        event = WorldEvent(tick=world.tick, type="eat", message=f"{person.name} ate food.", actor_id=person.id)
    elif action == "sleep":
        person.needs["energy"] = min(100, person.needs["energy"] + 35)
        person.needs["social"] = max(0, person.needs["social"] - 5)
        event = WorldEvent(tick=world.tick, type="sleep", message=f"{person.name} slept.", actor_id=person.id)
    elif action == "clean":
        person.needs["hygiene"] = min(100, person.needs["hygiene"] + 25)
        event = WorldEvent(tick=world.tick, type="clean", message=f"{person.name} cleaned up.", actor_id=person.id)
    elif action == "work":
        if not person.job_id:
            return None
        job = next((j for j in world.jobs if j.id == person.job_id), None)
        if job:
            salary = job.salary_per_day * 0.5
            person.money += salary
            person.needs["energy"] = max(0, person.needs["energy"] - 15)
            person.needs["fun"] = max(0, person.needs["fun"] - 8)
            person.needs["hygiene"] = max(0, person.needs["hygiene"] - 5)
            skill = job.required_skill or "general"
            current = person.skills.get(skill, 0)
            person.skills[skill] = min(100, current + 0.5)
            event = WorldEvent(tick=world.tick, type="work", message=f"{person.name} worked at {job.title}. Earned {salary:.0f}", actor_id=person.id)
    elif action == "socialize":
        others = [p for p in world.people if p.id != person.id and p.home_id == person.home_id]
        if not others:
            return None
        target = random.choice(others)
        current_rel = person.relationships.get(target.id, 0)
        person.relationships[target.id] = min(100, current_rel + 5)
        other_rel = target.relationships.get(person.id, 0)
        target.relationships[person.id] = min(100, other_rel + 5)
        person.needs["social"] = min(100, person.needs["social"] + 10)
        event = WorldEvent(tick=world.tick, type="socialize", message=f"{person.name} socialized with {target.name}", actor_id=person.id, target_id=target.id)
    elif action == "play":
        person.needs["fun"] = min(100, person.needs["fun"] + 25)
        person.needs["energy"] = max(0, person.needs["energy"] - 8)
        event = WorldEvent(tick=world.tick, type="play", message=f"{person.name} played.", actor_id=person.id)
    elif action == "idle":
        person.needs["energy"] = min(100, person.needs["energy"] + 2)
    return event
