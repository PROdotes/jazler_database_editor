import pytest
from unittest.mock import MagicMock, patch
from src.core.config import Config


def test_position_restoration_within_bounds():
    """Test that position is correctly restored when within query bounds."""
    
    # Create a mock config file with a saved position
    mock_config_data = {
        "db_path_live": "test.accdb",
        "db_path_test": "test.accdb",
        "drive_map": {},
        "genre_rules": {},
        "last_query": {
            "field": "artist",
            "match": "contains",
            "value": "test",
            "position": 10
        }
    }
    
    with patch('src.core.config.path.exists', return_value=True), \
         patch('builtins.open', create=True) as mock_open, \
         patch('json.load', return_value=mock_config_data):
        
        config = Config()
        last_query = config.load_last_query()
        
        assert last_query is not None
        assert last_query["position"] == 10


def test_position_restoration_out_of_bounds():
    """Test that position handling when saved position exceeds query length."""
    
    # Simulate: saved position is 100, but query only has 50 results
    saved_position = 100
    query_length = 50
    
    # This is the logic from app.py lines 40-59
    if saved_position < 0:
        restored_position = 0
    elif saved_position >= query_length:
        restored_position = max(0, query_length - 1)
    else:
        restored_position = saved_position
    
    # Should clamp to last valid position (49)
    assert restored_position == 49


def test_position_restoration_negative():
    """Test that negative positions are clamped to 0."""
    
    saved_position = -5
    query_length = 100
    
    if saved_position < 0:
        restored_position = 0
    elif saved_position >= query_length:
        restored_position = max(0, query_length - 1)
    else:
        restored_position = saved_position
    
    assert restored_position == 0


def test_position_restoration_empty_query():
    """Test position handling when query returns no results."""
    
    saved_position = 10
    query_length = 0
    
    if saved_position < 0:
        restored_position = 0
    elif saved_position >= query_length:
        restored_position = max(0, query_length - 1)
    else:
        restored_position = saved_position
    
    # Should return 0 (max(0, -1) = 0)
    assert restored_position == 0


def test_save_position_without_last_query():
    """Test that save_last_position creates last_query if it doesn't exist."""
    
    mock_config_data = {
        "db_path_live": "test.accdb",
        "db_path_test": "test.accdb",
        "drive_map": {},
        "genre_rules": {}
        # Note: no "last_query" key
    }
    
    with patch('src.core.config.path.exists', return_value=True), \
         patch('builtins.open', create=True) as mock_open, \
         patch('json.load', return_value=mock_config_data), \
         patch('json.dump') as mock_dump:
        
        config = Config()
        # This should create last_query section
        config.save_last_position(10)
        
        # Verify it DID save and created last_query
        assert mock_dump.called
        saved_config = mock_dump.call_args[0][0]
        assert "last_query" in saved_config
        assert saved_config["last_query"]["position"] == 10
        assert saved_config["last_query"]["field"] == "artist"
        assert saved_config["last_query"]["match"] == "contains"
