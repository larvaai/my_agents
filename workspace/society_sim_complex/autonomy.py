"""Autonomy planner: decision-making and action selection engine."""

# Autonomy Planner - core decision logic
class AutonomyPlanner:
    """Decides which actions to take based on needs, priorities, and constraints."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.decision_log = []
    
    def assess_needs(self, actor: dict) -> list:
        """Assess what the actor needs most urgently."""
        needs = []
        
        # Energy need (most critical)
        if 'current_energy' in actor and 'max_energy' in actor:
            energy_pct = actor['current_energy'] / actor['max_energy'] * 100
            if energy_pct < 30:
                needs.append(('ENERGY_CRITICAL', 5))
            elif energy_pct < 60:
                needs.append(('ENERGY_LOW', 4))
            else:
                needs.append(('ENERGY_OK', 2))
        
        # Resource need (food, supplies)
        if 'inventory' in actor and 'needs' in self.config:
            for res_type, threshold in self.config['needs'].items():
                current = actor['inventory'].get(res_type, 0)
                if current < threshold * 0.3:  # Below 30% of threshold
                    needs.append(('RESOURCE_' + res_type.upper(), 4))
        
        # Relationship need (social interaction)
        if 'relationships' in actor:
            avg_rel = sum(actor['relationships'].values()) / len(actor['relationships']) if actor['relationships'] else 0
            if avg_rel < 20:
                needs.append(('RELATIONSHIP_LOW', 3))
        
        # Time-based need (optimal phases)
        current_phase = self._get_current_phase()
        for action_name, action_info in ACTION_PHASES.items():
            if action_info['optimal_phase'] == current_phase:
                needs.append((f'PHASE_OPTIMAL_{action_name}', 1))
        
        return sorted(needs, key=lambda x: -x[1])  # Sort by priority (descending)
    
    def _get_current_phase(self) -> str:
        """Determine current time-of-day phase."""
        hour = self.config.get('current_hour', 8)  # Default morning
        if 5 <= hour < 12:
            return 'MORNING'
        elif 12 <= hour < 17:
            return 'AFTERNOON'
        else:
            return 'EVENING'
    
    def select_action(self, needs: list, available_actions: list) -> tuple[str, dict]:
        """Select the best action based on current needs."""
        if not available_actions:
            self.decision_log.append({'action': None, 'reason': 'no actions available'})
            return None, {'reason': 'no actions'}
        
        # Score each action against current needs
        best_action = None
        best_score = -999
        
        for action_name in available_actions:
            if action_name not in ACTION_REGISTRY:
                continue
            
            action_info = ACTION_REGISTRY[action_name]
            score = 0
            
            # Boost actions that match high-priority needs
            for need_type, priority in needs[:3]:  # Top 3 needs only
                if 'ENERGY' in need_type and action_info['energy_cost'] <= 20:
                    score += priority * 2  # Low-cost energy recovery preferred
                elif 'RESOURCE_' in need_type and action_name == 'EAT':
                    score += priority * 3  # Food is critical
                elif 'PHASE_OPTIMAL' in need_type and action_info['optimal_phase'] == self._get_current_phase():
                    score += priority
            
            # Base scoring from action type priorities
            if action_name == 'WORK':
                score += 10  # Primary income source
            elif action_name in ['SLEEP', 'RELAX']:
                score += 5  # Recovery actions
            elif action_name in ['HUNTER', 'FARMER']:
                score += 3  # Secondary income
            
            if score > best_score:
                best_score = score
                best_action = action_name
        
        self.decision_log.append({
            'action': best_action,
            'score': best_score,
            'top_needs': [n[0] for n in needs[:3]]  # Top 3 needs
        })
        
        return best_action, {'reason': f'score={best_score}, top_need={needs[0][0] if needs else "none"}'}

# Action Phase Registry - time-of-day aware action availability
ACTION_PHASES = {
    'WORK': {'optimal_phase': 'MORNING'},
    'COMMUTE': {'optimal_phase': 'ANY'},
    'EAT': {'optimal_phase': 'ANY'},
    'SLEEP': {'optimal_phase': 'EVENING'},
    'RELAX': {'optimal_phase': 'AFTERNOON'},
    'HUNTER': {'optimal_phase': 'MORNING'},
    'FARMER': {'optimal_phase': 'MORNING'},
    'CRAFTSMAN': {'optimal_phase': 'AFTERNOON'},
}

__all__ = ['AutonomyPlanner', 'ACTION_PHASES']
]

