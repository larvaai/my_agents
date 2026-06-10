#!/usr/bin/env python
"""Simulation engine for society_sim."""
from typing import Dict, List
import random


class Simulation:
    """Main simulation loop and control."""
    
    def __init__(self, world: dict):
        self.world = world
        self.tick_counter = 0
    
    def step(self) -> None:
        """Execute one tick of the simulation."""
        # Advance time
        if self.world['hour'] >= 23:
            self.world['hour'] = 6
            self.world['day'] += 1
        else:
            self.world['hour'] += 1
        
        self.tick_counter += 1
        
        # Process each person
        for person in self.world['people']:
            # Decay needs
            from rules import decay_needs, calculate_mood, choose_action, apply_action
            decay_needs(person, self.world['hour'])
            
            # Choose and apply action
            action = choose_action(person, self.world)
            event = apply_action(person, action, self.world)
            if event:
                self.world['events'].append(event)
        
        # Update moods for all people
        for person in self.world['people']:
            from rules import calculate_mood
            person['mood'] = calculate_mood(person)
    
    def run(self, ticks: int) -> None:
        """Run the simulation for a given number of ticks."""
        for t in range(ticks):
            self.step()
    
    def summary(self) -> Dict:
        """Generate a summary report."""
        day = self.world['day']
        hour = self.world['hour']
        population = len(self.world['people'])
        
        # Calculate averages
        if population > 0:
            avg_money = sum(p['money'] for p in self.world['people']) / population
            total_needs = 0
            mood_counts = {}
            for p in self.world['people']:
                for k, v in p['needs'].items():
                    total_needs += v
                m = p['mood']
                mood_counts[m] = mood_counts.get(m, 0) + 1
            avg_needs = total_needs / (population * 5)
        else:
            avg_money = 0.0
            avg_needs = 0.0
            mood_counts = {}
        
        # Get recent events (last 20)
        recent_events = self.world['events'][-20:] if len(self.world['events']) > 20 else self.world['events']
        
        return {
            'day': day,
            'hour': hour,
            'population': population,
            'average_money': round(avg_money, 2),
            'average_needs': round(avg_needs, 2),
            'mood_counts': mood_counts,
            'recent_events': recent_events
        }
