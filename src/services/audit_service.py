"""
Audit Service - Cross-references database records with filesystem snapshots.
Detects moved vs deleted files.
"""

import os
import re
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AuditService:
    """
    Handles auditing of the music library to find discrepancies 
    between the database and physical (or virtual) files.
    """
    
    def __init__(self, song_service, vfs_service, media_service, config: Optional[Dict] = None):
        self.song_service = song_service
        self.vfs = vfs_service
        self.media = media_service
        self.config = config or {}
        self.ignore_drive = self.config.get('audit_ignore_drive_letters', False)
        
    def _normalize_string(self, s: str) -> str:
        if not s: return ""
        s = s.lower()
        s = re.sub(r'[^a-z0-9]', '', s)
        return s

    def _normalize_path(self, path: str) -> str:
        if not path: return ""
        p = path.lower().replace('/', '\\').strip()
        
        # Strip drive letter if configured (e.g. "z:\" -> "\")
        if self.ignore_drive and ':' in p[:2]:
            p = p[2:]
            
        p = p.replace(".mp3.mp3", ".mp3")
        p = re.sub(r'\s+', ' ', p)
        return p

    def run_audit(self) -> Dict[str, Any]:
        """
        Runs a full library audit.
        Returns a dictionary with 'ok', 'moved', and 'missing' lists.
        """
        logger.info("Starting library audit...")
        
        # 1. Get all songs from DB
        songs = self.song_service.get_all()
        total_songs = len(songs)
        
        # 2. Build filename map from VFS/VfsEntries
        # If we have a massive log, this helps pinpoint "moved" files
        name_map = defaultdict(list)
        if self.vfs and self.vfs.is_active:
            for full_path in self.vfs.files:
                filename = os.path.basename(full_path)
                norm_name = self._normalize_string(filename)
                name_map[norm_name].append(full_path)
        
        results = {
            "total": total_songs,
            "found": 0,
            "virtual": 0,
            "moved": [],
            "missing": []
        }
        
        for song in songs:
            db_path = song.filename
            if not db_path:
                continue
                
            file_info = self.media.get_file_info(db_path)
            
            if file_info['exists']:
                results['found'] += 1
                continue
                
            if file_info['vfs_status'] == 'virtual':
                results['virtual'] += 1
                # Even if virtual, it's "in place" relative to the log
                continue

            # It's missing from both disk and the log's exact path.
            # Let's see if it moved (exists in log elsewhere).
            filename = os.path.basename(db_path)
            norm_name = self._normalize_string(filename)
            potential_paths = name_map.get(norm_name, [])
            
            song_data = {
                'id': song.id,
                'artist': song.artist,
                'title': song.title,
                'db_path': db_path,
                'resolved_path': file_info['resolved_path']
            }
            
            if potential_paths:
                song_data['new_paths'] = potential_paths
                results['moved'].append(song_data)
            else:
                results['missing'].append(song_data)

        logger.info(f"Audit complete: {results['found']} found, {results['virtual']} virtual, {len(results['moved'])} moved, {len(results['missing'])} missing.")
        return results

    def find_untracked_files(self) -> List[str]:
        """
        Find files on disk (or VFS log) that are NOT in the database.
        Returns a list of untracked file paths.
        """
        logger.info("Starting untracked files scan...")
        
        # 1. Get all DB paths
        # Normalize them to what we expect on disk (e.g. resolve drive mappings)
        db_paths_raw = self.song_service.get_all_paths()
        normalized_db_paths = set()
        
        for p in db_paths_raw:
            # Convert B:\... -> Z:\...
            local_p = self.media.resolve_path(p)
            # Normalize for comparison
            normalized_db_paths.add(self._normalize_path(local_p))
            
        # 2. Get all FS paths
        fs_paths = []
        if self.vfs and self.vfs.is_active:
            fs_paths = list(self.vfs.files) # already absolute, maybe lowercased
        else:
            fs_paths = self.media.scan_files()
            
        # 3. Compare
        untracked = []
        for p in fs_paths:
            # normalize for comparison
            norm_p = self._normalize_path(p)
            if norm_p not in normalized_db_paths:
                untracked.append(p)
                
        logger.info(f"Found {len(untracked)} untracked files.")
        
        # Sort for display
        return sorted(untracked)
