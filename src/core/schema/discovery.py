"""
Schema discovery - auto-probe database structure.

Introspects a database backend to discover tables and columns.
"""

from typing import Dict
from src.backends.base import Backend
from src.core.schema.definition import TableDefinition, FieldDefinition


class SchemaDiscovery:
    """
    Auto-discover schema from a database backend.
    
    Usage:
        discovery = SchemaDiscovery()
        schemas = discovery.probe(backend)
        # schemas is Dict[table_name, TableDefinition]
    """
    
    def probe(self, backend: Backend) -> Dict[str, TableDefinition]:
        """
        Discover all tables and their columns from a backend.
        
        Args:
            backend: Connected database backend
            
        Returns:
            Dict mapping table names to TableDefinition objects
        """
        tables = {}
        
        for table_name in backend.get_tables():
            columns = backend.get_columns(table_name)
            primary_key = backend.get_primary_key(table_name)
            
            field_defs = []
            for col in columns:
                field_def = FieldDefinition(
                    name=col.name,
                    type_name=col.type_name,
                    nullable=col.nullable,
                    max_length=col.max_length,
                    is_primary_key=(col.name == primary_key)
                )
                field_defs.append(field_def)
            
            tables[table_name] = TableDefinition(
                name=table_name,
                columns=field_defs,
                primary_key=primary_key
            )
        
        return tables
    
    def probe_table(self, backend: Backend, table_name: str) -> TableDefinition:
        """
        Probe a single table.
        
        Args:
            backend: Connected database backend
            table_name: Name of the table to probe
            
        Returns:
            TableDefinition for the specified table
        """
        columns = backend.get_columns(table_name)
        primary_key = backend.get_primary_key(table_name)
        
        field_defs = []
        for col in columns:
            field_def = FieldDefinition(
                name=col.name,
                type_name=col.type_name,
                nullable=col.nullable,
                max_length=col.max_length,
                is_primary_key=(col.name == primary_key)
            )
            field_defs.append(field_def)
        
        return TableDefinition(
            name=table_name,
            columns=field_defs,
            primary_key=primary_key
        )
