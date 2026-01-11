"""
Database backends module.

Provides pluggable backends for different database types:
- AccessBackend: MS Access via pyodbc
- SqliteBackend: SQLite (future)
- MemoryBackend: In-memory for testing (future)
"""

from src.backends.base import Backend
from src.backends.access import AccessBackend

__all__ = ['Backend', 'AccessBackend']
