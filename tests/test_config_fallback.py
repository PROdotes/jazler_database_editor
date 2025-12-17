import json
import os
import tempfile
import pytest
from src.core.config import Config, DEFAULT_CONFIG


def test_config_missing_keys_use_defaults():
    """Test that missing config keys fall back to default values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.json")
        
        # Create a config file with only some keys
        partial_config = {
            "db_path_live": "\\\\custom\\path\\live.accdb",
            # db_path_test is intentionally missing
            "drive_map": {"c:": "d:"}
            # genre_rules is intentionally missing
        }
        
        with open(config_path, 'w') as f:
            json.dump(partial_config, f)
        
        # Mock the CONFIG_FILE path
        import src.core.config as config_module
        original_config_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = config_path
        
        try:
            # Create a new config instance
            config = Config()
            
            # Check that custom values are preserved
            assert config.db_path_live == "\\\\custom\\path\\live.accdb"
            # drive_map should be merged: default + custom
            assert config.drive_map == {"b:": "z:", "c:": "d:"}
            
            # Check that missing keys use defaults
            assert config.db_path_test == DEFAULT_CONFIG["db_path_test"]
            assert config.genre_rules == DEFAULT_CONFIG["genre_rules"]
            
        finally:
            # Restore original CONFIG_FILE
            config_module.CONFIG_FILE = original_config_file


def test_config_missing_nested_keys_use_defaults():
    """Test that missing nested config keys (like genre_rules sub-keys) fall back to defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.json")
        
        # Create a config with partial genre_rules
        partial_config = {
            "db_path_live": "\\\\custom\\path\\live.accdb",
            "db_path_test": "\\\\custom\\path\\test.accdb",
            "drive_map": {"b:": "z:"},
            "genre_rules": {
                "path_overrides": {"custom": "z:\\\\custom\\\\"}
                # no_year_subfolder, no_genre_subfolder, standard_subfolder are missing
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(partial_config, f)
        
        # Mock the CONFIG_FILE path
        import src.core.config as config_module
        original_config_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = config_path
        
        try:
            # Create a new config instance
            config = Config()
            
            # Check that custom genre_rules values are preserved
            assert "custom" in config.genre_rules["path_overrides"]
            
            # Check that missing nested keys use defaults
            assert config.genre_rules["no_year_subfolder"] == DEFAULT_CONFIG["genre_rules"]["no_year_subfolder"]
            assert config.genre_rules["no_genre_subfolder"] == DEFAULT_CONFIG["genre_rules"]["no_genre_subfolder"]
            assert config.genre_rules["standard_subfolder"] == DEFAULT_CONFIG["genre_rules"]["standard_subfolder"]
            
        finally:
            # Restore original CONFIG_FILE
            config_module.CONFIG_FILE = original_config_file


def test_config_completely_empty_uses_all_defaults():
    """Test that an empty config file uses all default values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.json")
        
        # Create an empty config file
        with open(config_path, 'w') as f:
            json.dump({}, f)
        
        # Mock the CONFIG_FILE path
        import src.core.config as config_module
        original_config_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = config_path
        
        try:
            # Create a new config instance
            config = Config()
            
            # Check that all values use defaults
            assert config.db_path_live == DEFAULT_CONFIG["db_path_live"]
            assert config.db_path_test == DEFAULT_CONFIG["db_path_test"]
            assert config.drive_map == DEFAULT_CONFIG["drive_map"]
            assert config.genre_rules == DEFAULT_CONFIG["genre_rules"]
            
        finally:
            # Restore original CONFIG_FILE
            config_module.CONFIG_FILE = original_config_file
