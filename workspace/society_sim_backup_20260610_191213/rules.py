#!/usr/bin/env python
"""Game rules for society_sim."""
from typing import List, Optional
import random

def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, value))

def decay_needs(person: dict, hour: int) -> None:
    person['needs']['hunger'] = clamp(person['needs']['hunger'] - 0.5, 0.0, 100.0)
    energy_decay = 0.8 if hour >= 6 and hour < 23 else 0.3
    person['needs']['energy'] = clamp(person['needs']['energy'] - energy_decay, 0.0, 100.0)
    person['needs']['social'] = clamp(person['needs']['social'] - 0.6, 0.0, 100.0)
    person['needs']['fun'] = clamp(person['needs']['fun'] - 0.2, 0.0, 100.0)
    person['needs']['hygiene'] = clamp(person['needs']['hygiene'] - 0.15, 0.0, 100.0)

def calculate_mood(person: dict) -> str:
    avg_need = sum(person['needs'].values()) / len(person['needs'])
    if person['needs']['hunger'] < 20 or person['needs']['energy'] < 20:
        return "distressed"
    if person['needs']['social'] < 25 or person['needs']['fun'] < 25:
        return "lonely"
    if avg_need > 70:
        return "happy"
    return "neutral"

def choose_action(person: dict, world: dict) -> str:
    if person['needs']['hunger'] < 35:
        return "eat"
    if person['needs']['energy'] < 30:
        return "sleep"
    if person['needs']['hygiene'] < 30:
        return "clean"
    current_hour = world['hour']
    for job in world['jobs']:
        if (job['start_hour'] <= current_hour < job['end_hour'] and
            person.get('job_id') == job['id']):
            return "work"
    if person['needs']['social'] < 40:
        return "socialize"
    if person['needs']['fun'] < 40:
        return "play"
    return "idle"

def apply_action(person: dict, action: str, world: dict) -> Optional[dict]:
    event = None
    if action == "eat":
        cost = 5.0
        if person.get('money', 0) >= cost:
            person['money'] -= cost
            person['needs']['hunger'] = clamp(person['needs']['hunger'] + 15, 0.0, 100.0)
            event = {'tick': world['tick'], 'type': "eat",
                'message': f"{person.get('name', 'Person')} ate food (-${cost})"}
    elif action == "sleep":
        person['needs']['energy'] = clamp(person['needs']['energy'] + 25, 0.0, 100.0)
        person['needs']['social'] = clamp(person['needs']['social'] - 3, 0.0, 100.0)
        event = {'tick': world['tick'], 'type': "sleep",
            'message': f"{person.get('name', 'Person')} slept (+25 energy)"}
    elif action == "clean":
        person['needs']['hygiene'] = clamp(person['needs']['hygiene'] + 10, 0.0, 100.0)
        event = {'tick': world['tick'], 'type': "clean",
            'message': f"{person.get('name', 'Person')} cleaned up (+10 hygiene)"}
    elif action == "work":
        if person.get('job_id'):
            job = next((j for j in world['jobs'] if j['id'] == person['job_id']), None)
            if job:
                salary = job['salary_per_day'] / 8
                if 'money' not in person: person['money'] = 0
                person['money'] += salary
                person['needs']['energy'] = clamp(person['needs']['energy'] - 10, 0.0, 100.0)
                person['needs']['fun'] = clamp(person['needs']['fun'] - 5, 0.0, 100.0)
                person['needs']['hygiene'] = clamp(person['needs']['hygiene'] - 3, 0.0, 100.0)
                if job.get('required_skill'):
                    current_level = person.get('skills', {}).get(job['required_skill'], 0)
                    if 'skills' not in person: person['skills'] = {}
                    person['skills'][job['required_skill']] = clamp(current_level + 0.5, 0.0, 100.0)
                event = {'tick': world['tick'], 'type': "work",
                    'message': f"{person.get('name', 'Person')} worked (+${salary:.2f})"}
    elif action == "socialize":
        if len(world.get('people', [])) > 1:
            others = [p for p in world['people'] if p['id'] != person['id']]
            other = others[0] if others else None
            if other:
                current_rel_person = person.get('relationships', {}).get(other['id'], 0)
                current_rel_other = other.get('relationships', {}).get(person['id'], 0)
                new_rel = min(current_rel_person + 5, 100.0)
                new_rel_other = min(current_rel_other + 5, 100.0)
                if 'relationships' not in person: person['relationships'] = {}
                if 'relationships' not in other: other['relationships'] = {}
                person['relationships'][other['id']] = new_rel
                other['relationships'][person['id']] = new_rel_other
                person['needs']['social'] = clamp(person['needs']['social'] + 8, 0.0, 100.0)
                event = {'tick': world['tick'], 'type': "socialize",
                    'message': f"{person.get('name', 'Person')} socialized with {other.get('name', 'someone')}"}
    elif action == "play":
        person['needs']['fun'] = clamp(person['needs']['fun'] + 10, 0.0, 100.0)
        person['needs']['energy'] = clamp(person['needs']['energy'] - 8, 0.0, 100.0)
        event = {'tick': world['tick'], 'type': "play",
            'message': f"{person.get('name', 'Person')} played (+10 fun)"}
    elif action == "idle":
        if 'needs' not in person: person['needs'] = {}
        if 'energy' not in person['needs']: person['needs']['energy'] = 50.0
        person['needs']['energy'] = clamp(person['needs']['energy'] + 2, 0.0, 100.0)
        event = {'tick': world['tick'], 'type': "idle",
            'message': f"{person.get('name', 'Person')} was idle"}
    return event
