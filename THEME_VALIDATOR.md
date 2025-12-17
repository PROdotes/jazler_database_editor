# Theme Usage Validator

## Overview

The **Theme Usage Validator** is a tool that ensures the documentation in `theme.json` stays in sync with actual code usage. It scans the codebase to find all theme constant usages and compares them against the documented usage.

---

## Why This Is Useful

### Problem It Solves:
When developers add new UI elements or modify existing ones, they might:
- Use theme colors in new places without updating `theme.json` documentation
- Remove usage of a color but forget to update the docs
- Use the wrong theme constant for a particular purpose

### Solution:
The validator automatically:
- ✅ Finds all theme constant usages in the code
- ✅ Compares against documented usage in `theme.json`
- ✅ Reports discrepancies and provides usage statistics
- ✅ Runs as part of the test suite to catch issues early

---

## How to Use

### Command Line Usage

Run the validator manually:
```bash
python validate_theme_usage.py
```

**Output Example:**
```
================================================================================
THEME USAGE VALIDATION REPORT
================================================================================

[PASS] Overall Status: VALID

--------------------------------------------------------------------------------
DETAILS:
--------------------------------------------------------------------------------

[OK]   theme.BG_DARK: Used 9 times in code
       Documented: 5 use cases
       Detected: Buttons, Field validation, Labels, Main UI, Message frame

[OK]   theme.STATUS_SUCCESS: Used 8 times in code
       Documented: 7 use cases
       Detected: Field validation, Genre validation, ISRC validation, Main UI

[WARN] theme.SOME_COLOR: Documented but not used in code
       Documented uses: Old feature that was removed

================================================================================
```

### Automated Testing

The validator runs automatically as part of the test suite:
```bash
pytest tests/test_theme_usage_validator.py -v
```

**Tests Include:**
1. `test_theme_usage_matches_documentation` - Ensures all theme constants are documented
2. `test_all_theme_constants_are_used` - Warns about unused documented colors
3. `test_theme_usage_validator_finds_all_usages` - Verifies validator works correctly
4. `test_theme_constant_map_is_complete` - Ensures all colors are mapped

---

## How It Works

### 1. Scans Source Code
- Searches all `.py` files in `src/` directory
- Uses regex to find theme constant usage: `theme.BG_DARK`, `theme.STATUS_SUCCESS`, etc.
- Records file location, line number, and context for each usage

### 2. Analyzes Context
- Attempts to extract human-readable descriptions from code context
- Looks for keywords like "label", "button", "frame", "validation", etc.
- Groups usages by component type

### 3. Compares with Documentation
- Loads `theme.json` and extracts documented usage
- Compares actual usage count vs documented use cases
- Identifies discrepancies

### 4. Generates Report
- Shows usage statistics for each theme constant
- Highlights warnings (unused colors, undocumented usage)
- Provides actionable information for updating docs

---

## Status Codes

| Code | Meaning | Action Required |
|------|---------|-----------------|
| `[OK]` | Color is used and documented | None - everything is good |
| `[WARN]` | Minor issue (unused color, etc.) | Consider updating documentation |
| `[ERROR]` | Critical issue (missing from theme.json) | Fix immediately |

---

## Updating Documentation

When the validator reports discrepancies:

### If a color is used in new places:
1. Open `theme.json`
2. Find the color definition
3. Add the new usage to the `used_in` array

**Example:**
```json
{
  "status": {
    "success": {
      "hex": "#28a745",
      "name": "Success Green",
      "description": "Indicates successful validation...",
      "used_in": [
        "Test database button",
        "Valid fields",
        "Success messages",
        "NEW USAGE HERE"  // Add this
      ]
    }
  }
}
```

### If a color is no longer used:
1. Check if the usage was intentionally removed
2. If yes, remove it from `used_in` array in `theme.json`
3. If no, restore the usage in code

---

## Configuration

### Adding New Theme Constants

If you add a new theme constant:

1. **Add to `theme.json`:**
```json
{
  "new_category": {
    "new_color": {
      "hex": "#abc123",
      "name": "New Color",
      "description": "What this color is for",
      "used_in": ["Where it's used"]
    }
  }
}
```

2. **Add to `src/ui/theme.py`:**
```python
self.NEW_COLOR = self._theme_data["new_category"]["new_color"]["hex"]
```

3. **Add to `validate_theme_usage.py` THEME_CONSTANT_MAP:**
```python
THEME_CONSTANT_MAP = {
    ...
    'theme.NEW_COLOR': ('new_category', 'new_color'),
}
```

4. **Run validator to verify:**
```bash
python validate_theme_usage.py
```

---

## Integration with CI/CD

Add to your CI/CD pipeline to automatically check theme documentation:

```yaml
# Example GitHub Actions
- name: Validate Theme Documentation
  run: |
    python validate_theme_usage.py
    if [ $? -ne 0 ]; then
      echo "Theme documentation is out of sync!"
      exit 1
    fi
```

Or simply run the tests:
```bash
pytest tests/test_theme_usage_validator.py
```

---

## Benefits

### For Developers:
- ✅ **Automatic documentation** - No need to manually track color usage
- ✅ **Catches mistakes** - Warns when docs are out of sync
- ✅ **Easy maintenance** - Just run the validator

### For Documentation:
- ✅ **Always accurate** - Tests fail if docs are wrong
- ✅ **Comprehensive** - Shows all usage locations
- ✅ **Self-updating** - Detects new usage automatically

### For Code Quality:
- ✅ **Enforces consistency** - All colors must be documented
- ✅ **Prevents drift** - Docs stay in sync with code
- ✅ **Improves maintainability** - Easy to see where colors are used

---

## Example Workflow

1. **Developer adds new button with theme color:**
```python
btn = Button(root, bg=theme.STATUS_SUCCESS, text="Save")
```

2. **Run tests:**
```bash
pytest tests/
```

3. **Validator reports:**
```
[OK]   theme.STATUS_SUCCESS: Used 9 times in code  # Was 8 before
       Documented: 7 use cases
       Detected: ..., Buttons  # New detection!
```

4. **Developer updates `theme.json`:**
```json
{
  "status": {
    "success": {
      "used_in": [
        ...
        "Save button"  // Added
      ]
    }
  }
}
```

5. **Tests pass!** ✅

---

## Limitations

### Current Limitations:
- Only detects simple theme constant usage (`theme.CONSTANT`)
- Context extraction is heuristic-based (may not be 100% accurate)
- Doesn't detect dynamic color usage (e.g., `getattr(theme, color_name)`)

### Future Enhancements:
- More sophisticated context analysis
- Automatic documentation generation
- Visual diff of changes
- Integration with IDE for real-time validation

---

## Summary

The Theme Usage Validator is a **low-effort, high-value** tool that:
- Keeps documentation accurate
- Catches mistakes early
- Makes theme maintenance easier
- Runs automatically in tests

**Just run it and keep your docs in sync!** 🎨✅
