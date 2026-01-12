"""
Generic Record model for database rows.

A schema-aware wrapper around database records that provides:
- Attribute-style access (record.artist instead of record['fldArtist'])
- Display name resolution
- Type coercion
- Change tracking for updates
"""

from typing import Dict, Any, Optional, List, Set
from src.core.schema.definition import TableDefinition


class Record:
    """
    A generic, schema-aware database record.
    
    Usage:
        record = Record(row_data, table_definition)
        print(record.artist)  # Access by display name (lowercase)
        print(record['fldArtist'])  # Access by column name
        record.artist = "New Artist"  # Modify
        print(record.changes)  # {'fldArtist': 'New Artist'}
    """
    
    # FIELD_ALIASES removed - now handled by table schema
    
    def __init__(self, data: Dict[str, Any], schema: Optional[TableDefinition] = None):
        """
        Initialize a record.
        
        Args:
            data: Dict mapping column names to values
            schema: Optional TableDefinition for column metadata
        """
        # Use object.__setattr__ to avoid triggering our custom __setattr__
        object.__setattr__(self, '_data', dict(data))
        object.__setattr__(self, '_schema', schema)
        object.__setattr__(self, '_changes', {})
        object.__setattr__(self, '_display_to_column', {})
        
        # Build lowercase -> actual column name map for case-insensitive access
        lower_map = {k.lower(): k for k in data.keys()}
        object.__setattr__(self, '_lower_column_map', lower_map)
        
        # Build display name -> column name mapping
        if schema:
            for col in schema.columns:
                if col.display_name:
                    # Store as lowercase for case-insensitive access
                    key = col.display_name.lower().replace(' ', '_')
                    self._display_to_column[key] = col.name
                # Also allow access by column name (lowercase, no prefix)
                # e.g., "fldArtistName" -> "artistname"
                simple_name = col.name.lower()
                if simple_name.startswith('fld'):
                    simple_name = simple_name[3:]
                self._display_to_column[simple_name] = col.name
    
    def _resolve_column(self, name: str) -> Optional[str]:
        """Resolve a display name or alias to the actual column name."""
        # Direct match
        if name in self._data:
            return name
        
        name_lower = name.lower().replace(' ', '_')
        
        # Check aliases from schema
        if self._schema and self._schema.aliases:
            if name_lower in self._schema.aliases:
                alias_target = self._schema.aliases[name_lower]
                if alias_target in self._data:
                    return alias_target
                if alias_target.lower() in self._lower_column_map:
                    return self._lower_column_map[alias_target.lower()]
        
        # Finally check fuzzy match (remove underscores)
        fuzzy_name = name_lower.replace('_', '')
        if fuzzy_name in self._display_to_column:
            target = self._display_to_column[fuzzy_name]
            if target in self._data: return target
            if target.lower() in self._lower_column_map:
                return self._lower_column_map[target.lower()]
        
        # Try display name lookup
        if name_lower in self._display_to_column:
            target = self._display_to_column[name_lower]
            if target in self._data:
                return target
            if target.lower() in self._lower_column_map:
                return self._lower_column_map[target.lower()]
        
        # Fallback: check if the name itself exists case-insensitively
        if name_lower in self._lower_column_map:
            return self._lower_column_map[name_lower]
        
        return None
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to fields."""
        col = self._resolve_column(name)
        if col:
            return self._data.get(col)
        raise AttributeError(f"No column '{name}' in record")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Track changes when setting attributes."""
        col = self._resolve_column(name)
        if col:
            old_value = self._data.get(col)
            if old_value != value:
                self._data[col] = value
                self._changes[col] = value
        else:
            # For non-column attributes, use normal behavior
            object.__setattr__(self, name, value)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access."""
        col = self._resolve_column(key)
        if col:
            return self._data.get(col)
        raise KeyError(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-style mutation."""
        col = self._resolve_column(key)
        if col:
            old_value = self._data.get(col)
            if old_value != value:
                self._data[col] = value
                self._changes[col] = value
        else:
            raise KeyError(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if a column exists."""
        return self._resolve_column(key) is not None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style get with default."""
        col = self._resolve_column(key)
        if col:
            return self._data.get(col, default)
        return default
    
    @property
    def changes(self) -> Dict[str, Any]:
        """Get dict of changed columns and their new values."""
        return dict(self._changes)
    
    @property
    def has_changes(self) -> bool:
        """Check if any fields have been modified."""
        return len(self._changes) > 0
    
    def clear_changes(self) -> None:
        """Clear the change tracker (e.g., after saving)."""
        self._changes.clear()
    
    @property
    def primary_key(self) -> Any:
        """Get the primary key value."""
        if self._schema and self._schema.primary_key:
            return self._data.get(self._schema.primary_key)
        # Fallback to common PK names
        for key in ['AUID', 'ID', 'id', 'Id']:
            if key in self._data:
                return self._data[key]
        return None
    
    @property
    def raw_data(self) -> Dict[str, Any]:
        """Get the underlying data dict (read-only copy)."""
        return dict(self._data)
    
    def to_dict(self, use_display_names: bool = False) -> Dict[str, Any]:
        """
        Convert record to a plain dict.
        
        Args:
            use_display_names: If True, use display names as keys
            
        Returns:
            Dict representation of the record
        """
        if not use_display_names or not self._schema:
            return dict(self._data)
        
        result = {}
        for col in self._schema.columns:
            value = self._data.get(col.name)
            key = col.display_name if col.display_name else col.name
            result[key] = value
        return result
    
    def __repr__(self) -> str:
        pk = self.primary_key
        if self._schema:
            return f"<Record {self._schema.name}#{pk}>"
        return f"<Record #{pk}>"
    
    def __str__(self) -> str:
        """String representation with key fields."""
        parts = [repr(self)]
        # Show a few key fields if they exist
        for field in ['artist', 'title', 'name', 'filename']:
            value = self.get(field)
            if value:
                parts.append(f"{field}={value!r}")
                if len(parts) > 3:
                    break
        return " ".join(parts)


class RecordSet:
    """
    A collection of Records with navigation support.
    
    Provides:
    - Indexed access to records
    - Current position tracking
    - Iteration
    """
    
    def __init__(self, records: List[Record]):
        """Initialize with a list of records."""
        self._records = records
        self._position = 0 if records else -1
    
    @property
    def count(self) -> int:
        """Number of records in the set."""
        return len(self._records)
    
    @property
    def position(self) -> int:
        """Current position (0-indexed)."""
        return self._position
    
    @position.setter
    def position(self, value: int) -> None:
        """Set current position."""
        if self._records:
            self._position = max(0, min(value, len(self._records) - 1))
    
    @property
    def current(self) -> Optional[Record]:
        """Get the current record."""
        if 0 <= self._position < len(self._records):
            return self._records[self._position]
        return None
    
    def next(self) -> Optional[Record]:
        """Move to and return the next record."""
        if self._position < len(self._records) - 1:
            self._position += 1
            return self.current
        return None
    
    def previous(self) -> Optional[Record]:
        """Move to and return the previous record."""
        if self._position > 0:
            self._position -= 1
            return self.current
        return None
    
    def first(self) -> Optional[Record]:
        """Move to and return the first record."""
        if self._records:
            self._position = 0
            return self.current
        return None
    
    def last(self) -> Optional[Record]:
        """Move to and return the last record."""
        if self._records:
            self._position = len(self._records) - 1
            return self.current
        return None
    
    def __getitem__(self, index: int) -> Record:
        """Index access to records."""
        return self._records[index]
    
    def __iter__(self):
        """Iterate over records."""
        return iter(self._records)
    
    def __len__(self) -> int:
        """Length of record set."""
        return len(self._records)
    
    def __bool__(self) -> bool:
        """True if there are any records."""
        return len(self._records) > 0
    
    def __repr__(self) -> str:
        return f"<RecordSet count={self.count} position={self.position}>"
