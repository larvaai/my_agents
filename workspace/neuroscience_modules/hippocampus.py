"""
Hippocampus Module - Handles memory formation and spatial navigation.
The hippocampus is crucial for episodic memory, declarative memory consolidation,
and spatial mapping.
"""

import random

class Hippocampus:
    def __init__(self):
        self.name = "Hippocampus"
        self.memory_capacity = 100.0  # Units of information storage
        self.current_load = 0.0
        self.connections = []
        
    def process_input(self, input_signal):
        """
        Process memory-related or spatial input signals.
        Handles encoding and retrieval operations.
        """
        if not isinstance(input_signal, dict):
            input_signal = {"signal": input_signal}
            
        signal_type = input_signal.get("type", "memory")
        signal_strength = input_signal.get("strength", 0.5)
        
        # Hippocampus excels at pattern separation (distinguishing similar inputs)
        if signal_type == "encoding":
            encoding_efficiency = min(signal_strength * 1.2, 1.0)
            new_load = self.current_load + (signal_strength * 0.3)
            
            return {
                "module": self.name,
                "output_type": "memory_trace",
                "value": encoding_efficiency,
                "latency_ms": 25,
                "new_memory_load": new_load
            }
        elif signal_type == "retrieval":
            # Retrieval is more efficient when load is moderate (not too full, not empty)
            optimal_load = 0.4
            retrieval_efficiency = abs(optimal_load - self.current_load) / 0.6 + 0.5
            return {
                "module": self.name,
                "output_type": "retrieved_memory",
                "value": min(retrieval_efficiency, 1.0),
                "latency_ms": 30
            }
        else:
            # Default spatial processing
            return {
                "module": self.name,
                "output_type": "spatial_map",
                "value": signal_strength * 0.8,
                "latency_ms": 20
            }
    
    def generate_output(self):
        """
        Generate spontaneous spatial or memory-related output.
        """
        return {
            "module": self.name,
            "output_type": "spontaneous",
            "value": random.uniform(0.2, 0.6),
            "description": "Spatial awareness or memory consolidation event"
        }
    
    def connect_to(self, target_module):
        """Establish connection to another module."""
        self.connections.append(target_module)
        return self
