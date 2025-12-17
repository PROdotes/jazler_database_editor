"""Tests for the theme management system."""

import json
import os
import tempfile
import pytest
from src.ui.theme import Theme


@pytest.fixture
def valid_theme_data():
    """Fixture providing valid theme data."""
    return {
        "backgrounds": {
            "dark": {
                "hex": "#2b2b2b",
                "name": "Charcoal Gray",
                "description": "Main background",
                "used_in": ["Main window"]
            },
            "lighter": {
                "hex": "#3c3f41",
                "name": "Dark Slate",
                "description": "Input fields",
                "used_in": ["Entry fields"]
            },
            "control_bar": {
                "hex": "#1e1e1e",
                "name": "Almost Black",
                "description": "Control bar",
                "used_in": ["Bottom bar"]
            },
            "disabled": {
                "hex": "#1e1e1e",
                "name": "Almost Black",
                "description": "Disabled fields",
                "used_in": ["Read-only fields"]
            }
        },
        "foregrounds": {
            "white": {
                "hex": "#ffffff",
                "name": "Pure White",
                "description": "Primary text",
                "used_in": ["Labels"]
            },
            "light_gray": {
                "hex": "#cccccc",
                "name": "Light Gray",
                "description": "Secondary text",
                "used_in": ["Subtitles"]
            },
            "medium_gray": {
                "hex": "#6c757d",
                "name": "Medium Gray",
                "description": "Disabled text",
                "used_in": ["Disabled fields"]
            }
        },
        "status": {
            "success": {
                "hex": "#28a745",
                "name": "Success Green",
                "description": "Success state",
                "used_in": ["Valid fields"]
            },
            "danger": {
                "hex": "#dc3545",
                "name": "Danger Red",
                "description": "Error state",
                "used_in": ["Errors"]
            },
            "warning": {
                "hex": "#fd7e14",
                "name": "Warning Orange",
                "description": "Warning state",
                "used_in": ["Warnings"]
            },
            "error_background": {
                "hex": "#662222",
                "name": "Dark Red",
                "description": "Error background",
                "used_in": ["Invalid fields"]
            }
        },
        "buttons": {
            "active": {
                "hex": "#4c5052",
                "name": "Slate Gray",
                "description": "Active button",
                "used_in": ["Hover state"]
            },
            "disabled": {
                "hex": "#555555",
                "name": "Dim Gray",
                "description": "Disabled button",
                "used_in": ["Disabled state"]
            }
        }
    }


@pytest.fixture
def theme_file(valid_theme_data):
    """Fixture that creates a temporary theme file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(valid_theme_data, f, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_theme_loads_successfully(theme_file, valid_theme_data, monkeypatch):
    """Test that theme loads all colors correctly from JSON."""
    import src.ui.theme as theme_module
    monkeypatch.setattr(theme_module, 'THEME_FILE', theme_file)
    
    theme = Theme()
    
    # Test backgrounds
    assert theme.BG_DARK == "#2b2b2b"
    assert theme.BG_LIGHTER == "#3c3f41"
    assert theme.BG_CONTROL_BAR == "#1e1e1e"
    assert theme.BG_DISABLED == "#1e1e1e"
    
    # Test foregrounds
    assert theme.FG_WHITE == "#ffffff"
    assert theme.FG_LIGHT_GRAY == "#cccccc"
    assert theme.FG_MEDIUM_GRAY == "#6c757d"
    
    # Test status colors
    assert theme.STATUS_SUCCESS == "#28a745"
    assert theme.STATUS_DANGER == "#dc3545"
    assert theme.STATUS_WARNING == "#fd7e14"
    assert theme.STATUS_ERROR_BG == "#662222"
    
    # Test button states
    assert theme.BTN_ACTIVE == "#4c5052"
    assert theme.BTN_DISABLED == "#555555"


def test_theme_missing_file_raises_error(monkeypatch):
    """Test that missing theme file raises FileNotFoundError."""
    import src.ui.theme as theme_module
    monkeypatch.setattr(theme_module, 'THEME_FILE', '/nonexistent/theme.json')
    
    with pytest.raises(FileNotFoundError) as exc_info:
        Theme()
    
    assert "Theme file not found" in str(exc_info.value)


def test_theme_invalid_json_raises_error(monkeypatch):
    """Test that invalid JSON raises JSONDecodeError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        import src.ui.theme as theme_module
        monkeypatch.setattr(theme_module, 'THEME_FILE', temp_path)
        
        with pytest.raises(json.JSONDecodeError):
            Theme()
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_get_color_info(theme_file, monkeypatch):
    """Test getting detailed color information."""
    import src.ui.theme as theme_module
    monkeypatch.setattr(theme_module, 'THEME_FILE', theme_file)
    
    theme = Theme()
    
    # Get success color info
    success_info = theme.get_color_info('status', 'success')
    assert success_info['hex'] == "#28a745"
    assert success_info['name'] == "Success Green"
    assert success_info['description'] == "Success state"
    assert "Valid fields" in success_info['used_in']
    
    # Get background color info
    bg_info = theme.get_color_info('backgrounds', 'dark')
    assert bg_info['hex'] == "#2b2b2b"
    assert bg_info['name'] == "Charcoal Gray"


def test_get_color_info_nonexistent_returns_empty(theme_file, monkeypatch):
    """Test that getting nonexistent color returns empty dict."""
    import src.ui.theme as theme_module
    monkeypatch.setattr(theme_module, 'THEME_FILE', theme_file)
    
    theme = Theme()
    
    info = theme.get_color_info('nonexistent', 'color')
    assert info == {}


def test_theme_reload(theme_file, valid_theme_data, monkeypatch):
    """Test that theme can be reloaded after modification."""
    import src.ui.theme as theme_module
    monkeypatch.setattr(theme_module, 'THEME_FILE', theme_file)
    
    theme = Theme()
    original_color = theme.BG_DARK
    assert original_color == "#2b2b2b"
    
    # Modify the theme file
    valid_theme_data['backgrounds']['dark']['hex'] = "#000000"
    with open(theme_file, 'w', encoding='utf-8') as f:
        json.dump(valid_theme_data, f, indent=2)
    
    # Reload theme
    theme.reload()
    
    # Verify color changed
    assert theme.BG_DARK == "#000000"
    assert theme.BG_DARK != original_color


def test_theme_repr(theme_file, monkeypatch):
    """Test theme string representation."""
    import src.ui.theme as theme_module
    monkeypatch.setattr(theme_module, 'THEME_FILE', theme_file)
    
    theme = Theme()
    repr_str = repr(theme)
    
    assert "Theme(" in repr_str
    assert "BG_DARK=#2b2b2b" in repr_str
    assert "BG_LIGHTER=#3c3f41" in repr_str
    assert "STATUS_SUCCESS=#28a745" in repr_str
    assert "STATUS_DANGER=#dc3545" in repr_str


def test_theme_colors_are_valid_hex(theme_file, monkeypatch):
    """Test that all loaded colors are valid hex codes."""
    import src.ui.theme as theme_module
    import re
    
    monkeypatch.setattr(theme_module, 'THEME_FILE', theme_file)
    
    theme = Theme()
    
    # Regex for valid hex color
    hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
    
    # Check all color attributes
    colors_to_check = [
        theme.BG_DARK, theme.BG_LIGHTER, theme.BG_CONTROL_BAR, theme.BG_DISABLED,
        theme.FG_WHITE, theme.FG_LIGHT_GRAY, theme.FG_MEDIUM_GRAY,
        theme.STATUS_SUCCESS, theme.STATUS_DANGER, theme.STATUS_WARNING, theme.STATUS_ERROR_BG,
        theme.BTN_ACTIVE, theme.BTN_DISABLED
    ]
    
    for color in colors_to_check:
        assert hex_pattern.match(color), f"Invalid hex color: {color}"


def test_actual_theme_file_is_valid():
    """Test that the actual theme.json file in the project is valid and complete."""
    from src.ui.theme import theme
    
    # Verify all required attributes exist and are valid hex codes
    import re
    hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
    
    required_attrs = [
        'BG_DARK', 'BG_LIGHTER', 'BG_CONTROL_BAR', 'BG_DISABLED',
        'FG_WHITE', 'FG_LIGHT_GRAY', 'FG_MEDIUM_GRAY',
        'STATUS_SUCCESS', 'STATUS_DANGER', 'STATUS_WARNING', 'STATUS_ERROR_BG',
        'BTN_ACTIVE', 'BTN_DISABLED'
    ]
    
    for attr in required_attrs:
        assert hasattr(theme, attr), f"Theme missing attribute: {attr}"
        color_value = getattr(theme, attr)
        assert hex_pattern.match(color_value), f"Invalid hex color for {attr}: {color_value}"


def test_theme_singleton_consistency():
    """Test that the global theme singleton is consistent."""
    from src.ui.theme import theme as theme1
    from src.ui.theme import theme as theme2
    
    # Should be the same instance
    assert theme1 is theme2
    assert theme1.BG_DARK == theme2.BG_DARK
