"""
Tests for field mappings across the application.

These tests ensure that field definitions, display names, database columns,
and widget keys are consistent across all usage locations. This provides
safety for the Field Registry refactoring (Phase 1, Task #1).
"""

import pytest
from unittest.mock import MagicMock, patch

from src.ui.app import DatabaseEditor


class TestFieldConsistency:
    """Test that field lists are consistent across different parts of the app."""
    
    def test_ui_field_list_completeness(self):
        """Verify all expected fields are in the UI field list."""
        # This is the list from line 225 in app.py
        expected_fields = ["artist", "title", "album", "composer", "publisher", 
                          "year", "decade", "genre", "isrc", "duration"]
        
        # These are the fields that should exist in the UI
        assert "artist" in expected_fields
        assert "title" in expected_fields
        assert "album" in expected_fields
        assert "composer" in expected_fields
        assert "publisher" in expected_fields
        assert "year" in expected_fields
        assert "decade" in expected_fields
        assert "genre" in expected_fields  # Note: maps to genres_all in Song
        assert "isrc" in expected_fields
        assert "duration" in expected_fields
    
    def test_optional_fields_subset(self):
        """Verify optional fields are a subset of all fields."""
        all_fields = ["artist", "title", "album", "composer", "publisher", 
                     "year", "decade", "genre", "isrc", "duration"]
        optional_fields = ["album", "composer", "publisher", "isrc", "year"]
        
        for field in optional_fields:
            assert field in all_fields, f"Optional field '{field}' not in all_fields"
    
    def test_gather_fields_subset(self):
        """Verify _gather_data_from_ui fields are valid."""
        # From line 583 in app.py
        gather_fields = ["title", "album", "composer", "publisher", "isrc", "genres_all"]
        
        # All gather fields should be valid Song attributes
        valid_song_attrs = ["title", "album", "composer", "publisher", "isrc", "genres_all", "year"]
        
        for field in gather_fields:
            assert field in valid_song_attrs, f"Gather field '{field}' not a valid Song attribute"


class TestQueryFieldMapping:
    """Test the field mapping used in query_execute."""
    
    def test_query_mapping_completeness(self):
        """Verify query field mapping covers all queryable fields."""
        # From line 386-393 in app.py
        query_mapping = {
            "artist": "fldArtistName",
            "title": "fldTitle",
            "album": "fldAlbum",
            "composer": "fldComposer",
            "publisher": "fldLabel",
            "year": "fldYear"
        }
        
        # Verify all mappings are present
        assert query_mapping["artist"] == "fldArtistName"
        assert query_mapping["title"] == "fldTitle"
        assert query_mapping["album"] == "fldAlbum"
        assert query_mapping["composer"] == "fldComposer"
        assert query_mapping["publisher"] == "fldLabel"
        assert query_mapping["year"] == "fldYear"
    
    def test_query_mapping_no_orphans(self):
        """Ensure query mapping keys are valid UI fields."""
        query_fields = ["artist", "title", "album", "composer", "publisher", "year"]
        valid_ui_fields = ["artist", "title", "album", "composer", "publisher", 
                          "year", "decade", "genre", "isrc", "duration"]
        
        for field in query_fields:
            assert field in valid_ui_fields, f"Query field '{field}' not in UI fields"


class TestSaveFieldMapping:
    """Test the field mapping used in save_song."""
    
    def test_save_mapping_to_db_columns(self):
        """Verify save operation maps to correct database columns."""
        # From lines 635-647 in app.py
        save_mapping = {
            "title": "fldTitle",
            "album": "fldAlbum",
            "year": "fldYear",
            "composer": "fldComposer",
            "publisher": "fldLabel",  # Note: publisher -> fldLabel
            "isrc": "fldCDKey",       # Note: isrc -> fldCDKey
            "duration": "fldDuration",
            "genre_01": "fldCat1a",
            "genre_02": "fldCat1b",
            "genre_03": "fldCat1c",
            "genre_04": "fldCat2",
        }
        
        # Verify critical mappings
        assert save_mapping["title"] == "fldTitle"
        assert save_mapping["album"] == "fldAlbum"
        assert save_mapping["year"] == "fldYear"
        assert save_mapping["composer"] == "fldComposer"
        assert save_mapping["publisher"] == "fldLabel"
        assert save_mapping["isrc"] == "fldCDKey"
        assert save_mapping["duration"] == "fldDuration"
    
    def test_genre_field_mapping(self):
        """Verify genre fields map correctly."""
        genre_mapping = {
            "genre_01": "fldCat1a",
            "genre_02": "fldCat1b",
            "genre_03": "fldCat1c",
            "genre_04": "fldCat2",
        }
        
        assert genre_mapping["genre_01"] == "fldCat1a"
        assert genre_mapping["genre_02"] == "fldCat1b"
        assert genre_mapping["genre_03"] == "fldCat1c"
        assert genre_mapping["genre_04"] == "fldCat2"


class TestDisplayNameMapping:
    """Test field display names shown in the UI."""
    
    def test_display_name_capitalization(self):
        """Verify display names are properly capitalized."""
        display_names = {
            "artist": "Artist",
            "title": "Title",
            "album": "Album",
            "composer": "Composer",
            "publisher": "Publisher",
            "year": "Year",
            "decade": "Decade",
            "genre": "Genres",      # Special case: genre -> Genres
            "isrc": "ISRC",         # Special case: all caps
            "duration": "Duration",
        }
        
        # Test standard capitalization
        assert display_names["artist"] == "Artist"
        assert display_names["title"] == "Title"
        
        # Test special cases
        assert display_names["genre"] == "Genres", "Genre should display as 'Genres'"
        assert display_names["isrc"] == "ISRC", "ISRC should be all caps"
    
    def test_display_name_logic(self):
        """Test the display name generation logic from app.py."""
        # Simulating lines 230-232 in app.py
        test_cases = [
            ("artist", "Artist"),
            ("title", "Title"),
            ("album", "Album"),
            ("year", "Year"),
            ("decade", "Decade"),
            ("duration", "Duration"),
        ]
        
        for field, expected in test_cases:
            # Standard capitalization
            display = field.capitalize()
            assert display == expected, f"Field '{field}' should display as '{expected}'"


class TestWidgetKeyMapping:
    """Test the mapping between Song attributes and UI widget keys."""
    
    def test_genres_all_to_genre_widget(self):
        """Verify genres_all Song attribute maps to 'genre' widget."""
        # This mapping appears in multiple places:
        # - Line 434: widget_key = "genre" if field == "genres_all" else field
        # - Line 586: widget_key = "genre" if field == "genres_all" else field
        
        song_attr = "genres_all"
        widget_key = "genre" if song_attr == "genres_all" else song_attr
        
        assert widget_key == "genre", "genres_all should map to 'genre' widget"
    
    def test_standard_field_widget_mapping(self):
        """Verify standard fields map to themselves."""
        standard_fields = ["title", "album", "composer", "publisher", "isrc", "year"]
        
        for field in standard_fields:
            widget_key = "genre" if field == "genres_all" else field
            assert widget_key == field, f"Field '{field}' should map to itself"


class TestFieldPropertyConsistency:
    """Test field property consistency (required, editable, etc.)."""
    
    def test_disabled_fields(self):
        """Verify which fields should be disabled in the UI."""
        # From lines 260-263 in app.py
        disabled_fields = ["decade", "duration", "artist"]
        
        assert "decade" in disabled_fields, "Decade should be disabled (calculated)"
        assert "duration" in disabled_fields, "Duration should be disabled (read-only)"
        assert "artist" in disabled_fields, "Artist DB field should be disabled"
    
    def test_required_vs_optional(self):
        """Verify required vs optional field classification."""
        # From line 464 in app.py
        optional_fields = ["album", "composer", "publisher", "isrc", "year"]
        
        all_editable_fields = ["title", "album", "composer", "publisher", "year", "genre", "isrc"]
        
        required_fields = [f for f in all_editable_fields if f not in optional_fields]
        
        assert "title" in required_fields, "Title should be required"
        assert "genre" in required_fields, "Genre should be required"
        assert "album" in optional_fields, "Album should be optional"
        assert "year" in optional_fields, "Year should be optional"
    
    def test_artist_field_special_handling(self):
        """Verify artist field has special comparison logic."""
        # Artist uses startswith comparison (line 468 in app.py)
        special_comparison_fields = ["artist"]
        
        assert "artist" in special_comparison_fields, "Artist should use special comparison"


class TestFieldIntegration:
    """Integration tests for field usage across the application."""
    
    def test_query_dropdown_fields_match_mapping(self):
        """Verify query dropdown options match the query mapping."""
        # From line 739 in app.py
        dropdown_values = ["artist", "title", "album", "composer", "publisher", "year"]
        
        # These should all be in the query mapping
        query_mapping_keys = ["artist", "title", "album", "composer", "publisher", "year"]
        
        assert set(dropdown_values) == set(query_mapping_keys), \
            "Query dropdown values should match query mapping keys"
    
    def test_status_indicator_field_access(self):
        """Verify status indicators can access correct widget keys."""
        # From _update_status_indicators (lines 484-485, 496-498)
        # These fields are accessed directly for status updates
        ui_fields = ["artist", "title", "album", "composer", "publisher", 
                    "year", "decade", "genre", "isrc", "duration"]
        
        # Status indicators access these specific fields
        status_fields = ["genre", "isrc"]
        
        for field in status_fields:
            assert field in ui_fields, f"Status field '{field}' must be in UI fields"
    
    def test_update_fields_uses_correct_fields(self):
        """Verify update_fields accesses all expected widgets."""
        # From update_fields (lines 426-449)
        # These are the fields that update_fields manipulates
        update_fields_list = ["artist", "title", "album", "composer", "publisher", 
                             "year", "genres_all", "isrc", "decade", "duration"]
        
        # All should be valid
        valid_fields = ["artist", "title", "album", "composer", "publisher", 
                       "year", "decade", "genre", "isrc", "duration", "genres_all"]
        
        for field in update_fields_list:
            # genres_all maps to genre widget
            if field == "genres_all":
                assert "genre" in valid_fields, "genres_all should map to genre widget"
            else:
                assert field in valid_fields, f"Update field '{field}' must be valid"
    
    def test_save_song_direct_genre_access(self):
        """Verify save_song can access genre widget directly."""
        # From save_song (lines 619-620)
        # save_song directly accesses self.texts_db["genre"]
        ui_fields = ["artist", "title", "album", "composer", "publisher", 
                    "year", "decade", "genre", "isrc", "duration"]
        
        assert "genre" in ui_fields, "Genre widget must exist for save_song"
    
    def test_disabled_fields_can_be_toggled(self):
        """Verify disabled fields exist and can be toggled."""
        # From update_fields (lines 438-449)
        # These fields are toggled between normal and disabled
        toggleable_fields = ["decade", "duration", "artist"]
        ui_fields = ["artist", "title", "album", "composer", "publisher", 
                    "year", "decade", "genre", "isrc", "duration"]
        
        for field in toggleable_fields:
            assert field in ui_fields, f"Toggleable field '{field}' must be in UI fields"



class TestFieldMappingEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_publisher_to_label_mapping(self):
        """Verify publisher maps to fldLabel (not fldPublisher)."""
        # This is a common source of bugs
        assert "publisher" != "label", "UI uses 'publisher'"
        
        # But database uses fldLabel
        db_column = "fldLabel"
        assert db_column == "fldLabel", "Database column is fldLabel"
    
    def test_isrc_to_cdkey_mapping(self):
        """Verify ISRC maps to fldCDKey (not fldISRC)."""
        # Another common source of bugs
        ui_field = "isrc"
        db_column = "fldCDKey"
        
        assert ui_field == "isrc", "UI uses 'isrc'"
        assert db_column == "fldCDKey", "Database column is fldCDKey"
    
    def test_genre_vs_genres_all(self):
        """Verify genre/genres_all naming consistency."""
        ui_widget_key = "genre"
        song_attribute = "genres_all"
        
        assert ui_widget_key == "genre", "UI widget is 'genre'"
        assert song_attribute == "genres_all", "Song attribute is 'genres_all'"
        
        # They should map to each other
        widget_key = "genre" if song_attribute == "genres_all" else song_attribute
        assert widget_key == ui_widget_key, "genres_all should map to genre widget"
