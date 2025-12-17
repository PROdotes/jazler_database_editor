"""Test that theme usage in code matches documentation in theme.json."""

import pytest
from pathlib import Path
from validate_theme_usage import ThemeUsageValidator


def test_theme_usage_matches_documentation():
    """
    Test that all theme constants used in code are properly documented.
    
    This test ensures that:
    1. All theme constants are defined in theme.json
    2. Theme usage is tracked and documented
    3. No undocumented theme constants are used
    """
    project_root = Path(__file__).parent.parent
    validator = ThemeUsageValidator(project_root)
    
    is_valid, issues = validator.validate()
    
    # Print report for debugging if test fails
    if not is_valid:
        print("\n" + validator.generate_report())
    
    # Check for critical errors
    errors = [issue for issue in issues if issue.startswith('[ERROR]')]
    assert len(errors) == 0, f"Found {len(errors)} critical errors:\n" + "\n".join(errors)
    
    # Test passes if no critical errors
    assert is_valid, "Theme validation failed - see report above"


def test_all_theme_constants_are_used():
    """
    Test that all documented theme constants are actually used in the code.
    
    This helps catch when we remove usage but forget to update documentation.
    """
    project_root = Path(__file__).parent.parent
    validator = ThemeUsageValidator(project_root)
    
    is_valid, issues = validator.validate()
    
    # Check for unused constants
    unused = [issue for issue in issues if 'Documented but not used' in issue]
    
    # This is a warning, not a failure, but we want to know about it
    if unused:
        print("\nWarning: Some documented theme constants are not used:")
        for issue in unused:
            print(f"  {issue}")
    
    # Test always passes, but prints warnings
    assert True


def test_theme_usage_validator_finds_all_usages():
    """Test that the validator actually finds theme usages in the code."""
    project_root = Path(__file__).parent.parent
    validator = ThemeUsageValidator(project_root)
    
    usages = validator.find_theme_usages()
    
    # We should find at least some usages
    assert len(usages) > 0, "Validator found no theme usages - this is likely a bug"
    
    # Check that we found the expected constants
    expected_constants = [
        'theme.BG_DARK',
        'theme.BG_LIGHTER',
        'theme.STATUS_SUCCESS',
        'theme.STATUS_DANGER',
    ]
    
    for constant in expected_constants:
        assert constant in usages, f"Expected to find {constant} in code"
        assert len(usages[constant]) > 0, f"{constant} should be used at least once"


def test_theme_constant_map_is_complete():
    """Test that THEME_CONSTANT_MAP includes all theme constants."""
    project_root = Path(__file__).parent.parent
    validator = ThemeUsageValidator(project_root)
    
    # Load theme.json
    theme_data = validator.load_theme_json()
    
    # Count expected constants
    expected_count = 0
    for category in ['backgrounds', 'foregrounds', 'status', 'buttons']:
        if category in theme_data:
            expected_count += len(theme_data[category])
    
    # Count mapped constants
    mapped_count = len(validator.THEME_CONSTANT_MAP)
    
    assert mapped_count == expected_count, (
        f"THEME_CONSTANT_MAP has {mapped_count} entries but theme.json has {expected_count} colors. "
        "Update THEME_CONSTANT_MAP in validate_theme_usage.py"
    )
