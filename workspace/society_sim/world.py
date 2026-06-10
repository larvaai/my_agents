"""World management for Society Sim."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

# Import actual class (not just type hint)
from models import Person, House, Job, WorldEvent, WorldState

if TYPE_CHECKING:
    from models import Person, House, Job, WorldEvent, WorldState

def create_default_world() -> WorldState:
    world = WorldState()
    # Create houses first
    house1 = House(id="h1", name="Apartment 4B", capacity=4, comfort=50.0)
    house2 = House(id="h2", name="Studio 7A", capacity=3, comfort=45.0)
    world.houses = [house1, house2]
    # Create jobs
    job1 = Job(id="j1", title="Barista", salary_per_day=80.0, required_skill=None, start_hour=7, end_hour=15)
    job2 = Job(id="j2", title="Office Clerk", salary_per_day=100.0, required_skill="general", start_hour=8, end_hour=17)
    job3 = Job(id="j3", title="Warehouse Worker", salary_per_day=90.0, required_skill=None, start_hour=6, end_hour=14)
    world.jobs = [job1, job2, job3]
    # Create people with random traits and skills
    names = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley']
    for i in range(6):
        person = Person(
            id=f"p{i+1}",
            name=names[i],
            age=random.randint(20, 50),
            money=random.uniform(50, 300),
            traits=[random.choice(['creative', 'analytical', 'energetic', 'calm']) for _ in range(random.randint(1, 2))],
            skills={'general': random.uniform(30, 80)},
            needs={n: random.uniform(40, 70) for n in ['hunger', 'energy', 'social', 'fun', 'hygiene']},
            mood='neutral',
            home_id=f"h{random.randint(1,2)}",
            job_id=None,
            relationships={f'p{j+1}': random.uniform(-5, 5) for j in range(i+1)},
            current_action='idle'
        )
        world.people.append(person)
    # Assign jobs to some people (morning workers)
    morning_jobs = [j for j in world.jobs if j.start_hour <= 8 and j.end_hour >= 14]
    for person in world.people[:2]:
        if random.random() < 0.5:
            available = [j for j in morning_jobs if not any(p.job_id == j.id for p in world.people)]
            if available:
                person.job_id = random.choice(available).id

    # Initialize relationships between all people
    for i, p1 in enumerate(world.people):
        for j, p2 in enumerate(world.people[i+1:], start=i+1):
            current_rel = p1.relationships.get(p2.id, 0)
            p1.relationships[p2.id] = min(100, max(-50, current_rel + random.uniform(-3, 3)))
            current_rel2 = p2.relationships.get(p1.id, 0)
            p2.relationships[p1.id] = min(100, max(-50, current_rel2 + random.uniform(-3, 3)))

    return world

def get_person(world: WorldState, person_id: str) -> Optional[Person]:
    for p in world.people:
        if p.id == person_id:
            return p
    return None

def get_job(world: WorldState, job_id: str) -> Optional[Job]:
    for j in world.jobs:
        if j.id == job_id:
            return j
    return None

def get_house(world: WorldState, house_id: str) -> Optional[House]:
    for h in world.houses:
        if h.id == house_id:
            return h
    return None

def add_event(world: WorldState, event_type: str, message: str, actor_id: Optional[str] = None, target_id: Optional[str] = None) -> WorldEvent:
    tick = world.tick
    event = WorldEvent(tick=tick, type=event_type, message=message, actor_id=actor_id, target_id=target_id)
    world.events.append(event)
    return event
