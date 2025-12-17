"""
Field Definition Model for the Database Editor.

This module provides a centralized definition of all fields used in the application,
including their properties, mappings, and behavior. This eliminates duplication
and provides a single source of truth for field metadata.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FieldDefinition:
    """
    Defines a field used in the Database Editor UI.
    
    Attributes:
        name: Internal field name (used as dictionary key for widgets)
        db_column: Database column name (e.g., "fldTitle")
        display_name: Human-readable name shown in UI
        song_attr: Attribute name on Song object (defaults to name if None)
        required: Whether field must have a value
        editable: Whether user can edit this field
        db_editable: Whether DB side is editable (for artist field)
        id3_editable: Whether ID3 side is editable
        queryable: Whether field can be used in database queries
        special_comparison: Whether field uses special comparison logic (e.g., artist startswith)
    """
    name: str
    db_column: str
    display_name: str
    song_attr: Optional[str] = None  # Defaults to name if None
    required: bool = False  # Most fields are optional
    editable: bool = True
    db_editable: bool = True
    id3_editable: bool = True
    queryable: bool = False
    special_comparison: bool = False
    
    def __post_init__(self):
        """Set song_attr to name if not provided."""
        if self.song_attr is None:
            # Use object.__setattr__ because dataclass is frozen
            object.__setattr__(self, 'song_attr', self.name)
    
    @property
    def is_disabled(self) -> bool:
        """Returns True if field should be disabled in UI."""
        return not self.editable
    
    @property
    def is_optional(self) -> bool:
        """Returns True if field is optional (not required)."""
        return not self.required


# Field Registry - Single source of truth for all fields
FIELD_REGISTRY = [
    # Artist - Special: DB side disabled, uses startswith comparison
    FieldDefinition(
        name="artist",
        db_column="fldArtistName",
        display_name="Artist",
        required=True,  # Required field
        editable=False,  # Calculated field
        db_editable=False,  # DB side is disabled
        queryable=True,
        special_comparison=True  # Uses startswith logic
    ),
    
    # Title - Required, fully editable
    FieldDefinition(
        name="title",
        db_column="fldTitle",
        display_name="Title",
        required=True,  # Required field
        queryable=True
    ),
    
    # Album - Optional, fully editable
    FieldDefinition(
        name="album",
        db_column="fldAlbum",
        display_name="Album",
        queryable=True
    ),
    
    # Composer - Optional, fully editable
    FieldDefinition(
        name="composer",
        db_column="fldComposer",
        display_name="Composer",
        queryable=True
    ),
    
    # Publisher - Optional, fully editable
    # Note: Maps to fldLabel in database (not fldPublisher)
    FieldDefinition(
        name="publisher",
        db_column="fldLabel",
        display_name="Publisher",
        queryable=True
    ),
    
    # Year - Optional, fully editable
    FieldDefinition(
        name="year",
        db_column="fldYear",
        display_name="Year",
        queryable=True
    ),
    
    # Decade - Calculated field, read-only
    FieldDefinition(
        name="decade",
        db_column="fldCat2",  # Maps to genre_04
        display_name="Decade",
        editable=False  # Calculated from year
    ),
    
    # Genre - Required, fully editable
    # Note: Widget key is "genre", but Song attribute is "genres_all"
    FieldDefinition(
        name="genre",
        db_column="fldCat1a",  # Primary genre
        display_name="Genres",
        song_attr="genres_all",  # Maps to genres_all on Song
        required=True  # Required field
    ),
    
    # ISRC - Optional, fully editable
    # Note: Maps to fldCDKey in database (not fldISRC)
    FieldDefinition(
        name="isrc",
        db_column="fldCDKey",
        display_name="ISRC"
    ),
    
    # Duration - Read-only, calculated from file
    FieldDefinition(
        name="duration",
        db_column="fldDuration",
        display_name="Duration",
        editable=False  # Read-only
    ),
]


class FieldRegistry:
    """
    Provides convenient access to field definitions.
    """
    
    def __init__(self):
        self._fields = {field.name: field for field in FIELD_REGISTRY}
        self._by_db_column = {field.db_column: field for field in FIELD_REGISTRY}
        self._by_song_attr = {field.song_attr: field for field in FIELD_REGISTRY}
    
    def get(self, name: str) -> Optional[FieldDefinition]:
        """Get field definition by name."""
        return self._fields.get(name)
    
    def get_by_db_column(self, db_column: str) -> Optional[FieldDefinition]:
        """Get field definition by database column name."""
        return self._by_db_column.get(db_column)
    
    def get_by_song_attr(self, song_attr: str) -> Optional[FieldDefinition]:
        """Get field definition by Song attribute name."""
        return self._by_song_attr.get(song_attr)
    
    def all(self) -> list[FieldDefinition]:
        """Get all field definitions in order."""
        return FIELD_REGISTRY.copy()
    
    def queryable(self) -> list[FieldDefinition]:
        """Get all queryable fields."""
        return [f for f in FIELD_REGISTRY if f.queryable]
    
    def editable(self) -> list[FieldDefinition]:
        """Get all editable fields."""
        return [f for f in FIELD_REGISTRY if f.editable]
    
    def required(self) -> list[FieldDefinition]:
        """Get all required fields."""
        return [f for f in FIELD_REGISTRY if f.required]
    
    def optional(self) -> list[FieldDefinition]:
        """Get all optional fields."""
        return [f for f in FIELD_REGISTRY if not f.required]
    
    def disabled(self) -> list[FieldDefinition]:
        """Get all disabled (read-only) fields."""
        return [f for f in FIELD_REGISTRY if not f.editable]
    
    @property
    def names(self) -> list[str]:
        """Get all field names."""
        return [f.name for f in FIELD_REGISTRY]
    
    @property
    def db_columns(self) -> dict[str, str]:
        """Get mapping of field name to database column."""
        return {f.name: f.db_column for f in FIELD_REGISTRY}
    
    @property
    def display_names(self) -> dict[str, str]:
        """Get mapping of field name to display name."""
        return {f.name: f.display_name for f in FIELD_REGISTRY}


# Global registry instance
field_registry = FieldRegistry()
