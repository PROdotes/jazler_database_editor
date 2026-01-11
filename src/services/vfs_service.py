"""
VFS (Virtual File System) Service.
Handles offline file visibility by parsing log files (e.g. log.txt).
"""

import os
import re
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)

class VfsService:
    """
    Virtual File System service that simulates file existence 
    based on a snapshot log file.
    """
    
    def __init__(self, log_path: Optional[str] = None):
        self.files: Set[str] = set()
        self.is_active = False
        
        if log_path and os.path.exists(log_path):
            self.load_log(log_path)

    def load_log(self, log_path: str) -> bool:
        """
        Parses a PowerShell 'dir' style log file and builds a set of full paths.
        Supports both 'FullName' format and table format.
        """
        try:
            current_dir = ""
            count = 0
            
            # Patterns
            # Matches: "    Directory: B:\songs"
            dir_pattern = re.compile(r"^\s*Directory:\s*(.*)$", re.IGNORECASE)
            # Matches: "-a----  29/10/2025  14:28  5483047  Filename.mp3"
            # We look for the attribute string at the start
            file_pattern = re.compile(r"^[da-]{5,6}\s+")
            
            with open(log_path, 'r', encoding='utf-16' if self._is_utf16(log_path) else 'utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for directory header
                    dir_match = dir_pattern.match(line)
                    if dir_match:
                        current_dir = dir_match.group(1).strip()
                        continue
                    
                    # Check for file line (table format)
                    if file_pattern.match(line):
                        # The filename is at the end. Table layout is tricky but usually:
                        # Attributes, Date, Time, Length, Name
                        parts = line.split(maxsplit=4)
                        if len(parts) >= 5:
                            filename = parts[4]
                            if current_dir:
                                full_path = os.path.join(current_dir, filename)
                                self.files.add(full_path.lower())
                                count += 1
                        continue

                    # Fallback: Assume it's a flat list of FullNames if no table structure found
                    if os.path.isabs(line) or line.startswith('\\\\'):
                         self.files.add(line.lower())
                         count += 1

            logger.info(f"VFS loaded {count} entries from {log_path}")
            self.is_active = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load VFS log: {e}")
            return False

    def _is_utf16(self, path: str) -> bool:
        """Check if file is UTF-16 (common for PowerShell redirects)."""
        try:
            with open(path, 'rb') as f:
                header = f.read(2)
                return header in (b'\xff\xfe', b'\xfe\xff')
        except:
            return False

    def exists(self, path: str) -> bool:
        """Check if a path exists in the virtual snapshot."""
        if not path:
            return False
        return path.lower() in self.files

    def get_status(self, path: str, physically_exists: bool) -> str:
        """
        Get visual status for a path.
        Returns: 'live', 'virtual', or 'missing'
        """
        if physically_exists:
            return 'live'
        if self.exists(path):
            return 'virtual'
        return 'missing'
