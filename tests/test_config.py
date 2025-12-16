import pytest
import os
import json
from unittest.mock import patch, mock_open
from src.core.config import Config

# Default values from src/core/config.py
DEFAULT_LIVE_PATH = r"\\ONAIR\Jazler RadioStar 2\Databases\JZRS2DB-V5.accdb"
DEFAULT_TEST_PATH = r"\\ONAIR\Jazler RadioStar 2\Databases - Copy\JZRS2DB-V5.accdb"

@pytest.fixture
def clean_config(tmp_path):
    """
    Creates a temporary config environment.
    """
    config_file = tmp_path / "test_config_unit.json"
    
    with pytest.MonkeyPatch.context() as m:
        m.setattr("src.core.config.CONFIG_FILE", str(config_file))
        yield config_file

def test_load_defaults_if_missing(clean_config):
    """Test that a new file is created with defaults if missing."""
    assert not os.path.exists(clean_config)
    cfg = Config() 
    assert os.path.exists(clean_config)
    assert cfg.db_path_live == DEFAULT_LIVE_PATH 

def test_load_existing_file(clean_config):
    data = {"db_path_live": "custom.mdb"}  
    with open(clean_config, 'w') as f:
        json.dump(data, f)
    cfg = Config()
    assert cfg.db_path_live == "custom.mdb"

def test_save_query(clean_config):
    cfg = Config()
    cfg.save_last_query("artist", "contains", "TestQuery")
    with open(clean_config, 'r') as f:
        data = json.load(f)
    last_q = data.get("last_query")
    assert last_q is not None
    assert last_q["value"] == "TestQuery"

def test_load_last_query(clean_config):
    cfg = Config()
    cfg.save_last_query("artist", "contains", "SavedQuery")
    loaded = cfg.load_last_query()
    assert loaded["value"] == "SavedQuery"

def test_set_db_mode(clean_config):
    cfg = Config()
    path_val = cfg.set_db_mode(True)
    assert path_val == DEFAULT_LIVE_PATH
    path_val = cfg.set_db_mode(False)
    assert path_val == DEFAULT_TEST_PATH

def test_corrupt_config_file(clean_config):
    with open(clean_config, 'w') as f:
        f.write("{ invalid json")
    cfg = Config()
    assert cfg.db_path_live == DEFAULT_LIVE_PATH

def test_save_query_error(clean_config, capsys):
    """Test handling of write error during save_last_query."""
    cfg = Config()
    
    # Mock open to raise PermissionError when writing
    # We must allow read (for load_from_file called inside save_last_query)
    # So we only fail on mode='w'
    
    original_open = open
    def side_effect(file, mode='r', *args, **kwargs):
        if 'w' in mode:
            raise PermissionError("Disk Full")
        return original_open(file, mode, *args, **kwargs)

    with patch('builtins.open', side_effect=side_effect):
        cfg.save_last_query("artist", "eq", "val")
        
    # Verify error was printed (captured by capsys)
    captured = capsys.readouterr()
    assert "Error saving last query" in captured.out
    assert "Disk Full" in captured.out
