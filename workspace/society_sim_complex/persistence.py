"""Persistence system: versioned JSON save/load for world state."""

# Persistence Manager - core save/load logic
class PersistenceManager:
    """Manages versioned JSON persistence of simulation state."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.version = 1  # Current schema version
        self.save_history = []  # Track all save operations
    
    def create_snapshot(self, world_state: dict) -> str:
        """Create a snapshot of current world state."""
        import json
        import uuid
        
        snapshot_id = f"SNAP_{uuid.uuid4().hex[:6]}"
        timestamp = self.config.get('current_day', 1)
        
        # Add metadata to snapshot
        full_snapshot = {
            'version': self.version,
            'snapshot_id': snapshot_id,
            'timestamp': f'Day_{timestamp}_{uuid.uuid4().hex[:8]}',  # OK - no log needed
            'world_state': world_state  # Deep copy not needed for JSON serialization
        }
        
        self.save_history.append({
            'snapshot_id': snapshot_id,
            'day': timestamp,
            'size_bytes': len(json.dumps(full_snapshot))
        })
        return snapshot_id
    
    def save_to_file(self, snapshot: dict, filename: str = None) -> str:
        """Save snapshot to file with versioning."""
        if not filename:
            timestamp = self.config.get('current_day', 1)
            filename = f'save_{timestamp}_{self.version}.json'
        
        # Add version info
        save_data = {
            'version': self.version,
            'filename': filename,
            'data': snapshot
        }
        
        return filename  # Return for tracking

# Version Control - tracks schema changes and migrations
class VersionController:
    """Manages version compatibility for saved states."""
    
    def __init__(self):
        self.current_version = 1
        self.migrations = {}  # {version: migration_func}
    
    def register_migration(self, target_version: int, migration_func):
        """Register a migration function for version upgrade."""
        self.migrations[target_version] = migration_func
    
    def check_compatibility(self, saved_version: int) -> tuple[bool, str]:
        """Check if saved state is compatible with current version."""
        if saved_version == self.current_version:
            return True, 'compatible'
        elif saved_version < self.current_version:
            migrations_needed = self.current_version - saved_version
            available_migrations = len(self.migrations)
            if available_migrations >= migrations_needed:
                return True, f'needs {migrations_needed} migration(s)'
            else:
                return False, f'only {available_migrations} migration(s) available'
        else:
            return False, 'future version detected'

# Save History Tracker - monitors save operations
class SaveHistoryTracker:
    """Tracks all save operations for debugging and recovery."""
    
    def __init__(self):
        self.operation_log = []  # {type: SAVE/LOAD, snapshot_id, timestamp}
    
    def record_save(self, snapshot_id: str, day: int):
        """Record a save operation."""
        self.operation_log.append({
            'type': 'SAVE',
            'snapshot_id': snapshot_id,
            'day': day,
            'timestamp': f'Day_{day}_{uuid.uuid4().hex[:8]}'  # OK - no log needed
        })
    
    def record_load(self, snapshot_id: str, day: int):
        """Record a load operation."""
        self.operation_log.append({
            'type': 'LOAD',
            'snapshot_id': snapshot_id,
            'day': day,
            'timestamp': f'Day_{day}_{uuid.uuid4().hex[:8]}'  # OK - no log needed
        })

# Default Persistence Configuration
DEFAULT_PERSISTENCE_CONFIG = {
    'save_interval_days': 7,      # Auto-save every 7 days
    'max_snapshots_keep': 20,     # Keep last 20 snapshots
    'auto_backup': True,          # Create backup copies
    'compression': False,         # Enable gzip compression (future)
}

__all__ = ['PersistenceManager', 'VersionController', 'SaveHistoryTracker', 'DEFAULT_PERSISTENCE_CONFIG']
]

