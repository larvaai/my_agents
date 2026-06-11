"""Catalog of domain entities: action types, event templates, job categories."""

# Action Types (12 required)
ACTION_TYPES = [
    'WORK',           # Primary income-generating activity
    'COMMUTE',        # Travel between locations
    'EAT',            # Consume food from inventory
    'SLEEP',          # Restore energy/health
    'RELAX',          # Mental recovery, low cost
    'HUNTER',         # Gather resources in wild
    'FARMER',         # Cultivate plots for crops
    'CRAFTSMAN',      # Create goods from materials
    'TRADER',         # Exchange items with others
    'SOCIABLE',       # Build relationships, social events
    'LEARNER',        # Skill development activities
    'EXPLORER',       # Discover new locations/info
]

# Event Categories (6 required)
EVENT_CATEGORIES = [
    'RANDOM',         # Unpredictable occurrences
    'DAILY',          # Recurring at same time each day
    'SEASONAL',       # Time-based cycles
    'TRIGGERED',      # Caused by specific actions/states
    'CRISIS',         # Disruptive high-impact events
    'OPPORTUNITY',    # Beneficial unexpected events
]

# Event Templates (6 required)
EVENT_TEMPLATES = [
    {
        "category": "RANDOM",
        "name": "Supply Drop",
        "description": "Random resource delivery to a household.",
        "probability": 0.15,
        "effects": [{"type": "INVENTORY", "action": "ADD", "target": "SUPPLIES", "amount": 2}]
    },
    {
        "category": "DAILY",
        "name": "Market Day",
        "description": "Weekly market opportunity for traders.",
        "probability": 0.8,
        "effects": [{"type": "OPPORTUNITY", "action": "TRADER_EVENT", "target": "MARKET", "amount": 1}]
    },
    {
        "category": "SEASONAL",
        "name": "Harvest Season",
        "description": "Seasonal crop yields increase.",
        "probability": 0.3,
        "effects": [{"type": "RESOURCE", "action": "BONUS_YIELD", "target": "CROPS", "amount": 1.5}]
    },
    {
        "category": "TRIGGERED",
        "name": "Festive Gathering",
        "description": "Social event triggered by high relationship scores.",
        "probability": 0.4,
        "effects": [{"type": "RELATIONSHIP", "action": "BOOST", "target": "ALL_NEIGHBORS", "amount": 5}]
    },
    {
        "category": "CRISIS",
        "name": "Resource Shortage",
        "description": "Supply chain disruption affecting multiple households.",
        "probability": 0.1,
        "effects": [{"type": "INVENTORY", "action": "REDUCE", "target": "SUPPLIES", "amount": 3}, {"type": "ECONOMY", "action": "INFLATION", "target": "COSTS", "amount": 0.2}]
    },
    {
        "category": "OPPORTUNITY",
        "name": "Discovery Bonus",
        "description": "Finding valuable resources or information.",
        "probability": 0.12,
        "effects": [{"type": "RESOURCE", "action": "GAIN", "target": "MATERIALS", "amount": 4}, {"type": "INVENTORY", "action": "ADD", "target": "KNOWLEDGE", "amount": 1}]
    },
]

# Job Categories (6 required)
JOB_CATEGORIES = [
    'MANUFACTURING',   # Production-focused roles
    'SERVICE',         # Customer-facing or support roles
    'AGRICULTURE',     # Farming, harvesting, land management
    'TRADE',           # Commerce, logistics, sales
    'CRAFTING',        # Artisanal production
    'TECHNICAL',       # Specialized skills and expertise
]

# Default population configuration (10 people, 3 households, 4 homes)
DEFAULT_POPULATION = {
    "people": 10,
    "households": 3,
    "homes": 4,
    "jobs": 6,
    "locations": 6,
    "action_types": 12,
    "event_categories": 6,
}

__all__ = [
    'ACTION_TYPES',
    'EVENT_CATEGORIES',
    'EVENT_TEMPLATES',
    'JOB_CATEGORIES',
    'DEFAULT_POPULATION',
]

