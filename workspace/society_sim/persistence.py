"""Persistence layer for Society Sim."""

import json
from typing import Any, Optional

from models import WorldState, Person, House, Job, WorldEvent

def save_world(world: WorldState, path: str) -> None:
    """Save world state to a JSON file."""
    data = {
        "tick": world.tick,
        "hour": world.hour,
        "day": world.day,
        "people": [{
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "money": round(p.money, 2),
            "traits": p.traits,
            "skills": {k: round(v, 1) for k, v in p.skills.items()},
            "needs": {k: round(v, 1) for k, v in p.needs.items()},
            "mood": p.mood,
            "home_id": p.home_id,
            "job_id": p.job_id,
            "relationships": {k: round(v, 1) for k, v in p.relationships.items()},
            "current_action": p.current_action
        } for p in world.people],
        "houses": [{
            "id": h.id,
            "name": h.name,
            "capacity": h.capacity,
            "comfort": round(h.comfort, 1),
            "residents": list(h.residents)
        } for h in world.houses],
        "jobs": [{
            "id": j.id,
            "title": j.title,
            "salary_per_day": round(j.salary_per_day, 2),
            "required_skill": j.required_skill,
            "start_hour": j.start_hour,
            "end_hour": j.end_hour
        } for j in world.jobs],
        "events": [{
            "tick": e.tick,
            "type": e.type,
            "message": e.message,
            "actor_id": e.actor_id,
            "target_id": e.target_id
        } for e in world.events]
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_world(path: str) -> WorldState:
    """Load a saved world state from a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create houses
    houses = [House(**h) for h in data['houses']] if data.get('houses') else []
    # Create jobs
    jobs = [Job(**j) for j in data['jobs']] if data.get('jobs') else []
    # Create people with default values for missing fields
    people_data = data.get('people', []) or []
    people = []
    for pd in people_data:
        p = Person(
            id=pd['id'],
            name=pd['name'],
            age=int(pd['age']),
            money=float(pd['money']),
            traits=list(pd.get('traits', [])),
            skills={k: float(v) for k, v in pd.get('skills', {}).items()},
            needs={k: float(v) for k, v in pd.get('needs', {}).items()},
            mood=str(pd['mood']),
            home_id=pd.get('home_id'),
            job_id=pd.get('job_id'),
            relationships={k: float(v) for k, v in pd.get('relationships', {}).items()},
            current_action=str(pd.get('current_action', 'idle'))
        )
        people.append(p)

    # Create events
    events_data = data.get('events', []) or []
    events = [WorldEvent(**e) for e in events_data] if events_data else []

    return WorldState(
        tick=int(data['tick']),
        hour=int(data['hour']),
        day=int(data['day']),
        people=people,
        houses=houses,
        jobs=jobs,
        events=events
    )
