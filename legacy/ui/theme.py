"""
Theme management for MS Database Sync App.

This module provides centralized color management through a JSON configuration file.
All UI colors are defined in theme.json and loaded through the Theme class.
"""

import json
import sys
from os import path
from typing import Dict, Any


# Determine base directory for theme file (same logic as config)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = path.dirname(sys.executable)
else:
    # Running as script: src/ui/theme.py -> src/ui -> src -> root
    BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

THEME_FILE = path.join(BASE_DIR, "theme.json")


class Theme:
    """
    Centralized theme management with JSON configuration support.
    
    All color constants are loaded from theme.json, making it easy to:
    - Customize the app's appearance
    - Create different themes (dark/light)
    - Maintain consistent colors across the application
    
    Usage:
        from src.ui.theme import theme
        
        # Use in tkinter widgets
        label = Label(root, bg=theme.BG_DARK, fg=theme.FG_WHITE)
        
        # Use for validation
        if is_valid:
            entry.config(bg=theme.STATUS_SUCCESS)
        else:
            entry.config(bg=theme.STATUS_ERROR_BG)
    """
    
    def __init__(self):
        """Load theme from JSON file."""
        self._theme_data = self._load_theme()
        self._init_color_constants()
    
    def _load_theme(self) -> Dict[str, Any]:
        """
        Load theme configuration from theme.json.
        
        Returns:
            Dictionary containing theme configuration
            
        Raises:
            FileNotFoundError: If theme.json doesn't exist
            json.JSONDecodeError: If theme.json is invalid
        """
        if not path.exists(THEME_FILE):
            raise FileNotFoundError(
                f"Theme file not found: {THEME_FILE}\n"
                "Please ensure theme.json exists in the application directory."
            )
        
        try:
            with open(THEME_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid theme.json: {e.msg}",
                e.doc,
                e.pos
            )
    
    def _init_color_constants(self):
        """Initialize color constants from loaded theme data."""
        # Backgrounds
        self.BG_DARK = self._theme_data["backgrounds"]["dark"]["hex"]
        self.BG_LIGHTER = self._theme_data["backgrounds"]["lighter"]["hex"]
        self.BG_CONTROL_BAR = self._theme_data["backgrounds"]["control_bar"]["hex"]
        self.BG_DISABLED = self._theme_data["backgrounds"]["disabled"]["hex"]
        
        # Foregrounds
        self.FG_WHITE = self._theme_data["foregrounds"]["white"]["hex"]
        self.FG_LIGHT_GRAY = self._theme_data["foregrounds"]["light_gray"]["hex"]
        self.FG_MEDIUM_GRAY = self._theme_data["foregrounds"]["medium_gray"]["hex"]
        
        # Status colors
        self.STATUS_SUCCESS = self._theme_data["status"]["success"]["hex"]
        self.STATUS_DANGER = self._theme_data["status"]["danger"]["hex"]
        self.STATUS_WARNING = self._theme_data["status"]["warning"]["hex"]
        self.STATUS_ERROR_BG = self._theme_data["status"]["error_background"]["hex"]
        
        # Button states
        self.BTN_ACTIVE = self._theme_data["buttons"]["active"]["hex"]
        self.BTN_DISABLED = self._theme_data["buttons"]["disabled"]["hex"]
    
    def get_color_info(self, category: str, color_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific color.
        
        Args:
            category: Color category (e.g., 'backgrounds', 'status')
            color_key: Specific color key (e.g., 'dark', 'success')
            
        Returns:
            Dictionary with color information (hex, name, description, used_in)
            
        Example:
            >>> info = theme.get_color_info('status', 'success')
            >>> print(info['name'])  # "Success Green"
            >>> print(info['description'])  # "Indicates successful validation..."
        """
        return self._theme_data.get(category, {}).get(color_key, {})
    
    def reload(self):
        """Reload theme from disk. Useful for live theme switching."""
        self._theme_data = self._load_theme()
        self._init_color_constants()
    
    def __repr__(self) -> str:
        """String representation showing all loaded colors."""
        return (
            f"Theme(BG_DARK={self.BG_DARK}, "
            f"BG_LIGHTER={self.BG_LIGHTER}, "
            f"STATUS_SUCCESS={self.STATUS_SUCCESS}, "
            f"STATUS_DANGER={self.STATUS_DANGER})"
        )


# Global singleton instance
# Import this in your UI code: from src.ui.theme import theme
theme = Theme()
