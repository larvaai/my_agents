"""
Cerebellum Module - Motor coordination and timing.
The cerebellum is responsible for fine-tuning movements, motor learning,
timing, and increasingly recognized roles in cognitive functions like
attention, language processing, and working memory.
"""

import random

class Cerebellum:
    def __init__(self):
        self.name = "Cerebellum"
        self.coordination_level = 0.5  # 0-1 scale of motor coordination
        self.connections = []
        
    def process_input(self, input_signal):
        """
        Process motor coordination and timing inputs.
        Handles fine-tuning and predictive control aspects.
        """
        if not isinstance(input_signal, dict):
            input_signal = {"signal": input_signal}
            
        signal_type = input_signal.get("type", "coordination")
        signal_strength = input_signal.get("strength", 0.5)
        
        # Cerebellum excels at predictive control and fine-tuning
        if signal_type == "fine_tune":
            # Fine-tuning: improves with practice (simulated by strength)
            fine_tune_efficiency = min(signal_strength * 1.35, 1.0)
            return {
                "module": self.name,
                "output_type": "fine_tuned_output",
                "value": fine_tune_efficiency,
                "latency_ms": 8,  # Very fast - predictive control
                "description": "Predictive motor adjustment or timing correction"
            }
        elif signal_type == "timing":
            # Timing: cerebellum is exceptional at millisecond-level precision
            timing_efficiency = min(signal_strength * 1.45, 1.0)
            return {
                "module": self.name,
                "output_type": "temporal_control",
                "value": timing_efficiency,
                "latency_ms": 6,  # Fastest - precise timing
                "description": "Millisecond-level temporal coordination"
            }
        else:
            return {
                "module": self.name,
                "output_type": "motor_coordination",
                "value": signal_strength * 0.95,
                "latency_ms": 14
            }
    
    def generate_output(self):
        """
        Generate spontaneous coordination or timing output.
        """
        return {
            "module": self.name,
            "output_type": "spontaneous",
            "value": random.uniform(0.25, 0.65),
            "description": "Motor learning event or timing adjustment"
        }
    
    def connect_to(self, target_module):
        """Establish connection to another module."""
        self.connections.append(target_module)
        return self
