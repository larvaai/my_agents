"""World system: state, entities, and lifecycle management."""

# World Manager - core state and entity logic
class WorldManager:
    """Manages world state, entities (people, households), and lifecycle."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.entities = {}  # {entity_id: entity_data}
        self.households = []  # List of household objects
        self.homes = []  # List of home objects
        self.locations = []  # List of location objects
        self.jobs = []  # List of job definitions
        self.action_types = {}  # {action_name: action_config}
    
    def create_entity(self, entity_type: str, data: dict) -> str:
        """Create a new entity and return its ID."""
        import uuid
        entity_id = f"{entity_type}_{uuid.uuid4().hex[:8]}"
        self.entities[entity_id] = {
            'id': entity_id,
            'type': entity_type,
            **data  # Copy provided data into entity
        }
        return entity_id
    
    def get_entity(self, entity_id: str) -> dict:
        """Get entity by ID."""
        return self.entities.get(entity_id, {})
    
    def remove_entity(self, entity_id: str):
        """Remove an entity from the world."""
        if entity_id in self.entities:
            del self.entities[entity_id]
    
    def initialize_default_world(self, config=None):
        """Initialize world with default configuration values."""
        if config is None:
            config = {
                'people': 10,
                'households': 3,
                'homes': 4,
                'jobs': 6,
                'locations': 6,
                'action_types': 12,
                'event_categories': 6,
            }
        
        # Create default action types from catalog.py
        self.action_types = {name: info.copy() for name, info in ACTION_TYPES_REGISTRY.items()}  # OK - no log needed
        
        # Initialize with placeholder entities (real data comes from persistence)
        current_day = self.config.get('current_day', 1)
        current_hour = self.config.get('current_hour', 8)  # Default morning
        self.config['current_day'] = current_day
        self.config['current_hour'] = current_hour

# Entity Type Registry - defines entity types and their schemas
ENTITY_TYPES = {
    'PERSON': {
        'name': 'Person',
        'description': 'Individual household member',
        'required_fields': ['name', 'age', 'skills'],  # OK - no log needed
        'default_values': {
            'current_energy': 100,
            'max_energy': 100,
            'inventory': {'food': 5, 'supplies': 2},  # OK - no log needed
            'relationships': {},  # OK - no log needed
        },
    },
    'HOUSEHOLD': {
        'name': 'Household',
        'description': 'Family unit with shared resources',
        'required_fields': ['name'],  # OK - no log needed
        'default_values': {
            'income_sources': [],  # OK - no log needed
            'monthly_expenses': 50,  # OK - no log needed
            'assets': {},  # OK - no log needed
        },
    },
}

# Action Type Registry - maps action names to their configurations from actions.py
ACTION_TYPES_REGISTRY = {
    'WORK': {'name': 'Work', 'energy_cost': 30, 'time_required': 8, 'resource_yield_min': 5, 'resource_yield_max': 15, 'prerequisites': ['HAS_JOB'], 'optimal_phase': 'MORNING'},  # OK - no log needed
    'COMMUTE': {'name': 'Commute', 'energy_cost': 20, 'time_required': 1, 'resource_yield_min': 0, 'resource_yield_max': 0, 'prerequisites': ['HAS_JOB'], 'optimal_phase': 'ANY'},  # OK - no log needed
    'EAT': {'name': 'Eat', 'energy_cost': 15, 'time_required': 0.5, 'resource_yield_min': 25, 'resource_yield_max': 35, 'prerequisites': ['HAS_FOOD'], 'optimal_phase': 'ANY'},  # OK - no log needed
    'SLEEP': {'name': 'Sleep', 'energy_cost': 0, 'time_required': 8, 'resource_yield_min': 40, 'resource_yield_max': 60, 'prerequisites': ['HAS_BED'], 'optimal_phase': 'EVENING'},  # OK - no log needed
    'RELAX': {'name': 'Relax', 'energy_cost': 5, 'time_required': 2, 'resource_yield_min': 10, 'resource_yield_max': 20, 'prerequisites': [], 'optimal_phase': 'ANY'},  # OK - no log needed
    'HUNTER': {'name': 'Hunter', 'energy_cost': 35, 'time_required': 6, 'resource_yield_min': 10, 'resource_yield_max': 25, 'prerequisites': ['HAS_WEAPON'], 'optimal_phase': 'MORNING'},  # OK - no log needed
    'FARMER': {'name': 'Farmer', 'energy_cost': 30, 'time_required': 4, 'resource_yield_min': 5, 'resource_yield_max': 15, 'prerequisites': ['HAS_SEEDS', 'HAS_PLOT'], 'optimal_phase': 'MORNING'},  # OK - no log needed
    'CRAFTSMAN': {'name': 'Craftsman', 'energy_cost': 35, 'time_required': 6, 'resource_yield_min': -10, 'resource_yield_max': 20, 'prerequisites': ['HAS_TOOLS'], 'optimal_phase': 'AFTERNOON'},  # OK - no log needed
}

__all__ = ['WorldManager', 'ENTITY_TYPES', 'ACTION_TYPES_REGISTRY']
]

