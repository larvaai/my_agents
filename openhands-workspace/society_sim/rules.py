"""
Core rules and mechanics for Society Sim.

This module contains all the rule functions that drive simulation behavior:
- Need decay over time
- Mood calculation from needs
- Action selection based on current state
- Action application with effects
"""

from models import Person, WorldState
import random


def apply_action(person: Person, action: str, world: WorldState,
                 target_id: str | None = None) -> None:
    """Apply the effects of an action on a person and world.
    
    Each action has specific effects on needs, money, relationships, etc.
    
    Args:
        person: The person performing the action
        action: Action string (eat, sleep, clean, work, socialize, play, idle)
        world: Current world state for context
        target_id: Optional ID of specific person to interact with (for socialize)
    """
    # Eat - increases hunger slightly, costs money
    if action == "eat":
        cost = 5.0 + random.uniform(0, 3)  # $5-8 per meal
        person.money -= cost
        person.needs["hunger"] = min(100.0, person.needs.get("hunger", 0) + 25)
        person.needs["energy"] = min(100.0, person.needs.get("energy", 0) + 5)
    
    # Sleep - increases energy significantly, slight social cost
    elif action == "sleep":
        person.needs["energy"] = min(100.0, person.needs.get("energy", 0) + 40)
        person.needs["social"] = max(0.0, person.needs.get("social", 0) - 3)
    
    # Clean - restores hygiene
    elif action == "clean":
        person.needs["hygiene"] = min(100.0, person.needs.get("hygiene", 0) + 25)
    
    # Work - earns money but drains energy and other needs
    elif action == "work":
        salary = 80.0 + random.uniform(-10, 10)  # $70-90 per day
        person.money += salary
        person.needs["energy"] = max(0.0, person.needs.get("energy", 0) - 25)
        person.needs["fun"] = max(0.0, person.needs.get("fun", 0) - 8)
        person.needs["hygiene"] = max(0.0, person.needs.get("hygiene", 0) - 10)
        
        # Improve relevant skill
        if person.job_id:
            job = next((j for j in world.jobs if j.id == person.job_id), None)
            if job and job.required_skill:
                current_skill = person.skills.get(job.required_skill, 0)
                new_skill = min(100.0, current_skill + 2)  # +2 skill per work day
                person.skills[job.required_skill] = new_skill
    
    # Socialize - improves relationships and social need
    elif action == "socialize":
        # Find another person to interact with
        other_people = [p for p in world.people if p.id != person.id]
        if other_people:
            # If target_id is provided, use that specific person
            if target_id:
                targets = [p for p in other_people if p.id == target_id]
                if targets:
                    target = targets[0]
                else:
                    target = random.choice(other_people)
            else:
                target = random.choice(other_people)
            
            # Increase relationship between both parties
            current_rel = person.relationships.get(target.id, 0)
            new_rel = min(100.0, current_rel + 8)  # +8 relationship per interaction
            person.relationships[target.id] = new_rel
            
            # Also update target's relationship with us (symmetric)
            if hasattr(target, 'relationships'):
                target_relationships = getattr(target, 'relationships', {})
                if not isinstance(target_relationships, dict):
                    target_relationships = {}
                current_target_rel = target_relationships.get(person.id, 0)
                new_target_rel = min(100.0, current_target_rel + 8)
                target.relationships[person.id] = new_target_rel
            
            # Boost social need for both parties
            person.needs["social"] = min(100.0, person.needs.get("social", 0) + 15)
            if hasattr(target, 'needs'):
                target.needs["social"] = min(100.0, target.needs.get("social", 0) + 15)
    
    # Play - boosts fun but costs energy
    elif action == "play":
        person.needs["fun"] = min(100.0, person.needs.get("fun", 0) + 20)
        person.needs["energy"] = max(0.0, person.needs.get("energy", 0) - 15)
    
    # Idle - slight energy recovery or no change
    elif action == "idle":
        person.needs["energy"] = min(100.0, person.needs.get("energy", 0) + 2)
    
    # Update current action
    person.current_action = action


def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    """Clamp a value between min and max (inclusive).
    
    Args:
        value: The value to clamp
        min_value: Lower bound (default 0)
        max_value: Upper bound (default 100)
    
    Returns:
        Value constrained within [min_value, max_value]
    """
    return max(min_value, min(max_value, value))


def decay_needs(person: Person, hour: int) -> None:
    """Decay all needs based on time and current state.
    
    Each tick, needs naturally decrease unless acted upon:
    - Hunger decreases steadily (starvation risk)
    - Energy decreases when awake
    - Social decreases if not interacting with others
    - Fun decreases slowly over time
    - Hygiene decreases gradually
    
    Args:
        person: The person whose needs will decay
        hour: Current hour (affects energy decay rate)
    """
    # Base decay rates per tick
    base_decay = {
        "hunger": 2.0,      # Slow starvation
        "energy": 3.5 if hour < 6 or hour >= 22 else 5.0,  # More when awake
        "social": 1.5,      # Moderate social decay
        "fun": 0.8,         # Very slow fun decay
        "hygiene": 1.0,     # Slow hygiene decay
    }
    
    for need, rate in base_decay.items():
        if need not in person.needs:
            continue
        
        current = person.needs[need]
        new_value = max(0.0, current - rate)
        person.needs[need] = clamp(new_value)


def calculate_mood(person: Person) -> str:
    """Calculate mood based on current needs.
    
    Mood states (in order of priority):
    1. "distressed" - if hunger or energy < 20
    2. "lonely" - if social or fun < 25
    3. "happy" - if average needs > 70
    4. "neutral" - otherwise
    
    Args:
        person: The person whose mood to calculate
    
    Returns:
        Current mood string
    """
    # Check for distressed state (most severe)
    critical_needs = [person.needs.get("hunger", 100), person.needs.get("energy", 100)]
    if any(need < 20 for need in critical_needs):
        return "distressed"
    
    # Check for lonely state
    social_needs = [person.needs.get("social", 100), person.needs.get("fun", 100)]
    if any(need < 25 for need in social_needs):
        return "lonely"
    
    # Check for happy state
    valid_needs = [v for v in person.needs.values() if isinstance(v, (int, float))]
    if valid_needs and sum(valid_needs) / len(valid_needs) > 70:
        return "happy"
    
    # Default to neutral
    return "neutral"


def choose_action(person: Person, world: WorldState) -> str:
    """Choose the best action for a person based on their current state.
    
    Priority order (most urgent first):
    1. Eat - if hunger < 35
    2. Sleep - if energy < 30
    3. Clean - if hygiene < 30
    4. Work - if currently at work hours and has a job
    5. Socialize - if social < 40
    6. Play - if fun < 40
    7. Idle - otherwise
    
    Args:
        person: The person to choose action for
        world: Current world state (for checking work hours)
    
    Returns:
        Selected action string
    """
    # Priority-based action selection
    if person.needs.get("hunger", 100) < 35:
        return "eat"
    
    if person.needs.get("energy", 100) < 30:
        return "sleep"
    
    if person.needs.get("hygiene", 100) < 30:
        return "clean"
    
    # Check work hours (assuming standard 8-5 schedule)
    current_hour = world.hour
    has_job = person.job_id is not None and any(
        j.id == person.job_id for j in world.jobs
    )
    if 7 <= current_hour < 19 and has_job:
        return "work"
    
    # Social needs check
    social_need = person.needs.get("social", 100)
    fun_need = person.needs.get("fun", 100)
    if social_need < 40:
        return "socialize"
    
    if fun_need < 40:
        return "play"
    
    # Default to idle
    return "idle"


def apply_action(person: Person, action: str, world: WorldState) -> None:
    """Apply the effects of an action on a person and world.
    
    Each action has specific effects on needs, money, relationships, etc.
    
    Args:
        person: The person performing the action
        action: Action string (eat, sleep, clean, work, socialize, play, idle)
        world: Current world state for context
    """
    # Eat - increases hunger slightly, costs money
    if action == "eat":
        cost = 5.0 + random.uniform(0, 3)  # $5-8 per meal
        person.money -= cost
        person.needs["hunger"] = min(100.0, person.needs.get("hunger", 0) + 25)
        person.needs["energy"] = min(100.0, person.needs.get("energy", 0) + 5)
    
    # Sleep - increases energy significantly, slight social cost
    elif action == "sleep":
        person.needs["energy"] = min(100.0, person.needs.get("energy", 0) + 40)
        person.needs["social"] = max(0.0, person.needs.get("social", 0) - 3)
    
    # Clean - restores hygiene
    elif action == "clean":
        person.needs["hygiene"] = min(100.0, person.needs.get("hygiene", 0) + 25)
    
    # Work - earns money but drains energy and other needs
    elif action == "work":
        salary = 80.0 + random.uniform(-10, 10)  # $70-90 per day
        person.money += salary
        person.needs["energy"] = max(0.0, person.needs.get("energy", 0) - 25)
        person.needs["fun"] = max(0.0, person.needs.get("fun", 0) - 8)
        person.needs["hygiene"] = max(0.0, person.needs.get("hygiene", 0) - 10)
        
        # Improve relevant skill
        if person.job_id:
            job = next((j for j in world.jobs if j.id == person.job_id), None)
            if job and job.required_skill:
                current_skill = person.skills.get(job.required_skill, 0)
                new_skill = min(100.0, current_skill + 2)  # +2 skill per work day
                person.skills[job.required_skill] = new_skill
    
    # Socialize - improves relationships and social need
    elif action == "socialize":
        # Find another person to interact with
        other_people = [p for p in world.people if p.id != person.id]
        if other_people:
            target = random.choice(other_people)
            
            # Increase relationship between both parties
            current_rel = person.relationships.get(target.id, 0)
            new_rel = min(100.0, current_rel + 8)  # +8 relationship per interaction
            person.relationships[target.id] = new_rel
            
            # Also update target's relationship with us (symmetric)
            if hasattr(target, 'relationships'):
                target_relationships = getattr(target, 'relationships', {})
                if not isinstance(target_relationships, dict):
                    target_relationships = {}
                current_target_rel = target_relationships.get(person.id, 0)
                new_target_rel = min(100.0, current_target_rel + 8)
                target.relationships[person.id] = new_target_rel
            
            # Boost social need for both parties
            person.needs["social"] = min(100.0, person.needs.get("social", 0) + 15)
            if hasattr(target, 'needs'):
                target.needs["social"] = min(100.0, target.needs.get("social", 0) + 15)
    
    # Play - boosts fun but costs energy
    elif action == "play":
        person.needs["fun"] = min(100.0, person.needs.get("fun", 0) + 20)
        person.needs["energy"] = max(0.0, person.needs.get("energy", 0) - 15)
    
    # Idle - slight energy recovery or no change
    elif action == "idle":
        person.needs["energy"] = min(100.0, person.needs.get("energy", 0) + 2)
    
    # Update current action
    person.current_action = action
