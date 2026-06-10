"""Simulation rules and behavior functions."""

from typing import List, Dict, Optional
import random

# ============ UTILITY FUNCTIONS ============

def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    """Keep value within bounds."""
    return max(min_value, min(max_value, value))

# ============ NEEDS DECAY ============

def decay_needs(person: 'Person', hour: int) -> None:
    """Decay needs based on time and current state.
    
    Args:
        person: The person whose needs to decay
        hour: Current hour (6-23)
    """
    # Base decay rates per tick
    hunger_decay = 0.5 + (hour - 6) * 0.1  # Higher during day
    energy_decay = 0.3 if person.needs['energy'] > 40 else 0.2  # Less when tired
    social_decay = 0.2 if person.needs['social'] > 50 else 0.15
    fun_decay = 0.15
    hygiene_decay = 0.1

    # Apply decay with randomness
    import random
    hunger = max(0, min(100, person.needs['hunger'] - clamp(hunger_decay * random.uniform(0.8, 1.2), 0, 5)))
    energy = max(0, min(100, person.needs['energy'] - clamp(energy_decay * random.uniform(0.8, 1.2), 0, 3)))
    social = max(0, min(100, person.needs['social'] - clamp(social_decay * random.uniform(0.8, 1.2), 0, 4)))
    fun = max(0, min(100, person.needs['fun'] - clamp(fun_decay * random.uniform(0.8, 1.2), 0, 2)))
    hygiene = max(0, min(100, person.needs['hygiene'] - clamp(hygiene_decay * random.uniform(0.8, 1.2), 0, 2)))

    # Update needs (keep in valid range)
    person.needs['hunger'] = clamp(hunger, 0, 100)
    person.needs['energy'] = clamp(energy, 0, 100)
    person.needs['social'] = clamp(social, 0, 100)
    person.needs['fun'] = clamp(fun, 0, 100)
    person.needs['hygiene'] = clamp(hygiene, 0, 100)

# ============ MOOD CALCULATION ============

def calculate_mood(person: 'Person') -> str:
    """Calculate current mood based on needs."""
    avg_need = sum(person.needs.values()) / len(person.needs)
    min_critical = min(person.needs['hunger'], person.needs['energy'])
    min_social_fun = min(person.needs['social'], person.needs['fun'])

    # Critical states first
    if min_critical < 20:
        return 'distressed'
    if min_social_fun < 25:
        return 'lonely'
    if avg_need > 70:
        return 'happy'
    return 'neutral'

# ============ ACTION SELECTION ============

def choose_action(person: 'Person', world: 'WorldState') -> str:
    """Choose the best action for a person based on needs."""
    hour = world.hour
    job = None
    if person.job_id and any(j.id == person.job_id for j in world.jobs):
        job = next((j for j in world.jobs if j.id == person.job_id), None)

    # Priority order based on needs
    actions_priority = [
        ('eat', 'hunger' < 35, 1.0),
        ('sleep', 'energy' < 30, 1.0),
        ('clean', 'hygiene' < 30, 1.0),
        ('work', job is not None and hour >= job.start_hour and hour < job.end_hour, 0.95),
        ('socialize', 'social' < 40, 0.85),
        ('play', 'fun' < 40, 0.85),
        ('idle', True, 0.7),
    ]

    # Find best action (highest priority that's applicable)
    for action_name, condition, base_priority in actions_priority:
        if condition or (action_name == 'idle' and not any(a[1] for a in actions_priority[:-1])):
            return action_name

    return 'idle'

# ============ ACTION APPLICATION ============

def apply_action(person: 'Person', action: str, world: 'WorldState') -> List['WorldEvent']:
    """Apply an action and update the person/world. Returns events."""
    events: List[WorldEvent] = []
    hour = world.hour
    job = None
    if person.job_id and any(j.id == person.job_id for j in world.jobs):
        job = next((j for j in world.jobs if j.id == person.job_id), None)

    # EAT - increases hunger slightly, costs money
    if action == 'eat':
        cost = 5.0 + random.uniform(0, 3)  # $5-8 per meal
        person.money -= cost
        person.needs['hunger'] = min(100, person.needs['hunger'] + 25)
        events.append(WorldEvent(
            tick=world.tick,
            type='daily',
            message=f"{person.name} ate a meal (-${cost:.1f})",
            actor_id=person.id
        ))

    # SLEEP - restores energy, slightly reduces social (less awake)
    elif action == 'sleep':
        person.needs['energy'] = min(100, person.needs['energy'] + 35)
        person.needs['social'] = max(0, person.needs['social'] - 2)  # Less socialization while sleeping
        events.append(WorldEvent(
            tick=world.tick,
            type='daily',
            message=f"{person.name} slept (+35 energy)",
            actor_id=person.id
        ))

    # CLEAN - restores hygiene
    elif action == 'clean':
        person.needs['hygiene'] = min(100, person.needs['hygiene'] + 25)
        events.append(WorldEvent(
            tick=world.tick,
            type='daily',
            message=f"{person.name} cleaned up (+25 hygiene)",
            actor_id=person.id
        ))

    # WORK - earns money, costs energy/fun/hygiene, improves skill
    elif action == 'work':
        if job:
            salary = job.salary_per_day * 0.1  # Partial day work
            person.money += salary
            person.needs['energy'] = max(0, person.needs['energy'] - 25)
            person.needs['fun'] = max(0, person.needs['fun'] - 15)
            person.needs['hygiene'] = max(0, person.needs['hygiene'] - 10)
            # Improve relevant skill
            if job.required_skill:
                current_level = person.skills.get(job.required_skill, 0)
                new_level = min(100, current_level + 0.5)  # Small improvement per work day
                person.skills[job.required_skill] = new_level
            person.needs['energy'] = max(0, person.needs['energy'] - 25)
            person.needs['fun'] = max(0, person.needs['fun'] - 15)
            person.needs['hygiene'] = max(0, person.needs['hygiene'] - 10)
            # Improve relevant skill
            if job.required_skill:
                current_level = person.skills.get(job.required_skill, 0)
                new_level = min(100, current_level + 0.5)  # Small improvement per work day
                person.skills[job.required_skill] = new_level