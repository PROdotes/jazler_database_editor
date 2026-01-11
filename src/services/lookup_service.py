"""
Lookup Service - Generic service for managing reference/lookup tables.
Handles simple lookups (Genre, Decade) AND complex entities (Artist).
"""

import logging
from typing import Dict, Any, List, Optional
from src.backends.base import Backend
from src.core.schema.registry import SchemaRegistry
from src.core.models.record import Record

logger = logging.getLogger(__name__)

class LookupService:
    """
    Generic service for lookup table operations.
    Supports reading, searching, creating, and merging entries.
    """
    
    def __init__(self, backend: Backend, registry: SchemaRegistry):
        self.backend = backend
        self.registry = registry

    def _get_table_def(self, table_name: str):
        return self.registry.get_table(table_name)

    def get_all(self, table_name: str, sort_field: str = None) -> List[Record]:
        """Get all entries from a lookup table."""
        try:
            rows = self.backend.fetch(table_name, limit=10000)
            records = [Record(row, self._get_table_def(table_name)) for row in rows]
            
            if sort_field:
                records.sort(key=lambda x: str(x.get(sort_field, '')).lower())
            
            return records
        except Exception as e:
            logger.error(f"Failed to fetch lookups for {table_name}: {e}")
            return []

    def get_by_id(self, table_name: str, pk_value: int) -> Optional[Record]:
        """Get a single lookup entry."""
        if not pk_value: return None
        
        table_def = self._get_table_def(table_name)
        pk_col = table_def.primary_key if table_def else "AUID"
        
        row = self.backend.fetch_one(
            table_name, 
            pk_value, 
            primary_key_column=pk_col
        )
        return Record(row, table_def) if row else None

    def search(self, table_name: str, field: str, query: str) -> List[Record]:
        """Search for lookup entries."""
        try:
            rows = self.backend.search(table_name, field, query, "contains")
            return [Record(row, self._get_table_def(table_name)) for row in rows]
        except Exception as e:
            logger.error(f"Search failed for {table_name}: {e}")
            return []

    def create(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new lookup entry.
        Returns the new ID if successful.
        """
        try:
            # Backend insert not yet fully unified, assuming Access backend 'insert' method exists
            # or extending backend interface. For now, we need to check backend capabilities.
            if hasattr(self.backend, 'insert'):
                 return self.backend.insert(table_name, data)
            else:
                logger.error("Backend does not support INSERT yet")
                return None
        except Exception as e:
            logger.error(f"Create failed for {table_name}: {e}")
            return None

    def update(self, table_name: str, pk_value: int, data: Dict[str, Any]) -> bool:
        """Update a lookup entry."""
        table_def = self._get_table_def(table_name)
        pk_col = table_def.primary_key if table_def else "AUID"
        return self.backend.update(table_name, pk_value, data, primary_key_column=pk_col)

    def delete(self, table_name: str, pk_value: int) -> bool:
        """
        Delete a lookup entry.
        WARNING: Does not check for orphans (songs still using this ID).
        Client must verify usage before calling.
        """
        table_def = self._get_table_def(table_name)
        pk_col = table_def.primary_key if table_def else "AUID"
        
        # We need a delete method on backend
        if hasattr(self.backend, 'delete'):
            return self.backend.delete(table_name, pk_value, primary_key_column=pk_col)
        return False
