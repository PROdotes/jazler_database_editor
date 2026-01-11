"""
Schema system for database introspection and configuration.

Provides:
- SchemaDiscovery: Auto-probe tables and columns from any backend
- SchemaRegistry: Combines discovered schema with user overrides
- FieldDefinition/TableDefinition: Data classes for schema metadata
"""

from src.core.schema.definition import FieldDefinition, TableDefinition
from src.core.schema.discovery import SchemaDiscovery
from src.core.schema.registry import SchemaRegistry

__all__ = [
    'FieldDefinition', 
    'TableDefinition', 
    'SchemaDiscovery', 
    'SchemaRegistry'
]
