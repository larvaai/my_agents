"""Simulation engine for Society Sim."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from models import Person, WorldState, WorldEvent

class Simulation:
    def __init__(self, world: WorldState):
        self.world = world
        self.tick_count = 0
        self.day_events: list[WorldEvent] = []

    def step(self) -> None:
        """Run one tick of the simulation."""
        self.tick_count += 1
        self.world.tick = self.tick_count
        hour = self.world.hour
        day = self.world.day
        if hour == 23:
            # End of day - reset hour and increment day
            self.world.hour = 6
            self.world.day += 1
            self._end_of_day_event()

        for person in self.world.people:
            interacted = False
            # Decay needs
            decay_needs(person, hour, interacted)
            # Choose and apply action (pass current hour for work scheduling)
            action = choose_action(person, self.world, hour=hour)
            event = apply_action(person, action, self.world, hour=hour)
            if event:
                self.day_events.append(event)
                interacted = True
            # Update mood after all actions
            person.mood = calculate_mood(person)

    def _end_of_day_event(self) -> None:
        """Create a summary event at end of day."""
        avg_money = sum(p.money for p in self.world.people) / len(self.world.people) if self.world.people else 0
        avg_needs = {n: sum(p.needs.get(n, 0) for p in self.world.people) / len(self.world.people)
                    for n in ['hunger', 'energy', 'social', 'fun', 'hygiene']}
        mood_counts = {}
        for p in self.world.people:
            m = p.mood
            mood_counts[m] = mood_counts.get(m, 0) + 1
        summary_event = WorldEvent(
            tick=self.world.tick,
            type="day_summary",
            message=f"Day {self.world.day} ended. Pop: {len(self.world.people)}, Avg money: {avg_money:.0f}, Moods: {mood_counts}",
            actor_id=None
        )
        self.day_events.append(summary_event)

    def run(self, ticks: int) -> list[WorldEvent]:
        """Run simulation for specified number of ticks."""
        events = []
        for _ in range(ticks):
            self.step()
            events.extend(self.day_events)
            self.day_events.clear()
        return events

    def summary(self) -> Dict[str, Any]:
        """Get current simulation state summary."""
        avg_money = sum(p.money for p in self.world.people) / len(self.world.people) if self.world.people else 0
        avg_needs = {n: sum(p.needs.get(n, 0) for p in self.world.people) / len(self.world.people)
                    for n in ['hunger', 'energy', 'social', 'fun', 'hygiene']}
        mood_counts = {}
        for p in self.world.people:
            m = p.mood
            mood_counts[m] = mood_counts.get(m, 0) + 1

        return {
            "day": self.world.day,
            "hour": self.world.hour,
            "population": len(self.world.people),
            "average_money": round(avg_money, 2),
            "average_needs": avg_needs,
            "mood_counts": mood_counts,
            "recent_events": [e.message for e in self.day_events[-5:]]
        }

# Import rule functions here to avoid circular imports
from rules import decay_needs, choose_action, apply_action, calculate_mood
