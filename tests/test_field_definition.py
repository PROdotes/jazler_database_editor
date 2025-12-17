"""
Tests for the Field Registry and Field Definition.

These tests ensure the field registry provides correct metadata
and that all expected fields are properly defined.
"""

import pytest
from src.models.field_definition import (
    FieldDefinition,
    FieldRegistry,
    field_registry,
    FIELD_REGISTRY
)


class TestFieldDefinition:
    """Test the FieldDefinition dataclass."""
    
    def test_field_definition_creation(self):
        """Test creating a basic field definition."""
        field = FieldDefinition(
            name="test",
            db_column="fldTest",
            display_name="Test Field"
        )
        
        assert field.name == "test"
        assert field.db_column == "fldTest"
        assert field.display_name == "Test Field"
        assert field.song_attr == "test"  # Defaults to name
        assert field.required is False  # Default (most fields are optional)
        assert field.editable is True  # Default
    
    def test_field_definition_with_custom_song_attr(self):
        """Test field with custom song attribute."""
        field = FieldDefinition(
            name="genre",
            db_column="fldCat1a",
            display_name="Genres",
            song_attr="genres_all"
        )
        
        assert field.name == "genre"
        assert field.song_attr == "genres_all"
    
    def test_field_definition_optional(self):
        """Test optional field properties."""
        field = FieldDefinition(
            name="album",
            db_column="fldAlbum",
            display_name="Album",
            required=False
        )
        
        assert field.required is False
        assert field.is_optional is True
    
    def test_field_definition_disabled(self):
        """Test disabled field properties."""
        field = FieldDefinition(
            name="decade",
            db_column="fldCat2",
            display_name="Decade",
            editable=False
        )
        
        assert field.editable is False
        assert field.is_disabled is True


class TestFieldRegistry:
    """Test the FieldRegistry class."""
    
    def test_registry_has_all_fields(self):
        """Verify registry contains all expected fields."""
        expected_fields = [
            "artist", "title", "album", "composer", "publisher",
            "year", "decade", "genre", "isrc", "duration"
        ]
        
        registry = FieldRegistry()
        actual_fields = registry.names
        
        assert set(actual_fields) == set(expected_fields)
        assert len(actual_fields) == 10
    
    def test_get_field_by_name(self):
        """Test retrieving field by name."""
        registry = FieldRegistry()
        
        field = registry.get("title")
        assert field is not None
        assert field.name == "title"
        assert field.db_column == "fldTitle"
        assert field.display_name == "Title"
    
    def test_get_field_by_db_column(self):
        """Test retrieving field by database column."""
        registry = FieldRegistry()
        
        field = registry.get_by_db_column("fldTitle")
        assert field is not None
        assert field.name == "title"
    
    def test_get_field_by_song_attr(self):
        """Test retrieving field by Song attribute."""
        registry = FieldRegistry()
        
        # Genre widget maps to genres_all Song attribute
        field = registry.get_by_song_attr("genres_all")
        assert field is not None
        assert field.name == "genre"
        assert field.song_attr == "genres_all"
    
    def test_queryable_fields(self):
        """Test getting queryable fields."""
        registry = FieldRegistry()
        queryable = registry.queryable()
        
        queryable_names = [f.name for f in queryable]
        
        # These should be queryable
        assert "artist" in queryable_names
        assert "title" in queryable_names
        assert "album" in queryable_names
        assert "composer" in queryable_names
        assert "publisher" in queryable_names
        assert "year" in queryable_names
        
        # These should NOT be queryable
        assert "genre" not in queryable_names
        assert "isrc" not in queryable_names
        assert "decade" not in queryable_names
        assert "duration" not in queryable_names
    
    def test_required_fields(self):
        """Test getting required fields."""
        registry = FieldRegistry()
        required = registry.required()
        
        required_names = [f.name for f in required]
        
        assert "artist" in required_names
        assert "title" in required_names
        assert "genre" in required_names
    
    def test_optional_fields(self):
        """Test getting optional fields."""
        registry = FieldRegistry()
        optional = registry.optional()
        
        optional_names = [f.name for f in optional]
        
        assert "album" in optional_names
        assert "composer" in optional_names
        assert "publisher" in optional_names
        assert "isrc" in optional_names
        assert "year" in optional_names
    
    def test_disabled_fields(self):
        """Test getting disabled fields."""
        registry = FieldRegistry()
        disabled = registry.disabled()
        
        disabled_names = [f.name for f in disabled]
        
        assert "decade" in disabled_names
        assert "duration" in disabled_names
        assert "artist" in disabled_names
    
    def test_db_columns_mapping(self):
        """Test database column mapping."""
        registry = FieldRegistry()
        db_columns = registry.db_columns
        
        assert db_columns["title"] == "fldTitle"
        assert db_columns["album"] == "fldAlbum"
        assert db_columns["publisher"] == "fldLabel"  # Special mapping
        assert db_columns["isrc"] == "fldCDKey"  # Special mapping
    
    def test_display_names_mapping(self):
        """Test display name mapping."""
        registry = FieldRegistry()
        display_names = registry.display_names
        
        assert display_names["title"] == "Title"
        assert display_names["genre"] == "Genres"  # Plural
        assert display_names["isrc"] == "ISRC"  # All caps


class TestFieldRegistryEdgeCases:
    """Test edge cases and special field behaviors."""
    
    def test_publisher_maps_to_label(self):
        """Verify publisher field maps to fldLabel."""
        registry = FieldRegistry()
        field = registry.get("publisher")
        
        assert field.name == "publisher"
        assert field.db_column == "fldLabel"
    
    def test_isrc_maps_to_cdkey(self):
        """Verify ISRC field maps to fldCDKey."""
        registry = FieldRegistry()
        field = registry.get("isrc")
        
        assert field.name == "isrc"
        assert field.db_column == "fldCDKey"
    
    def test_genre_maps_to_genres_all(self):
        """Verify genre widget maps to genres_all Song attribute."""
        registry = FieldRegistry()
        field = registry.get("genre")
        
        assert field.name == "genre"
        assert field.song_attr == "genres_all"
    
    def test_artist_special_comparison(self):
        """Verify artist field uses special comparison."""
        registry = FieldRegistry()
        field = registry.get("artist")
        
        assert field.special_comparison is True
    
    def test_artist_db_not_editable(self):
        """Verify artist DB side is not editable."""
        registry = FieldRegistry()
        field = registry.get("artist")
        
        assert field.db_editable is False
        assert field.id3_editable is True


class TestGlobalRegistry:
    """Test the global field_registry instance."""
    
    def test_global_registry_exists(self):
        """Verify global registry is available."""
        assert field_registry is not None
        assert isinstance(field_registry, FieldRegistry)
    
    def test_global_registry_has_fields(self):
        """Verify global registry has all fields."""
        assert len(field_registry.names) == 10
    
    def test_field_registry_constant_exists(self):
        """Verify FIELD_REGISTRY constant exists."""
        assert FIELD_REGISTRY is not None
        assert len(FIELD_REGISTRY) == 10
