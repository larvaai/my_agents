"""
Basal Ganglia Module - Motor control and habit formation.
The basal ganglia are involved in motor learning, procedural memory,
habit formation, and action selection.
"""

import random

class BasalGanglia:
    def __init__(self):
        self.name = "Basal Ganglia"
        self.habit_strength = 0.5  # 0-1 scale of habit strength
        self.connections = []
        
    def process_input(self, input_signal):
        """
        Process motor and procedural learning inputs.
        Handles action selection and reinforcement learning aspects.
        """
        if not isinstance(input_signal, dict):
            input_signal = {"signal": input_signal}
            
        signal_type = input_signal.get("type", "motor")
        signal_strength = input_signal.get("strength", 0.5)
        
        # Basal ganglia shows habit-like behavior - performance improves with repetition
        if signal_type == "procedural":
            # Procedural learning: performance increases over time (simulated by strength)
            procedural_efficiency = min(signal_strength * 1.4, 1.0)
            return {
                "module": self.name,
                "output_type": "procedural_memory",
                "value": procedural_efficiency,
                "latency_ms": 20,
                "description": "Action selection based on learned procedures"
            }
        elif signal_type == "habit":
            # Habit execution: faster and more automatic
            habit_efficiency = min(signal_strength * 1.5 + self.habit_strength, 1.0)
            return {
                "module": self.name,
                "output_type": "habit_response",
                "value": habit_efficiency,
                "latency_ms": 12,  # Very fast - automatic
                "description": "Automatic response based on established habits"
            }
        else:
            return {
                "module": self.name,
                "output_type": "motor_control",
                "value": signal_strength * 0.9,
                "latency_ms": 18
            }
    
    def generate_output(self):
        """
        Generate spontaneous motor or procedural output.
        """
        return {
            "module": self.name,
            "output_type": "spontaneous",
            "value": random.uniform(0.3, 0.7),
            "description": "Motor planning or habit activation event"
        }
    
    def connect_to(self, target_module):
        """Establish connection to another module."""
        self.connections.append(target_module)
        return self
