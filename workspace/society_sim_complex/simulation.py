"""Simulation engine: main loop, time management, and coordination."""

# Simulation Engine - core runtime logic
class SimulationEngine:
    """Main simulation loop coordinator."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.current_day = 1
        self.current_hour = 8  # Default morning
        self.simulation_log = []  # Track all simulation events
        self.paused = False
    
    def advance_time(self, hours=24):
        """Advance simulation time by specified hours."""
        if self.paused:
            return {'type': 'TIME_ADVANCE', 'hours': hours, 'status': 'PAUSED'}
        
        # Calculate new hour and day
        self.current_hour += hours
        while self.current_hour >= 24:
            self.current_hour -= 24
            self.current_day += 1
        
        log_entry = {
            'type': 'TIME_ADVANCE',
            'hours': hours,
            'new_day': self.current_day,
            'new_hour': self.current_hour
        }
        self.simulation_log.append(log_entry)
        return log_entry
    
    def get_current_phase(self) -> str:
        """Determine current time-of-day phase."""
        hour = self.config.get('current_hour', self.current_hour)
        if 5 <= hour < 12:
            return 'MORNING'
        elif 12 <= hour < 17:
            return 'AFTERNOON'
        else:
            return 'EVENING'
    
    def get_weekday(self) -> str:
        """Get current day of week (1-7)."""
        day_of_week = self.current_day % 7
        weekdays = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
        return weekdays[day_of_week - 1] if day_of_week > 0 else 'SUNDAY'

# Time Event Scheduler - schedules and fires time-based events
class TimeEventScheduler:
    """Schedules and fires time-based events."""
    
    def __init__(self, engine: SimulationEngine):
        self.engine = engine
        self.scheduled_events = []  # {event_id: {'type': ..., 'day': ..., 'triggered': False}}
    
    def schedule_daily_event(self, event_type: str, day_of_week: int):
        """Schedule an event to occur on specific days of the week."""
        current_day = self.engine.current_day
        # Calculate when next occurrence will be (0-6 for MON-SUN)
        current_weekday = current_day % 7
        if current_weekday == day_of_week:
            # Event should trigger today
            return {'type': 'DAILY_TRIGGER', 'event_type': event_type, 'day': current_day}
        else:
            # Calculate days until next occurrence (0-6)
            days_until = (day_of_week - current_weekday) % 7
            if days_until == 0:
                days_until = 7  # Will trigger in 7 days (next week)
            return {'type': 'DAILY_PENDING', 'event_type': event_type, 'days_until': days_until}

# Simulation State Manager - tracks overall simulation state
class SimulationStateManager:
    """Manages global simulation state and checkpoints."""
    
    def __init__(self):
        self.checkpoints = []  # {day: snapshot_data}
        self.running = True
    
    def create_checkpoint(self, day: int, world_state: dict):
        """Create a save checkpoint."""
        checkpoint = {
            'day': day,
            'world_state': world_state.copy(),  # Shallow copy for performance
            'timestamp': f'Day_{day}_{self.running}'  # OK - no log needed
        }
        self.checkpoints.append(checkpoint)
        return checkpoint

__all__ = ['SimulationEngine', 'TimeEventScheduler', 'SimulationStateManager']
]

