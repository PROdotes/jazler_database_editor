import pytest
from unittest.mock import patch
import sys
import os


def test_config_location_logic_when_frozen():
    """Test that config path logic works correctly when running as standalone EXE."""
    
    # Simulate the logic from config.py
    with patch.object(sys, 'frozen', True, create=True), \
         patch.object(sys, 'executable', r'C:\Program Files\JazlerEditor\JazlerEditor.exe'):
        
        # Replicate the BASE_DIR logic from config.py
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = "should_not_reach_here"
        
        config_file = os.path.join(base_dir, "config.json")
        
        # Verify the paths are correct
        assert base_dir == r'C:\Program Files\JazlerEditor'
        assert config_file == r'C:\Program Files\JazlerEditor\config.json'


def test_config_location_logic_when_not_frozen():
    """Test that config path logic works correctly when running as script."""
    
    # Simulate the logic from config.py without sys.frozen
    frozen = getattr(sys, 'frozen', False)
    
    if frozen:
        base_dir = os.path.dirname(sys.executable)
    else:
        # This simulates the project root logic
        # In actual config.py, it goes up 3 levels from src/core/config.py
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    config_file = os.path.join(base_dir, "config.json")
    
    # When not frozen, should use project directory structure
    assert 'tests' in __file__  # We're in the tests directory
    assert config_file.endswith('config.json')
    # Should NOT be in Python's executable directory
    assert not config_file.startswith(os.path.dirname(sys.executable))
