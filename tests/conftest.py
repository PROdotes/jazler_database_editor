import sys
import os
import pytest
from unittest.mock import MagicMock

# Ensure 'src' is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_config(tmp_path):
    """
    Patches the global app_config to use a temporary config file.
    """
    config_file = tmp_path / "test_config.json"
    
    # Imports inside fixture to avoid circular issues or early init
    from src.core.config import app_config
    
    with pytest.MonkeyPatch.context() as m:
        # Patch the file path constant in the module
        m.setattr("src.core.config.CONFIG_FILE", str(config_file))
        
        # Force a reload so it reads from (and creates) the new empty temp file
        app_config.reload()
        
        yield app_config
        
        # Cleanup is handled by MonkeyPatch context exit (restores attr)
        # But app_config state might be dirty. 
        # Ideally we restore original state, but for unit tests transient file is fine.
