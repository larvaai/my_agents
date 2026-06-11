"""Business logic invariants and decision tables for society simulation."""

# Core Invariants - These must always hold true
INVARANTS = [
    ("ENERGY_CONSERVATION", "Energy consumed cannot exceed energy available + regeneration"),
    ("RESOURCE_BALANCE", "Total resources across all households is conserved or changes only via events"),
    ("TIME_FLOW", "Time advances monotonically; no backward jumps allowed"),
    ("POPULATION_STABILITY", "Population changes only through birth, death, migration events"),
    ("ECONOMIC_CLOSED_SYSTEM", "Money flows between entities but total system value is tracked"),
]

# Decision Table: Energy Management
# Format: (condition, action, priority)
ENERGY_DECISIONS = [
    # High energy - can do most actions
    ("energy >= 80%", "FULL_ACTION_MODE", 1),
    # Medium-high energy - normal operations
    ("50% <= energy < 80%", "NORMAL_ACTION_MODE", 2),
    # Medium-low energy - need rest soon
    ("30% <= energy < 50%", "CAUTION_MODE", 3),
    # Low energy - urgent need for recovery
    ("10% <= energy < 30%", "CRITICAL_RECOVERY", 4),
    # Critical - immediate action required
    ("energy < 10%", "EMERGENCY_REST", 5),
]

# Decision Table: Action Selection Priority
# Higher priority = more likely to be chosen when multiple actions available
ACTION_PRIORITY_ORDER = [
    'WORK',           # Primary income source - highest priority when employed
    'COMMUTE',        # Must happen before/after work-related actions
    'EAT',            # Basic survival need
    'SLEEP',          # Recovery mechanism
    'RELAX',          # Mental health maintenance
    'HUNTER',         # Resource gathering - secondary income
    'FARMER',         # Long-term resource production
    'CRAFTSMAN',      # Value creation from existing resources
    'TRADER',         # Exchange mechanism
    'SOCIABLE',       # Relationship building
    'LEARNER',        # Skill development
    'EXPLORER',       # Discovery and expansion
]

# Decision Table: Event Response Priorities
EVENT_RESPONSE_PRIORITY = [
    ('CRISIS', 1),      # Most urgent - immediate response needed
    ('OPPORTUNITY', 2),  # High value if seized quickly
    ('RANDOM', 3),       # Standard processing
    ('DAILY', 4),        # Routine handling
    ('SEASONAL', 5),     # Periodic attention
    ('TRIGGERED', 6),    # Context-dependent response
]

# Household Economy Rules
ECONOMY_RULES = [
    ("INCOME_SOURCE", "Households must have at least one income source to generate money"),
    ("EXPENSE_TRACKING", "All resource consumption reduces household inventory"),
    ("CASH_FLOW", "Income - Expenses = Net Flow; negative flow triggers deficit events"),
    ("INVESTMENT", "Surplus can be invested in assets, skills, or relationships"),
]

# Relationship Development Rules
RELATIONSHIP_RULES = [
    ("INITIAL_STATE", "New neighbors start with neutral/unknown relationship level"),
    ("POSITIVE_INTERACTIONS", "Helping, sharing resources, social events increase affinity"),
    ("NEGATIVE_INTERACTIONS", "Conflict, resource hoarding, ignoring decrease affinity"),
    ("DECAY_RATE", "Relationships slowly decay without positive interaction"),
    ("THRESHOLDS", "Key thresholds: Friendly (>30%), Good Friend (>60%), Best Friend (>85%)"),
]

# Time Management Rules
TIME_RULES = [
    ("DAY_CYCLE", "Each day has morning, afternoon, evening phases with different action availability"),
    ("WEEKLY_RHYTHM", "Certain events/actions only available on specific days"),
    ("SEASONAL_CYCLES", "Seasons affect resource availability and event types"),
]

# Default Configuration Values
DEFAULT_CONFIG = {
    'energy_regeneration_rate': 0.5,      # Energy per day when resting
    'work_income_base': 15,               # Base income from work action
    'hunting_yield': [2, 8],              # Min/max resources from hunter action
    'farming_growth_rate': 0.3,            # Crop growth multiplier
    'crafting_efficiency': 0.8,            # Crafting success rate base
    'social_interaction_cost': 1,          # Energy cost for social actions
    'relationship_decay_per_day': 2,       # Points lost per day without interaction
}

__all__ = [
    'INVARANTS',
    'ENERGY_DECISIONS',
    'ACTION_PRIORITY_ORDER',
    'EVENT_RESPONSE_PRIORITY',
    'ECONOMY_RULES',
    'RELATIONSHIP_RULES',
    'TIME_RULES',
    'DEFAULT_CONFIG'
]

