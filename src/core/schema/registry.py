"""
Schema registry - combines discovered schema with user overrides.

Loads schema overrides from JSON and merges with auto-discovered schema.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List

import logging
from src.backends.base import Backend

logger = logging.getLogger(__name__)
from src.core.schema.definition import TableDefinition, FieldDefinition
from src.core.schema.discovery import SchemaDiscovery


class SchemaRegistry:
    """
    Central registry for database schema information.
    
    Combines auto-discovered schema with user-configured overrides
    (ignored tables, display names, etc.)
    
    Usage:
        registry = SchemaRegistry.from_config("config/schema_overrides.json")
        registry.load(backend)
        table = registry.get_table("snDatabase")
    """
    
    def __init__(self, overrides: Optional[Dict] = None):
        """
        Initialize registry with optional overrides.
        
        Args:
            overrides: Dict with ignored_tables, display_names, etc.
        """
        self.overrides = overrides or {}
        self._tables: Dict[str, TableDefinition] = {}
        self._discovery = SchemaDiscovery()
    
    @classmethod
    def from_config(cls, config_path: str) -> 'SchemaRegistry':
        """
        Create registry from a JSON config file.
        
        Args:
            config_path: Path to schema_overrides.json
            
        Returns:
            Configured SchemaRegistry instance
        """
        path = Path(config_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                overrides = json.load(f)
        else:
            overrides = {}
        
        return cls(overrides)
    
    def load(self, backend: Backend) -> None:
        """
        Load schema from a backend, applying overrides.
        
        Args:
            backend: Connected database backend
        """
        # Discover raw schema
        raw_tables = self._discovery.probe(backend)
        
        # Apply overrides
        ignored_tables = set(self.overrides.get('ignored_tables', []))
        primary_keys = self.overrides.get('primary_keys', {})
        display_names = self.overrides.get('display_names', {})
        ignored_columns = self.overrides.get('ignored_columns', {})
        lookup_tables = self.overrides.get('lookup_tables', {})
        
        for table_name, table_def in raw_tables.items():
            # Skip ignored tables
            if table_name in ignored_tables:
                table_def.is_ignored = True
            
            # Override primary key if specified
            if table_name in primary_keys:
                table_def.primary_key = primary_keys[table_name]
                # Update the column's is_primary_key flag
                for col in table_def.columns:
                    col.is_primary_key = (col.name == table_def.primary_key)
            
            # Apply display names
            table_display_names = display_names.get(table_name, {})
            for col in table_def.columns:
                if col.name in table_display_names:
                    col.display_name = table_display_names[col.name]
            
            # Mark ignored columns
            # Case-insensitive lookup
            table_ignored = []
            for t_name, cols in ignored_columns.items():
                if t_name.lower() == table_name.lower():
                    table_ignored = cols
                    break
            
            if table_ignored:
                logger.info(f"Ignoring columns for {table_name}: {table_ignored}")
                
            for col in table_def.columns:
                if col.name in table_ignored:
                    col.is_ignored = True
            
            # Mark lookup tables
            if table_name in lookup_tables:
                table_def.is_lookup = True
            
            self._tables[table_name] = table_def
        
        # Apply new 'tables' configuration structure
        tables_config = self.overrides.get('tables', {})
        for table_name, config in tables_config.items():
            if table_name in self._tables:
                table = self._tables[table_name]
                if 'display_name' in config:
                    table.display_name = config['display_name']
                if 'is_lookup' in config:
                    table.is_lookup = config.get('is_lookup', False)
                if 'lookup_config' in config:
                    table.lookup_config = config['lookup_config']
    
    def get_table(self, name: str) -> Optional[TableDefinition]:
        """Get a table definition by name."""
        return self._tables.get(name)
    
    def get_tables(self, include_ignored: bool = False) -> List[TableDefinition]:
        """
        Get all table definitions.
        
        Args:
            include_ignored: Whether to include ignored tables
            
        Returns:
            List of TableDefinition objects
        """
        tables = list(self._tables.values())
        if not include_ignored:
            tables = [t for t in tables if not t.is_ignored]
        return tables
    
    def get_table_names(self, include_ignored: bool = False) -> List[str]:
        """Get list of table names."""
        return [t.name for t in self.get_tables(include_ignored)]
    
    def get_lookup_tables(self) -> List[TableDefinition]:
        """Get all lookup/category tables."""
        return [t for t in self._tables.values() if t.is_lookup]
    
    def get_data_tables(self) -> List[TableDefinition]:
        """Get all non-lookup, non-ignored tables."""
        return [t for t in self._tables.values() 
                if not t.is_lookup and not t.is_ignored]
    
    def get_lookup_config(self, table_name: str) -> Optional[Dict]:
        """Get lookup table configuration."""
        # Check TableDefinition first (new style)
        table = self.get_table(table_name)
        if table and table.lookup_config:
            return table.lookup_config
            
        # Fallback to legacy structure
        return self.overrides.get('lookup_tables', {}).get(table_name)

    def get_grid_view(self, view_name: str = 'default') -> List[str]:
        """
        Get list of column names for a specific grid view.
        Returns default view if view_name not found.
        """
        views = self.overrides.get('grid_views', {})
        return views.get(view_name) or views.get('default', [])

    def get_available_views(self) -> List[str]:
        """Get names of all available grid views."""
        return list(self.overrides.get('grid_views', {}).keys())
