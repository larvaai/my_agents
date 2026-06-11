"""Event system: random, daily, seasonal, and triggered events."""

# Event Manager - core event processing logic
class EventManager:
    """Manages event scheduling, triggering, and effects."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.event_log = []  # Track all events for debugging
        self.active_events = {}  # {event_id: event_data}
    
    def schedule_random_event(self) -> dict:
        """Schedule a random event based on probability weights."""
        import random
        
        templates = self.config.get('random_templates', [])
        if not templates:
            return {'type': 'RANDOM_EMPTY', 'reason': 'no templates configured'}
        
        # Weighted selection from templates
        total_weight = sum(t.get('probability', 0.1) for t in templates)
        r = random.random() * total_weight
        cumulative = 0
        selected_template = None
        
        for template in templates:
            weight = template.get('probability', 0.1)
            cumulative += weight
            if r <= cumulative:
                selected_template = template
                break
        else:
            # Fallback to first template if none match (shouldn't happen with proper weights)
            selected_template = templates[0] if templates else None
        
        if not selected_template:
            return {'type': 'RANDOM_FAILED', 'reason': 'no matching template'}
        
        # Create event instance
        current_day = self.config.get('current_day', 1)
        event_id = f"RND_{current_day}_{random.randint(1000,9999)}"
        
        return {
            'type': 'RANDOM',
            'id': event_id,
            'template_name': selected_template.get('name'),
            'day': current_day,
            'effects': self._apply_effects(selected_template)
        }
    
    def _apply_effects(self, template) -> list:
        """Apply event effects and return effect log."""
        effects = []
        for eff in template.get('effects', []):
            effect_type = eff.get('type')
            action = eff.get('action')
            target = eff.get('target')
            amount = eff.get('amount')
            effects.append({
                'type': effect_type,
                'action': action,
                'target': target,
                'amount': amount
            })
        return effects

# Event Templates - predefined event configurations from catalog.py
EVENT_TEMPLATES = [
    {
        'category': 'RANDOM',
        'name': 'Supply Drop',
        'description': 'Random resource delivery to a household.',
        'probability': 0.15,
        'effects': [{'type': 'INVENTORY', 'action': 'ADD', 'target': 'SUPPLIES', 'amount': 2}]
    },
    {
        'category': 'DAILY',
        'name': 'Market Day',
        'description': 'Weekly market opportunity for traders.',
        'probability': 0.8,
        'allowed_days': [1, 3, 5, 7],  # Mon/Wed/Fri/Sun
        'effects': [{'type': 'OPPORTUNITY', 'action': 'TRADER_EVENT', 'target': 'MARKET', 'amount': 1}]
    },
    {
        'category': 'SEASONAL',
        'name': 'Harvest Season',
        'description': 'Seasonal crop yields increase.',
        'probability': 0.3,
        'seasons': ['SPRING', 'SUMMER'],  # Harvest seasons
        'effects': [{'type': 'RESOURCE', 'action': 'BONUS_YIELD', 'target': 'CROPS', 'amount': 1.5}]
    },
    {
        'category': 'TRIGGERED',
        'name': 'Festive Gathering',
        'description': 'Social event triggered by high relationship scores.',
        'probability': 0.4,
        'trigger_condition': 'AFFINITY_85',  # High affinity threshold
        'effects': [{'type': 'RELATIONSHIP', 'action': 'BOOST', 'target': 'ALL_NEIGHBORS', 'amount': 5}]
    },
    {
        'category': 'CRISIS',
        'name': 'Resource Shortage',
        'description': 'Supply chain disruption affecting multiple households.',
        'probability': 0.1,
        'trigger_condition': 'INVENTORY_LOW_SUPPLIES',  # Low supplies threshold
        'effects': [{'type': 'INVENTORY', 'action': 'REDUCE', 'target': 'SUPPLIES', 'amount': 3}, {'type': 'ECONOMY', 'action': 'INFLATION', 'target': 'COSTS', 'amount': 0.2}]
    },
    {
        'category': 'OPPORTUNITY',
        'name': 'Discovery Bonus',
        'description': 'Finding valuable resources or information.',
        'probability': 0.12,
        'effects': [{'type': 'RESOURCE', 'action': 'GAIN', 'target': 'MATERIALS', 'amount': 4}, {'type': 'INVENTORY', 'action': 'ADD', 'target': 'KNOWLEDGE', 'amount': 1}]
    },
]

__all__ = ['EventManager', 'EVENT_TEMPLATES']
]

