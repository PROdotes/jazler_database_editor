import pytest
from unittest.mock import MagicMock, patch
from src.web.app import DatabaseEditor


def test_ask_database_mode_defaults_to_test():
    """Test that the database selection dialog defaults to Test (False)."""
    
    # Mock all Tkinter components
    with patch('src.ui.app.Toplevel') as MockToplevel, \
         patch('src.ui.app.Frame'), \
         patch('src.ui.app.Label'), \
         patch('src.ui.app.Button') as MockButton:
        
        mock_window = MagicMock()
        MockToplevel.return_value = mock_window
        
        # Create a minimal DatabaseEditor instance just to test ask_database_mode
        # We need to avoid full initialization
        with patch('tkinter.Tk.__init__', return_value=None):
            app = object.__new__(DatabaseEditor)
            
            # Simulate closing the window without clicking (should default to Test)
            def simulate_close(*args, **kwargs):
                # Trigger the WM_DELETE_WINDOW protocol callback
                # The protocol is set to select_test, which sets result["use_live"] = False
                pass
            
            mock_window.wait_window.side_effect = simulate_close
            
            result = app.ask_database_mode()
            
            # Should default to False (Test database)
            assert result is False, "Database mode should default to Test (False)"


def test_ask_database_mode_live_selection():
    """Test that clicking Live button returns True."""
    
    with patch('src.ui.app.Toplevel') as MockToplevel, \
         patch('src.ui.app.Frame'), \
         patch('src.ui.app.Label'), \
         patch('src.ui.app.Button') as MockButton:
        
        mock_window = MagicMock()
        MockToplevel.return_value = mock_window
        
        # Track the button callbacks
        button_callbacks = {}
        
        def capture_button(parent, text=None, command=None, **kwargs):
            btn = MagicMock()
            if command:
                # Store callbacks based on button text
                if "LIVE" in text:
                    button_callbacks['live'] = command
                elif "Test" in text:
                    button_callbacks['test'] = command
            return btn
        
        MockButton.side_effect = capture_button
        
        with patch('tkinter.Tk.__init__', return_value=None):
            app = object.__new__(DatabaseEditor)
            
            # Simulate clicking Live button
            def simulate_live_click(*args, **kwargs):
                if 'live' in button_callbacks:
                    button_callbacks['live']()
            
            mock_window.wait_window.side_effect = simulate_live_click
            
            result = app.ask_database_mode()
            
            # Should return True (Live database)
            assert result is True, "Should return True when Live button is clicked"


def test_ask_database_mode_test_selection():
    """Test that clicking Test button returns False."""
    
    with patch('src.ui.app.Toplevel') as MockToplevel, \
         patch('src.ui.app.Frame'), \
         patch('src.ui.app.Label'), \
         patch('src.ui.app.Button') as MockButton:
        
        mock_window = MagicMock()
        MockToplevel.return_value = mock_window
        
        # Track the button callbacks
        button_callbacks = {}
        
        def capture_button(parent, text=None, command=None, **kwargs):
            btn = MagicMock()
            if command:
                if "LIVE" in text:
                    button_callbacks['live'] = command
                elif "Test" in text:
                    button_callbacks['test'] = command
            return btn
        
        MockButton.side_effect = capture_button
        
        with patch('tkinter.Tk.__init__', return_value=None):
            app = object.__new__(DatabaseEditor)
            
            # Simulate clicking Test button
            def simulate_test_click(*args, **kwargs):
                if 'test' in button_callbacks:
                    button_callbacks['test']()
            
            mock_window.wait_window.side_effect = simulate_test_click
            
            result = app.ask_database_mode()
            
            # Should return False (Test database)
            assert result is False, "Should return False when Test button is clicked"
