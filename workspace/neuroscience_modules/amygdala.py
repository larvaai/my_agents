"""
Amygdala Module - Processes emotional and threat-related information.
The amygdala is involved in fear conditioning, emotional memory, and decision-making under uncertainty.
"""

import random

class Amygdala:
    def __init__(self):
        self.name = "Amygdala"
        self.activity_level = 0.5  # Baseline activity (0-1)
        self.connections = []
        
    def process_input(self, input_signal):
        """
        Process emotional/threat-related input signals.
        Returns processed output with emotional context.
        """
        if not isinstance(input_signal, dict):
            input_signal = {"signal": input_signal}
            
        signal_strength = input_signal.get("signal", 0)
        # Amygdala amplifies threat-related signals
        amplified = min(signal_strength * 1.5 + random.uniform(-0.2, 0.2), 1.0)
        return {
            "module": self.name,
            "output_type": "emotional_context",
            "value": amplified,
            "latency_ms": 15
        }
    
    def generate_output(self):
        """
        Generate spontaneous emotional output (e.g., fear response).
        """
        return {
            "module": self.name,
            "output_type": "spontaneous",
            "value": random.uniform(0.3, 0.7),
            "description": "Baseline emotional state"
        }
    
    def connect_to(self, target_module):
        """Establish connection to another module."""
        self.connections.append(target_module)
        return self
