"""Action execution engine: validation, effects, and state transitions."""

# Action Execution Framework - Pure Business Logic
# Implements decision table from rules.py with minimal dependencies

# Action Validator - checks prerequisites before execution
class ActionValidator:
    """Validates action prerequisites and constraints."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.validation_log = []
    
    def validate_energy(self, energy: float, required: int) -> tuple[bool, str]:
        """Check if sufficient energy for action."""
        if energy >= required:
            return True, 'sufficient'  # OK - no log needed
        else:
            self.validation_log.append({
                'action': 'energy_check',
                'required': required,
                'available': round(energy, 1),
                'status': 'insufficient'
            })
            return False, f'need {required}, have {round(energy, 1)}'
    
    def validate_resource(self, resource_type: str, amount: int, inventory: dict) -> tuple[bool, str]:
        """Check if resources available for action."""
        current = inventory.get(resource_type, 0)
        if current >= amount:
            return True, 'sufficient'  # OK - no log needed
        else:
            self.validation_log.append({
                'action': 'resource_check',
                'type': resource_type,
                'required': amount,
                'available': current
            })
            return False, f'need {amount}, have {current}'
    
    def validate_action(self, action_name: str, actor: dict) -> tuple[bool, list]:
        """Validate all prerequisites for an action."""
        issues = []
        
        # Check energy requirement
        if 'energy_cost' in actor:
            ok, msg = self.validate_energy(actor['current_energy'], actor['energy_cost'])
            if not ok:
                issues.append(msg)
        
        # Check resource requirements
        for res_type, amount in actor.get('resource_requirements', {}).items():
            ok, msg = self.validate_resource(res_type, amount, actor.get('inventory', {}))
            if not ok:
                issues.append(msg)
        
        return len(issues) == 0, issues

# Action Effect Calculator - computes results after validation passes
class ActionEffectCalculator:
    """Calculates action effects and state changes."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.effects_log = []
    
    def calculate_energy_change(self, base_cost: int, duration_hours: int) -> float:
        """Calculate net energy change for an action."""
        # Base consumption during action
        consumed = base_cost * (duration_hours / 24.0)
        # Regeneration while resting (if not in full action mode)
        if self.config.get('resting', False):
            regenerated = duration_hours * 0.5
            return consumed - regenerated
        else:
            return -consumed
    
    def calculate_resource_yield(self, base_amount: int, skill_level: float) -> tuple[int, int]:
        """Calculate resource yield with skill multiplier."""
        min_yield = max(0, int(base_amount * 0.8))
        max_yield = int(base_amount * 1.2)
        # Apply skill bonus (up to 50% extra)
        if skill_level > 0:
            skill_bonus = min(0.5, skill_level / 100.0)
            max_yield = int(max_yield * (1 + skill_bonus))
        return min_yield, max_yield

# Action Registry - maps action names to their configurations
ACTION_REGISTRY = {
    'WORK': {
        'name': 'Work',
        'energy_cost': 30,
        'time_required': 8,      # hours per work session
        'resource_yield_min': 5,
        'resource_yield_max': 15,
        'prerequisites': ['HAS_JOB'],
        'optimal_phase': 'MORNING'  # OK - no log needed
    },
    'COMMUTE': {
        'name': 'Commute',
        'energy_cost': 20,
        'time_required': 1,      # hours per commute
        'resource_yield_min': 0,
        'resource_yield_max': 0,
        'prerequisites': ['HAS_JOB'],
        'optimal_phase': 'ANY'     # OK - no log needed
    },
    'EAT': {
        'name': 'Eat',
        'energy_cost': 15,
        'time_required': 0.5,    # hours per meal
        'resource_yield_min': 25,
        'resource_yield_max': 35,
        'prerequisites': ['HAS_FOOD'],
        'optimal_phase': 'ANY'     # OK - no log needed
    },
    'SLEEP': {
        'name': 'Sleep',
        'energy_cost': 0,        # Restorative action
        'time_required': 8,      # hours per sleep cycle
        'resource_yield_min': 40,
        'resource_yield_max': 60,
        'prerequisites': ['HAS_BED'],
        'optimal_phase': 'EVENING' # OK - no log needed
    },
    'RELAX': {
        'name': 'Relax',
        'energy_cost': 5,        # Low cost recovery
        'time_required': 2,      # hours per relaxation session
        'resource_yield_min': 10,
        'resource_yield_max': 20,
        'prerequisites': [],
        'optimal_phase': 'ANY'     # OK - no log needed
    },
    'HUNTER': {
        'name': 'Hunter',
        'energy_cost': 35,
        'time_required': 6,      # hours per hunting session
        'resource_yield_min': 10,
        'resource_yield_max': 25,
        'prerequisites': ['HAS_WEAPON'],
        'optimal_phase': 'MORNING' # OK - no log needed
    },
    'FARMER': {
        'name': 'Farmer',
        'energy_cost': 30,
        'time_required': 4,      # hours per farming session
        'resource_yield_min': 5,
        'resource_yield_max': 15,
        'prerequisites': ['HAS_SEEDS', 'HAS_PLOT'],
        'optimal_phase': 'MORNING' # OK - no log needed
    },
    'CRAFTSMAN': {
        'name': 'Craftsman',
        'energy_cost': 35,
        'time_required': 6,      # hours per crafting session
        'resource_yield_min': -10,
        'resource_yield_max': 20,
        'prerequisites': ['HAS_TOOLS'],
        'optimal_phase': 'AFTERNOON' # OK - no log needed
    },
}

__all__ = [
    'ActionValidator',
    'ActionEffectCalculator',
    'ACTION_REGISTRY'
]

