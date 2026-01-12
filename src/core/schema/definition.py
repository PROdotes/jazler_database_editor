"""
Schema definition classes.

Provides dataclasses for representing database schema metadata.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class FieldDefinition:
    """
    Metadata about a database field/column.
    
    Combines introspected database info with user-configured display settings.
    """
    # Core properties (from database)
    name: str                           # Actual column name in DB
    type_name: str = "TEXT"             # Database type
    nullable: bool = True               # Whether NULL is allowed
    max_length: Optional[int] = None    # For text fields
    
    # User-configured properties (from overrides)
    display_name: Optional[str] = None  # Friendly name for UI
    is_ignored: bool = False            # Hide from UI/exports
    is_primary_key: bool = False        # Part of primary key
    
    # For lookup/foreign key fields
    lookup_table: Optional[str] = None  # e.g., "snCat1" for genre
    lookup_key: Optional[str] = None    # Key column in lookup table
    lookup_value: Optional[str] = None  # Value column in lookup table
    
    @property
    def label(self) -> str:
        """Return display name if set, otherwise the column name."""
        return self.display_name or self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'type': self.type_name,
            'nullable': self.nullable,
            'max_length': self.max_length,
            'display_name': self.display_name,
            'is_primary_key': self.is_primary_key,
            'is_ignored': self.is_ignored,
        }


@dataclass
class TableDefinition:
    """
    Metadata about a database table.
    
    Contains column definitions and table-level settings.
    """
    name: str                                         # Table name in DB
    columns: List[FieldDefinition] = field(default_factory=list)
    primary_key: Optional[str] = None                 # Primary key column name
    display_name: Optional[str] = None                # Friendly name for UI
    is_ignored: bool = False                          # Hide from exploration
    is_lookup: bool = False                           # Is a lookup/category table
    lookup_config: Optional[Dict[str, Any]] = None    # Configuration for lookup UI
    aliases: Dict[str, str] = field(default_factory=dict) # Field aliases
    
    def get_column(self, name: str) -> Optional[FieldDefinition]:
        """Get a column by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None
    
    def get_visible_columns(self) -> List[FieldDefinition]:
        """Get non-ignored columns."""
        return [c for c in self.columns if not c.is_ignored]
    
    @property
    def column_names(self) -> List[str]:
        """List of all column names."""
        return [c.name for c in self.columns]
    
    @property
    def visible_column_names(self) -> List[str]:
        """List of non-ignored column names."""
        return [c.name for c in self.get_visible_columns()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'primary_key': self.primary_key,
            'is_lookup': self.is_lookup,
            'lookup_config': self.lookup_config,
            'columns': [c.to_dict() for c in self.columns if not c.is_ignored]
        }
