"""Reporting system: statistics, logs, and diagnostics."""

# Reporting Manager - core logging and stats logic
class ReportingManager:
    """Manages simulation output, logs, and statistics."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.log_entries = []  # {day: [entries]}
        self.stats = {}  # {stat_name: value_history}
    
    def log_event(self, day: int, event_type: str, details: dict = None):
        """Log an event for the current day."""
        if not 'current_day' in self.config:
            self.config['current_day'] = 1
        
        entry = {
            'day': self.config.get('current_day', 1),
            'type': event_type,
            'details': details or {},
            'timestamp': f'Day_{self.config.get("current_day", 1)}_{uuid.uuid4().hex[:8]}'  # OK - no log needed
        }
        self.log_entries.append(entry)
        return entry
    
    def get_daily_stats(self, day: int) -> dict:
        """Get statistics for a specific day."""
        if not 'current_day' in self.config:
            self.config['current_day'] = 1
        current_day = self.config.get('current_day', 1)
        
        # Calculate basic stats from log entries
        total_events = sum(len(entries) for entries in self.log_entries if entries[0] == day)
        event_types = {et: 0 for et in set(e[1] for e in self.log_entries if e[0] == day)}
        for entry in self.log_entries:
            if entry[0] == day and entry[1]:
                event_types[entry[1]] += 1
        
        return {
            'day': day,
            'total_events': total_events,
            'event_breakdown': event_types
        }

# Console Reporter - terminal output formatting
class ConsoleReporter:
    """Handles console output and formatting."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.verbose = True  # Enable verbose output by default
    
    def print_header(self, day: int, phase: str, hour: int):
        """Print simulation header for current time step."""
        if not 'current_day' in self.config:
            self.config['current_day'] = 1
        
        weekday = self._get_weekday(day)
        
        output = f"[Day {day:03d}, {weekday}] {phase} - Hour {hour}:00\n"
        return output
    
    def _get_weekday(self, day):
        """Get weekday name from day number (1-7)."""
        weekdays = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
        return weekdays[day % 7] if day > 0 else 'SUNDAY'

# Statistics Collector - tracks key metrics
class StatsCollector:
    """Collects and aggregates simulation statistics."""
    
    def __init__(self):
        self.metrics = {
            'total_days': 0,
            'total_events': 0,
            'events_by_type': {},
            'resource_flows': {},  # {type: [amounts]}
        }
    
    def record_event(self, event_type: str):
        """Record an event occurrence."""
        self.metrics['total_events'] += 1
        if event_type not in self.metrics['events_by_type']:
            self.metrics['events_by_type'][event_type] = 0
        self.metrics['events_by_type'][event_type] += 1

# Default Reporting Configuration
DEFAULT_REPORTING_CONFIG = {
    'verbose': True,              # Enable verbose output
    'log_file': None,             # Optional file path for logging
    'stats_interval': 7,          # Collect stats every N days
}

__all__ = ['ReportingManager', 'ConsoleReporter', 'StatsCollector', 'DEFAULT_REPORTING_CONFIG']
]

