"""
Sync Service - Manages offline change queuing and synchronization.
Allows users to "save" changes locally when the database is unreachable or read-only.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SyncService:
    """
    Handles queuing of database changes and their eventual application.
    """
    
    def __init__(self, queue_path: str):
        self.queue_path = queue_path
        self.pending_changes: Dict[str, Dict[str, Any]] = {}
        self.load_queue()

    def load_queue(self):
        """Loads pending changes from disk."""
        if os.path.exists(self.queue_path):
            try:
                with open(self.queue_path, 'r', encoding='utf-8') as f:
                    self.pending_changes = json.load(f)
                logger.info(f"Loaded {len(self.pending_changes)} pending changes.")
            except Exception as e:
                logger.error(f"Failed to load sync queue: {e}")

    def save_queue(self):
        """Saves current pending changes to disk."""
        try:
            with open(self.queue_path, 'w', encoding='utf-8') as f:
                json.dump(self.pending_changes, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sync queue: {e}")

    def queue_change(self, song_id: int, artist: str, title: str, changes: Dict[str, Any]):
        """
        Adds or updates a change in the queue.
        
        Args:
            song_id: Database ID of the song
            artist: Current artist (for display in sync list)
            title: Current title (for display in sync list)
            changes: Dict of field -> new_value
        """
        sid = str(song_id)
        
        if sid not in self.pending_changes:
            self.pending_changes[sid] = {
                'id': song_id,
                'artist': artist,
                'title': title,
                'timestamp': datetime.datetime.now().isoformat(),
                'fields': {}
            }
        
        # Merge changes
        self.pending_changes[sid]['fields'].update(changes)
        self.pending_changes[sid]['timestamp'] = datetime.datetime.now().isoformat()
        
        self.save_queue()
        logger.info(f"Queued {len(changes)} changes for song #{song_id}")

    def get_pending(self) -> List[Dict[str, Any]]:
        """Returns a list of all pending changes for UI display."""
        return sorted(self.pending_changes.values(), key=lambda x: x['timestamp'], reverse=True)

    def remove_change(self, song_id: int):
        """Removes a change from the queue."""
        sid = str(song_id)
        if sid in self.pending_changes:
            del self.pending_changes[sid]
            self.save_queue()

    def clear(self):
        """Clears the entire queue."""
        self.pending_changes = {}
        if os.path.exists(self.queue_path):
            os.remove(self.queue_path)
        logger.info("Sync queue cleared.")

    def count(self) -> int:
        """Returns the number of pending songs."""
        return len(self.pending_changes)
