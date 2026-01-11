"""
Media Service - handles file-related operations.

Includes:
- Path resolution (handling drive mapping)
- File existence checks
- Metadata loading (duration, bitrate)
- Future: File renaming and moving
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from src.services.vfs_service import VfsService
from src.services.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)

class MediaService:
    """
    Service for file and media operations.
    """
    
    def __init__(self, drive_map: Optional[Dict[str, str]] = None, 
                 base_path: Optional[str] = None, 
                 vfs_service: Optional[VfsService] = None,
                 snapshot_service: Optional[SnapshotService] = None):
        """
        Initialize media service.
        
        Args:
            drive_map: Dict mapping database drives to local drives (e.g. {"B:": "Z:"})
            base_path: Base path for songs if absolute paths aren't used
            vfs_service: Optional VfsService for offline mode
            snapshot_service: Optional SnapshotService for offline metadata
        """
        self.drive_map = {k.lower(): v for k, v in (drive_map or {}).items()}
        self.base_path = base_path
        self.vfs = vfs_service
        self.snapshot = snapshot_service
    
    def resolve_path(self, db_path: str) -> str:
        """
        Convert a database path to a local physical path using the drive map.
        
        Example:
            'B:\\Songs\\Rock\\Beatles.mp3' -> 'Z:\\Songs\\Rock\\Beatles.mp3'
        """
        if not db_path:
            return ""
        
        resolved = db_path
        
        # Apply drive mapping if present
        for remote_drive, local_drive in self.drive_map.items():
            if db_path.lower().startswith(remote_drive):
                resolved = local_drive + db_path[len(remote_drive):]
                break
                
        return resolved

    def exists(self, path: str) -> bool:
        """Check if a file exists on the local filesystem."""
        if not path:
            return False
        return os.path.exists(path)

    def get_file_info(self, db_path: str) -> dict:
        """
        Get info about a file (resolved path, existence, size, VFS status).
        """
        resolved = self.resolve_path(db_path)
        exists = self.exists(resolved)
        vfs_status = 'live' if exists else 'missing'
        
        if not exists and self.vfs:
            if self.vfs.exists(db_path) or self.vfs.exists(resolved):
                vfs_status = 'virtual'
        
        info = {
            "db_path": db_path,
            "resolved_path": resolved,
            "exists": exists,
            "vfs_status": vfs_status,
            "size_bytes": 0,
            "extension": "",
            "metadata": None
        }
        
        # Prefer physical metadata if exists, otherwise fallback to snapshot
        if exists:
            try:
                stats = os.stat(resolved)
                info["size_bytes"] = stats.st_size
                info["extension"] = os.path.splitext(resolved)[1].lower()
                # We could read ID3 here, but usually it's read selectively in the route
            except Exception as e:
                logger.warning(f"Could not get file stats for {resolved}: {e}")
        elif vfs_status == 'virtual' and self.snapshot:
            # Try to get cached info
            cached = self.snapshot.get_metadata(db_path) or self.snapshot.get_metadata(resolved)
            if cached:
                info["metadata"] = cached
                info["extension"] = os.path.splitext(resolved)[1].lower()
        
        return info
                
    def sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filenames."""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            filename = filename.replace(char, '_')
        return filename.strip()

    def rename_file(self, db_path: str, new_name_basis: str) -> Optional[str]:
        """
        Rename a physical file on disk and return the new DB-relative path.
        
        Args:
            db_path: Current path stored in database
            new_name_basis: The basis for new filename (e.g. "Artist - Title")
            
        Returns:
            The new database-relative path, or None if rename failed/skipped.
        """
        resolved_old = self.resolve_path(db_path)
        if not self.exists(resolved_old):
            logger.warning(f"Rename failed: Original file not found at {resolved_old}")
            return None
            
        old_path = Path(resolved_old)
        extension = old_path.suffix
        new_filename = self.sanitize_filename(new_name_basis) + extension
        
        # Create new full local path
        new_local_path = old_path.parent / new_filename
        
        # If names are already the same, skip
        if resolved_old.lower() == str(new_local_path).lower():
            return db_path
            
        try:
            # Perform rename
            logger.info(f"Renaming file: {resolved_old} -> {new_local_path}")
            os.rename(resolved_old, new_local_path)
            
            # Convert back to database-relative path
            # We reverse the drive mapping
            new_db_path = str(new_local_path)
            for remote_drive, local_drive in self.drive_map.items():
                if new_db_path.lower().startswith(local_drive.lower()):
                    new_db_path = remote_drive + new_db_path[len(local_drive):]
                    break
            
            return new_db_path
        except Exception as e:
            logger.error(f"Rename failed: {e}")
            return None

    def scan_files(self) -> list[str]:
        """
        Recursively scan base_path for MP3 files.
        Returns list of absolute paths.
        """
        files = []
        if not self.base_path or not os.path.exists(self.base_path):
            logger.warning(f"Cannot scan: Base path not found: {self.base_path}")
            return []
            
        try:
            for root, _, filenames in os.walk(self.base_path):
                for f in filenames:
                    if f.lower().endswith('.mp3'):
                        files.append(os.path.join(root, f))
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            
        return files
