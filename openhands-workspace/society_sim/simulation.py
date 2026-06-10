"""
Simulation Engine for Society Sim.

This module contains the main Simulation class that drives the game loop,
manages ticks, and provides summary statistics.
"""

from models import WorldState, Person, House, Job, WorldEvent
from rules import (
    decay_needs,
    calculate_mood,
    choose_action,
    apply_action,
)
import random


class Simulation:
    """Main simulation engine.
    
    The Simulation class manages the game loop, ticking through time,
    updating each person's state, and tracking events.
    
    Attributes:
        world: The current WorldState being simulated
    """
    
    def __init__(self, world: WorldState):
        """Initialize simulation with a world state.
        
        Args:
            world: The WorldState to simulate
        """
        self.world = world
    
    def step(self) -> None:
        """Execute one tick of the simulation.
        
        Each step:
        - Increments the tick counter
        - Updates hour/day cycle
        - Processes each person's needs, actions, and mood
        - Logs interesting events
        """
        # Increment tick
        self.world.tick += 1
        
        # Update time of day (every 24 ticks = one day)
        if self.world.tick % 24 == 0:
            self.world.hour = 6  # Start new day at 6 AM
            self.world.day += 1
        else:
            self.world.hour = (self.world.hour + 1) % 24
        
        # Process each person
        for person in self.world.people:
            # Decay needs based on current hour
            decay_needs(person, self.world.hour)
            
            # Choose and apply action
            action = choose_action(person, self.world)
            apply_action(person, action, self.world)
            
            # Update mood after all changes are applied
            person.mood = calculate_mood(person)
        
        # Add daily summary event every 24 ticks
        if self.world.tick % 24 == 0:
            add_daily_summary_event(self.world)
    
    def run(self, ticks: int) -> None:
        """Run the simulation for a specified number of ticks.
        
        Args:
            ticks: Number of ticks to simulate
        """
        for t in range(ticks):
            self.step()
    
    def summary(self) -> dict:
        """Generate a summary of the current simulation state.
        
        Returns a dictionary containing:
        - Current day and hour
        - Population count
        - Average money across all people
        - Average needs levels
        - Mood distribution
        - Recent events (last 10)
        """
        if not self.world.people:
            return {
                "day": self.world.day,
                "hour": self.world.hour,
                "population": 0,
                "average_money": 0.0,
                "average_needs": {},
                "mood_counts": {},
                "recent_events": [],
            }
        
        # Calculate averages
        total_money = sum(p.money for p in self.world.people)
        avg_money = total_money / len(self.world.people)
        
        # Average needs by type
        need_totals: dict[str, float] = {"hunger": 0.0, "energy": 0.0,
                                          "social": 0.0, "fun": 0.0, "hygiene": 0.0}
        for p in self.world.people:
            for need_type in need_totals:
                if need_type in p.needs:
                    need_totals[need_type] += p.needs[need_type]
        
        avg_needs = {
            k: v / len(self.world.people) for k, v in need_totals.items()
        }
        
        # Mood counts
        mood_counts: dict[str, int] = {}
        for p in self.world.people:
            m = p.mood
            mood_counts[m] = mood_counts.get(m, 0) + 1
        
        # Recent events (last 10)
        recent_events = [
            {
                "tick": e.tick,
                "type": e.type,
                "message": e.message,
                "actor_id": e.actor_id,
                "target_id": e.target_id,
            }
            for e in self.world.events[-10:]
        ]
        
        return {
            "day": self.world.day,
            "hour": self.world.hour,
            "population": len(self.world.people),
            "average_money": round(avg_money, 2),
            "average_needs": avg_needs,
            "mood_counts": mood_counts,
            "recent_events": recent_events,
        }


def add_daily_summary_event(world: WorldState) -> None:
    """Add a daily summary event at the start of each new day.
    
    Args:
        world: The current world state
    """
    from rules import clamp  # Import here to avoid circular dependency
    
    # Calculate average money for the message
    if world.people:
        avg_money = sum(p.money for p in world.people) / len(world.people)
        msg = f"New day begins! Day {world.day} starts at 6 AM."
    else:
        msg = "A new day begins..."
    
    add_event(
        world,
        event_type="daily",
        message=msg,
        actor_id=None,
        target_id=None,
    )


def add_event(
    world: WorldState,
    event_type: str,
    message: str,
    actor_id: str | None = None,
    target_id: str | None = None,
) -> WorldEvent:
    """Add an event to the simulation timeline.
    
    Args:
        world: The current world state
        event_type: Category of the event
        message: Human-readable description
        actor_id: Optional ID of who caused/acted in the event
        target_id: Optional ID of who was affected by the event
    
    Returns:
        The newly created WorldEvent object
    """
    event = WorldEvent(
        tick=world.tick,
        type=event_type,
        message=message,
        actor_id=actor_id,
        target_id=target_id,
    )
    world.events.append(event)
    return event