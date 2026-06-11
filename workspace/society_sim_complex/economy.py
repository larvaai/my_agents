"""Economy system: household income, expenses, and resource tracking."""

# Economy Manager - core financial logic
class EconomyManager:
    """Manages household finances, income sources, and expense tracking."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.transaction_log = []  # Track all economic transactions
    
    def register_income_source(self, actor_id: str, source_type: str, base_amount: int) -> bool:
        """Register a new income source for an actor."""
        sources = self.config.get('income_sources', {})  # {actor_id: [source_configs]}
        if actor_id not in sources:
            sources[actor_id] = []
        
        source_config = {
            'type': source_type,
            'base_amount': base_amount,
            'status': 'ACTIVE'  # ACTIVE, INACTIVE, EXPIRED
        }
        sources[actor_id].append(source_config)
        self.config['income_sources'] = sources
        return True
    
    def calculate_monthly_income(self, actor: dict) -> int:
        """Calculate total monthly income from all active sources."""
        sources = self.config.get('income_sources', {}).get(actor.get('id'), [])
        if not sources:
            return 0
        
        # Filter to ACTIVE sources only
        active_sources = [s for s in sources if s.get('status') == 'ACTIVE']
        total_income = sum(s.get('base_amount', 0) * 2.5 for s in active_sources)
        return int(total_income)  # Monthly (assuming 1 work session per week)
    
    def record_expense(self, actor_id: str, expense_type: str, amount: int):
        """Record an expense and deduct from inventory."""
        current_day = self.config.get('current_day', 1)
        transaction = {
            'type': 'EXPENSE',
            'actor': actor_id,
            'expense_type': expense_type,
            'amount': amount,
            'day': current_day
        }
        
        # Deduct from appropriate inventory slot
        if expense_type == 'FOOD' and 'inventory' in actor:
            food_slot = actor['inventory'].get('food', 0)
            if food_slot >= amount:
                actor['inventory']['food'] -= amount
            else:
                # Partial deduction or overflow to supplies
                needed = amount - food_slot
                if 'supplies' in actor['inventory'] and actor['inventory']['supplies'] >= needed:
                    actor['inventory']['supplies'] -= needed
        elif expense_type == 'SUPPLIES':
            supply_slot = actor['inventory'].get('supplies', 0)
            if supply_slot >= amount:
                actor['inventory']['supplies'] -= amount
            else:
                # Overflow to materials or knowledge slots
                for slot_name in ['materials', 'knowledge']:
                    slot_val = actor['inventory'].get(slot_name, 0)
                    if slot_val >= needed and amount > 0:
                        actor['inventory'][slot_name] -= min(amount, needed, slot_val)
                        break
        
        transaction_log.append(transaction)
        return True
    
    def calculate_deficit_risk(self, actor: dict) -> tuple[int, str]:
        """Calculate monthly deficit risk based on income vs expenses."""
        monthly_income = self.calculate_monthly_income(actor)
        estimated_expenses = 50  # Base food cost per month (adjustable)
        
        if monthly_income >= estimated_expenses * 1.2:
            return 0, 'SURPLUS'  # 20% buffer is healthy
        elif monthly_income >= estimated_expenses * 0.8:
            return int((estimated_expenses - monthly_income) / 3), 'LOW_RISK'  # Small deficit
        else:
            return int((estimated_expenses - monthly_income) / 2), 'HIGH_RISK'  # Significant deficit

# Income Source Registry - predefined income sources
INCOME_SOURCES = {
    'WORK': {
        'name': 'Employment',
        'description': 'Primary income from job',
        'base_amount': 15,  # Per session (weekly)
        'prerequisites': ['HAS_JOB'],
        'optimal_phase': 'MORNING'
    },
    'HUNTER': {
        'name': 'Resource Gathering',
        'description': 'Secondary income from hunting/gathering',
        'base_amount': 8,  # Per successful session
        'prerequisites': ['HAS_WEAPON'],
        'optimal_phase': 'MORNING'
    },
    'FARMER': {
        'name': 'Crop Production',
        'description': 'Long-term income from farming',
        'base_amount': 12,  # Per harvest cycle (seasonal)
        'prerequisites': ['HAS_SEEDS', 'HAS_PLOT'],
        'optimal_phase': 'MORNING'
    },
    'CRAFTSMAN': {
        'name': 'Artisan Production',
        'description': 'Income from crafting goods',
        'base_amount': 10,  # Per successful craft session
        'prerequisites': ['HAS_TOOLS'],
        'optimal_phase': 'AFTERNOON'
    },
}

# Expense Categories - predefined expense types
EXPENSE_CATEGORIES = {
    'FOOD': {
        'name': 'Food & Drink',
        'description': 'Basic sustenance needs',
        'base_cost': 25,  # Per meal (3 meals/day)
        'frequency': 'DAILY',
        'prerequisites': ['HAS_FOOD']  # Must have food in inventory
    },
    'SUPPLIES': {
        'name': 'General Supplies',
        'description': 'Tools, materials, miscellaneous supplies',
        'base_cost': 15,  # Per session when needed
        'frequency': 'WEEKLY',
        'prerequisites': []  # Can be purchased with income
    },
    'MAINTENANCE': {
        'name': 'Home Maintenance',
        'description': 'Upkeep costs for homes and property',
        'base_cost': 10,  # Per week per home
        'frequency': 'WEEKLY',
        'prerequisites': ['HAS_HOME']  # Must own a home
    },
}

__all__ = ['EconomyManager', 'INCOME_SOURCES', 'EXPENSE_CATEGORIES']
]

