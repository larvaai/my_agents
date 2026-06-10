"""
World management for Society Sim.

Handles creating a default starting world, querying entities,
and adding events to the simulation timeline.
"""

from models import (
    Person,
    House,
    Job,
    WorldEvent,
    WorldState,
)
import random
from rules import clamp  # Import clamp for relationship calculations


def create_default_world() -> WorldState:
    """Create a default starting world with sample entities.
    
    Returns a WorldState containing:
    - At least 6 people (with varied traits and initial needs)
    - At least 2 houses (with capacity for residents)
    - At least 3 jobs (covering different skill requirements)
    - Initial relationships between all people
    """
    world = WorldState()
    
    # Create 6-8 people with varied characteristics
    person_templates = [
        {"name": "Alex", "age": 28, "traits": ["ambitious", "organized"], "skills": {"management": 45}},
        {"name": "Jordan", "age": 31, "traits": ["creative", "energetic"], "skills": {"design": 60}},
        {"name": "Sam", "age": 24, "traits": ["friendly", "adaptable"], "skills": {"sales": 55}},
        {"name": "Taylor", "age": 35, "traits": ["detail-oriented", "patient"], "skills": {"support": 70}},
        {"name": "Casey", "age": 29, "traits": ["bold", "competitive"], "skills": {"leadership": 65}},
        {"name": "Riley", "age": 26, "traits": ["curious", "helpful"], "skills": {"research": 50}},
    ]
    
    # Create people
    for template in person_templates:
        p = Person(
            name=template["name"],
            age=template["age"],
            traits=template.get("traits", []),
            skills=template.get("skills", {}),
        )
        world.people.append(p)
    
    # Create 2-3 houses
    house_templates = [
        {"name": "Downtown Apartment Complex", "capacity": 6, "comfort": 80},
        {"name": "Suburban Family Home", "capacity": 4, "comfort": 75},
        {"name": "Studio Loft", "capacity": 2, "comfort": 90},
    ]
    
    for template in house_templates:
        h = House(
            name=template["name"],
            capacity=template["capacity"],
            comfort=template["comfort"],
        )
        world.houses.append(h)
    
    # Create 3-4 jobs
    job_templates = [
        {"title": "Office Manager", "salary": 120, "skill": "management", "hours": (8, 17)},
        {"title": "Creative Designer", "salary": 95, "skill": "design", "hours": (9, 18)},
        {"title": "Sales Associate", "salary": 80, "skill": "sales", "hours": (10, 20)},
        {"title": "Customer Support", "salary": 70, "skill": "support", "hours": (8, 16)},
    ]
    
    for template in job_templates:
        j = Job(
            title=template["title"],
            salary_per_day=template["salary"],
            required_skill=template.get("skill"),
            start_hour=template["hours"][0],
            end_hour=template["hours"][1],
        )
        world.jobs.append(j)
    
    # Assign people to houses (distribute evenly, respecting capacity)
    total_people = len(world.people)
    total_capacity = sum(h.capacity for h in world.houses)
    
    if total_capacity > 0:
        # Sort houses by remaining capacity
        house_order = sorted(
            range(len(world.houses)),
            key=lambda i: (len(world.houses[i].residents), -world.houses[i].capacity),
        )
        
        for person in world.people:
            # Find a house with available space
            assigned = False
            for h_idx in house_order:
                if len(world.houses[h_idx].residents) < world.houses[h_idx].capacity:
                    world.houses[h_idx].residents.append(person.id)
                    person.home_id = world.houses[h_idx].id
                    assigned = True
                    break
            
            if not assigned:
                # If no space, create a new house for them
                new_house = House(
                    name=f"Solo Residence {len(world.houses) + 1}",
                    capacity=2,
                    comfort=60,
                )
                world.houses.append(new_house)
                new_house.residents.append(person.id)
                person.home_id = new_house.id
    
    # Assign some people to jobs (based on skills and availability)
    for job in world.jobs:
        if job.required_skill:
            # Find qualified candidates
            qualified = [
                p for p in world.people
                if p.skills.get(job.required_skill, 0) >= 30  # Minimum skill threshold
            ]
            
            if qualified and len(qualified) < total_people:
                # Assign one qualified person to this job
                candidate = random.choice(qualified)
                candidate.job_id = job.id
    
    # Create initial relationships (everyone knows everyone at least slightly)
    for i, p1 in enumerate(world.people):
        for j, p2 in enumerate(world.people):
            if i < j:  # Avoid duplicates and self-relationships
                # Base relationship based on proximity (same house = closer)
                base_rel = 5.0
                if p1.home_id == p2.home_id:
                    base_rel += 10.0  # Roommates know each other better
                
                # Add small random variation
                rel_value = clamp(base_rel + random.uniform(-3, 3), 0, 50)
                p1.relationships[p2.id] = rel_value
    
    return world


def get_person(world: WorldState, person_id: str) -> Person | None:
    """Find a person by their ID.
    
    Args:
        world: The current world state
        person_id: The unique ID of the person to find
    
    Returns:
        The Person object if found, or None otherwise
    """
    for p in world.people:
        if p.id == person_id:
            return p
    return None


def get_job(world: WorldState, job_id: str) -> Job | None:
    """Find a job by its ID.
    
    Args:
        world: The current world state
        job_id: The unique ID of the job to find
    
    Returns:
        The Job object if found, or None otherwise
    """
    for j in world.jobs:
        if j.id == job_id:
            return j
    return None


def get_house(world: WorldState, house_id: str) -> House | None:
    """Find a house by its ID.
    
    Args:
        world: The current world state
        house_id: The unique ID of the house to find
    
    Returns:
        The House object if found, or None otherwise
    """
    for h in world.houses:
        if h.id == house_id:
            return h
    return None


def add_event(
    world: WorldState,
    event_type: str,
    message: str,
    actor_id: str | None = None,
    target_id: str | None = None,
) -> WorldEvent:
    """Add an event to the simulation timeline.
    
    Events are stored in world.events and can be used for:
    - Tracking interesting moments
    - Triggering special effects
    - Creating a narrative log of what's happening
    
    Args:
        world: The current world state
        event_type: Category of the event (social, work, daily, random, etc.)
        message: Human-readable description
        actor_id: Optional ID of who caused/acted in the event
        target_id: Optional ID of who was affected by the event
    
    Returns:
        The newly created WorldEvent object
    """
    from rules import clamp  # Import here to avoid circular dependency
    
    event = WorldEvent(
        tick=world.tick,
        type=event_type,
        message=message,
        actor_id=actor_id,
        target_id=target_id,
    )
    world.events.append(event)
    return event