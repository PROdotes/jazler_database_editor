import pytest
from unittest.mock import MagicMock, patch
from src.ui.app import process_string_comparison, WebSearch, copy_text
from tkinter import Entry

def test_process_string_comparison():
    """Test string comparison logic for UI coloring."""
    
    # Match
    v1, v2, color = process_string_comparison("Abba", "Abba")
    assert v1 == "Abba"
    assert v2 == "Abba"
    assert color == "#3c3f41" # Dark color (match)
    
    # Mismatch
    v1, v2, color = process_string_comparison("Abba", "AC/DC")
    assert color == "#662222" # Red color (mismatch)
    
    # Empty vs None (Default Required=True)
    v1, v2, color = process_string_comparison("-", None)
    assert color == "#662222" # Mismatch/Empty is flagged red by default
    
    # Empty (Required=False)
    v1, v2, color = process_string_comparison("-", None, required=False)
    assert color == "#3c3f41" # Allowed because not required
    
    # Mismatch (Required=False)
    v1, v2, color = process_string_comparison("Abba", "AC/DC", required=False)
    assert color == "#662222" # Still mismatch

def test_process_string_comparison_artist():
    """Test string comparison logic specifically for artist field with startswith."""
    
    # Artist: Exact match
    v1, v2, color = process_string_comparison("The Beatles", "The Beatles", is_artist=True)
    assert v1 == "The Beatles"
    assert v2 == "The Beatles"
    assert color == "#3c3f41" # Match
    
    # Artist: ID3 starts with DB value (truncated in database)
    v1, v2, color = process_string_comparison("The Beatles", "The Beatles feat. Special Guest", is_artist=True)
    assert v1 == "The Beatles"
    assert v2 == "The Beatles feat. Special Guest"
    assert color == "#3c3f41" # Should match because ID3 starts with DB value
    
    # Artist: ID3 does NOT start with DB value
    v1, v2, color = process_string_comparison("The Beatles", "AC/DC", is_artist=True)
    assert color == "#662222" # Mismatch
    
    # Artist: DB value is substring but not at start
    v1, v2, color = process_string_comparison("Beatles", "The Beatles", is_artist=True)
    assert color == "#662222" # Mismatch - doesn't start with "Beatles"
    
    # Artist: Empty DB value (required)
    v1, v2, color = process_string_comparison("", "Some Artist", is_artist=True, required=True)
    assert color == "#662222" # Required but empty
    
    # Artist: Empty ID3 value
    v1, v2, color = process_string_comparison("The Beatles", "", is_artist=True)
    assert color == "#662222" # Mismatch - empty string doesn't start with "The Beatles"
    
    # Artist: Both empty (required)
    v1, v2, color = process_string_comparison("", "", is_artist=True, required=True)
    assert color == "#662222" # Required but empty
    
    # Artist: Both empty (not required)
    v1, v2, color = process_string_comparison("", "", is_artist=True, required=False)
    assert color == "#3c3f41" # OK because not required
    
    # Artist: Case sensitivity check
    v1, v2, color = process_string_comparison("the beatles", "The Beatles", is_artist=True)
    assert color == "#662222" # Case sensitive - doesn't start with lowercase
    
    # Artist: Partial match at start
    v1, v2, color = process_string_comparison("Led Zeppelin", "Led Zeppelin IV", is_artist=True)
    assert color == "#3c3f41" # Match - starts with DB value


@patch('src.ui.app.webbrowser')
def test_web_search(mock_browser):
    """Test web search URL generation."""
    # Mocking a simple object with attributes
    class SimpleSong:
        artist = "Test Artist"
        title = "Test Title"
        
    song = SimpleSong()
    
    # Google
    WebSearch.google_lookup(song)
    mock_browser.open.assert_called()
    url = mock_browser.open.call_args[0][0]
    assert "duckduckgo" in url
    assert "Test%20Artist" in url
    
    # Discogs
    WebSearch.discogs_lookup(song)
    url_discogs = mock_browser.open.call_args[0][0]
    assert "discogs" in url_discogs

def test_copy_text():
    """Test the copy text helper function using Mock objects acting like Tkinter widgets."""
    entry1 = MagicMock()
    entry1.get.return_value = "Value"
    
    entry2 = MagicMock()
    
    # Because END is a Tkinter constant, we need to pass something
    copy_text(entry1, entry2, "end")
    
    entry2.delete.assert_called_with(0, "end")
    entry2.insert.assert_called_with(0, "Value")
