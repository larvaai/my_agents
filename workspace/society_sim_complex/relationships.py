"""Relationship system: neighbor affinity, social events, and interaction tracking."""

# Relationship Manager - core affinity logic
class RelationshipManager:
    """Manages relationships between household members and neighbors."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.interaction_log = []
    
    def calculate_affinity(self, base: int, interactions: list) -> float:
        """Calculate relationship affinity based on interaction history."""
        if not interactions:
            return 20.0  # Neutral starting point
        
        positive = sum(1 for i in interactions if i.get('type') == 'POSITIVE')
        negative = sum(1 for i in interactions if i.get('type') == 'NEGATIVE')
        neutral = len(interactions) - positive - negative
        
        # Base affinity from interaction count (up to 100 points)
        interaction_bonus = min(60, len(interactions) * 3)
        
        # Affinity decay over time (without recent interactions)
        days_since_interaction = self.config.get('days_since_last', 7)
        decay_factor = max(0.5, 1.0 - (days_since_interaction / 30.0))
        
        affinity = base + interaction_bonus * decay_factor
        return min(100.0, max(0.0, affinity))
    
    def record_interaction(self, actor_id: str, neighbor_id: str, interaction_type: str, intensity: int = 1):
        """Record a social interaction."""
        self.interaction_log.append({
            'actor': actor_id,
            'neighbor': neighbor_id,
            'type': interaction_type,
            'intensity': intensity,
            'timestamp': self.config.get('current_day', 1)
        })
    
    def get_relationship_status(self, actor: dict) -> dict:
        """Get current relationship status for an actor."""
        relationships = actor.get('relationships', {})  # {neighbor_id: affinity}
        total_affinity = sum(relationships.values()) if relationships else 0
        avg_affinity = total_affinity / len(relationships) if relationships else 20.0
        
        status = 'UNKNOWN'  # New neighbor, no interactions yet
        if relationships:
            max_rel = max(relationships.values())
            min_rel = min(relationships.values())
            if max_rel > 85:
                status = 'BEST_FRIEND'
            elif max_rel > 60:
                status = 'GOOD_FRIEND'
            elif max_rel > 30:
                status = 'FRIENDLY'
            else:
                status = 'ACQUAINTANCE'
        
        return {
            'total_affinity': round(total_affinity, 1),
            'avg_affinity': round(avg_affinity, 1),
            'status': status,
            'count': len(relationships)
        }

# Social Event Trigger - determines when social events occur
class SocialEventTrigger:
    """Monitors relationship levels to trigger appropriate social events."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.event_history = []  # Track recent events to prevent spam
    
    def check_for_events(self, actor: dict) -> list:
        """Check if any social events should trigger for this actor."""
        triggers = []
        relationships = actor.get('relationships', {})  # {neighbor_id: affinity}
        current_day = self.config.get('current_day', 1)
        
        # Check relationship-based triggers (every 3 days to prevent spam)
        if current_day % 3 == 0 and relationships:
            for neighbor_id, affinity in relationships.items():
                if affinity > 85:  # Best friend threshold
                    trigger = {
                        'type': 'FESTIVE_GATHERING',
                        'target': neighbor_id,
                        'reason': f'Best friend celebration (affinity={round(affinity, 1)}%)'
                    }
                    triggers.append(trigger)
        
        # Check seasonal/community events (every 7 days)
        if current_day % 7 == 0:
            trigger = {
                'type': 'COMMUNITY_EVENT',
                'target': 'ALL',
                'reason': f'Weekly community gathering'
            }
            triggers.append(trigger)
        
        return triggers

# Relationship Decay Monitor - tracks decay over time
class RelationshipDecayMonitor:
    """Monitors and applies relationship decay when interactions are sparse."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.last_interaction_time = {}  # {neighbor_id: last_interaction_day}
    
    def apply_decay(self, actor: dict) -> int:
        """Apply decay to relationships based on time since last interaction."""
        total_decay = 0
        current_day = self.config.get('current_day', 1)
        relationships = actor.get('relationships', {})  # {neighbor_id: affinity}
        
        for neighbor_id, affinity in list(relationships.items()):
            days_since = current_day - self.last_interaction_time.get(neighbor_id, current_day)
            decay_rate = self.config.get('decay_per_day', 2)  # Points per day
            decay_amount = min(int(days_since * decay_rate), int(affinity * 0.1))  # Cap at 10% of affinity
            relationships[neighbor_id] -= decay_amount
            total_decay += decay_amount
            self.last_interaction_time[neighbor_id] = current_day
        
        return total_decay

# Social Event Registry - defines available social events
SOCIAL_EVENTS = {
    'FESTIVE_GATHERING': {
        'name': 'Festive Gathering',
        'description': 'Celebration with best friends',
        'energy_cost': 20,
        'time_required': 4,      # hours
        'resource_yield_min': 5,
        'resource_yield_max': 15,
        'prerequisites': ['AFFINITY_85'],  # Need best friend status
        'optimal_phase': 'EVENING'
    },
    'COMMUNITY_EVENT': {
        'name': 'Community Event',
        'description': 'Weekly town gathering',
        'energy_cost': 15,
        'time_required': 3,      # hours
        'resource_yield_min': 8,
        'resource_yield_max': 20,
        'prerequisites': [],
        'optimal_phase': 'ANY'
    },
}

__all__ = ['RelationshipManager', 'SocialEventTrigger', 'RelationshipDecayMonitor', 'SOCIAL_EVENTS']
]

