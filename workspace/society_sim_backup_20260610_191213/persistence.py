#!/usr/bin/env python
"""Persistence layer for society_sim."""
import json

def save_world(world, path: str) -> None:
    """Save world state to JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(world, f, indent=2)

def load_world(path: str) -> dict:
    """Load world state from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)