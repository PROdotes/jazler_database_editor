"""
Snapshot Service - Handles indexing of ID3 tags for offline use.
Uses ThreadPoolExecutor for high-speed parallel scanning.
"""

import os
import json
import logging
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

class SnapshotService:
    """
    Service to generate and manage metadata snapshots of the music library.
    """
    
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}

    def load_cache(self) -> bool:
        """Loads the metadata cache from disk."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.metadata_cache = json.load(f)
                logger.info(f"Loaded {len(self.metadata_cache)} entries from snapshot cache.")
                return True
            except Exception as e:
                logger.error(f"Failed to load snapshot cache: {e}")
        return False

    def save_cache(self):
        """Saves current metadata cache to disk."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_cache, f, indent=2)
            logger.info(f"Saved snapshot cache to {self.cache_path}")
        except Exception as e:
            logger.error(f"Failed to save snapshot cache: {e}")

    def _read_file_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Reads ID3 tags and tech info from a single file."""
        try:
            audio = MP3(filepath, ID3=EasyID3)
            
            def get_tag(key):
                val = audio.get(key)
                return val[0] if val else None

            return {
                'artist': get_tag('artist'),
                'title': get_tag('title'),
                'album': get_tag('album'),
                'year': get_tag('date'),
                'genre': get_tag('genre'),
                'duration': audio.info.length,
                'bitrate': audio.info.bitrate // 1000,
                'sample_rate': audio.info.sample_rate
            }
        except Exception:
            # Silently skip files we can't read
            return None

    def generate_snapshot(self, folder_paths: List[str], max_workers: int = 20):
        """
        Scans folders and builds a metadata snapshot in parallel.
        
        Args:
            folder_paths: List of local folder paths to scan
            max_workers: Number of parallel threads
        """
        all_files = []
        for folder in folder_paths:
            path = Path(folder)
            if path.exists():
                logger.info(f"Indexing files in {folder}...")
                all_files.extend([str(f) for f in path.rglob('*.mp3')])

        total_files = len(all_files)
        logger.info(f"Found {total_files} MP3s. Starting parallel metadata scan...")

        results_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map paths to futures
            future_to_path = {executor.submit(self._read_file_metadata, p): p for p in all_files}
            
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    metadata = future.result()
                    if metadata:
                        # Store by lowercase path for easy lookup
                        self.metadata_cache[path.lower()] = metadata
                        results_count += 1
                        
                        if results_count % 1000 == 0:
                            logger.info(f"Scanned {results_count}/{total_files} files...")
                except Exception as e:
                    logger.error(f"Error scanning {path}: {e}")

        logger.info(f"Finished. Snapshot contains {len(self.metadata_cache)} files.")
        self.save_cache()

    def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Lookup metadata for a specific path in the cache."""
        return self.metadata_cache.get(path.lower())
