#!/usr/bin/env python
"""World management for society_sim."""
from typing import Optional
import random

def create_default_world() -> dict:
    """Create a default world with 6+ people, 2+ houses, 3+ jobs."""
    world = {
        'tick': 0,
        'hour': 6,
        'day': 1,
        'people': [],
        'houses': [],
        'jobs': [],
        'events': []
    }
    
    # Create 2 houses
    for i in range(2):
        world['houses'].append({
            'id': f'house_{i+1}',
            'name': f"House {i+1}",
            'capacity': 4,
            'comfort': 50.0 + random.uniform(-10, 10),
            'residents': []
        })
    
    # Create 3 jobs
    world['jobs'].append({
        'id': 'job_1',
        'title': 'Office Worker',
        'salary_per_day': 200.0,
        'required_skill': None,
        'start_hour': 8,
        'end_hour': 17
    })
    
    world['jobs'].append({
        'id': 'job_2',
        'title': 'Factory Worker',
        'salary_per_day': 150.0,
        'required_skill': None,
        'start_hour': 6,
        'end_hour': 14
    })
    
    world['jobs'].append({
        'id': 'job_3',
        'title': 'Retail Clerk',
        'salary_per_day': 120.0,
        'required_skill': None,
        'start_hour': 9,
        'end_hour': 18
    })
    
    # Create 6 people with initial relationships (to other people, not jobs)
    for i in range(6):
        person = {
            'id': f'person_{i+1}',
            'name': ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"][i],
            'age': 20 + random.randint(0, 30),
            'money': 100.0,
            'traits': [],
            'skills': {},
            'needs': {
                'hunger': 50.0,
                'energy': 100.0,
                'social': 50.0,
                'fun': 50.0,
                'hygiene': 80.0
            },
            'mood': 'neutral',
            'home_id': None,
            'job_id': None,
            # Initialize relationships to other people (empty dict, will be populated)
            'relationships': {},
            'current_action': 'idle'
        }
        
        # Assign home
        world['people'].append(person)
        available_homes = [h for h in world['houses'] if len(h['residents']) < h['capacity']]
        if available_homes:
            person['home_id'] = random.choice(available_homes)['id']
            available_homes[0]['residents'].append(person['id'])
        
        # Assign some jobs
        if i % 2 == 0 and world['jobs']:
            job = random.choice(world['jobs'])
            person['job_id'] = job['id']

    for i, person in enumerate(world['people']):
        for other in world['people'][i + 1:]:
            person['relationships'][other['id']] = 0.0
            other['relationships'][person['id']] = 0.0
    
    return world

def get_person(world, person_id):
    """Get a person by ID."""
    for p in world['people']:
        if p['id'] == person_id:
            return p
    return None

def get_job(world, job_id):
    """Get a job by ID."""
    for j in world['jobs']:
        if j['id'] == job_id:
            return j
    return None

def get_house(world, house_id):
    """Get a house by ID."""
    for h in world['houses']:
        if h['id'] == house_id:
            return h
    return None

def add_event(world, event_type, message, actor_id=None, target_id=None):
    """Add an event to the world."""
    event = {
        'tick': world['tick'],
        'type': event_type,
        'message': message,
        'actor_id': actor_id,
        'target_id': target_id
    }
    world['events'].append(event)
    return event
