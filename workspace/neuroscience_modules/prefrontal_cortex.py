"""
Prefrontal Cortex Module - Executive functions and decision-making.
The prefrontal cortex is the seat of executive functions including working memory,
cognitive flexibility, impulse control, and complex decision-making under uncertainty.
"""

import random

class PrefrontalCortex:
    def __init__(self):
        self.name = "Prefrontal Cortex"
        self.working_memory_capacity = 7.0  # Miller's magic number approximation
        self.current_working_memory = 0.0
        self.connections = []
        
    def process_input(self, input_signal):
        """
        Process complex cognitive and decision-making inputs.
        Handles working memory operations and executive control.
        """
        if not isinstance(input_signal, dict):
            input_signal = {"signal": input_signal}
            
        signal_type = input_signal.get("type", "executive")
        signal_strength = input_signal.get("strength", 0.5)
        
        # Prefrontal cortex has optimal performance at moderate loads
        if self.current_working_memory < 3.0:
            efficiency = min(signal_strength * 1.3, 1.0)
        elif self.current_working_memory > 5.0:
            efficiency = signal_strength * 0.7  # Overload reduces efficiency
        else:
            efficiency = signal_strength * 1.1
            
        # Update working memory load
        new_load = min(self.current_working_memory + (signal_strength * 0.2), 7.0)
        self.current_working_memory = new_load
        
        return {
            "module": self.name,
            "output_type": "executive_decision",
            "value": efficiency,
            "latency_ms": 45,  # Slower but more deliberate processing
            "working_memory_used": new_load
        }
    
    def generate_output(self):
        """
        Generate spontaneous executive output (e.g., planning, goal-setting).
        """
        return {
            "module": self.name,
            "output_type": "spontaneous",
            "value": random.uniform(0.4, 0.8),
            "description": "Executive function event (planning/goal adjustment)"
        }
    
    def connect_to(self, target_module):
        """Establish connection to another module."""
        self.connections.append(target_module)
        return self
