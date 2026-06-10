#!/usr/bin/env python
"""Minimal JSON Schema Validator - Standard Library Only"""
import json
import sys

def validate_schema(path):
    """Validate schema syntax and structure."""
    errors = []
    warnings = []
    
    # 1. Parse as valid JSON
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"JSON Syntax Error: {e}"]
    
    # 2. Check required Draft-04 fields
    required_keys = ['$schema', 'id', 'description', 'type']
    for key in required_keys:
        if key not in data:
            warnings.append(f"Missing recommended field: {key}")
    
    # 3. Verify structure
    if data.get('type') != 'object':
        errors.append("Root type must be 'object'")
    
    props = data.get('properties', {})
    for prop_name, prop_def in props.items():
        if 'type' not in prop_def:
            warnings.append(f"Property '{prop_name}' missing 'type' field")
        elif prop_def['type'] == 'string':
            # Check if numeric data is incorrectly typed as string
            if any(kw in prop_name for kw in ['duration', 'sampleRate', 'Width', 'Length']):
                warnings.append(f"Property '{prop_name}' may be better as number/integer")
    
    required = data.get('required', [])
    if not required:
        warnings.append("No 'required' array - fields are optional by default")
    
    return errors, warnings

if __name__ == '__main__':
    schema_path = sys.argv[1] if len(sys.argv) > 1 else 'schemas/video_metadata_schema.json'
    errors, warnings = validate_schema(schema_path)
    
    print("=== VALIDATION RESULTS ===")
    for e in errors:
        print(f"ERROR: {e}")
    for w in warnings:
        print(f"WARNING: {w}")
    if not errors and not warnings:
        print("Schema is valid!")
