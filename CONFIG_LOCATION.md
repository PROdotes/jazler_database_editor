# Config File Location

## Overview
The `config.json` file stores application settings including database paths, genre rules, and the last query state.

## Location Behavior

### When Running as Standalone EXE
When you build and run `JazlerEditor.exe`, the config file will be created in **the same directory as the executable**.

**Example:**
```
C:\Program Files\JazlerEditor\
├── JazlerEditor.exe
└── config.json          ← Created here automatically
```

### When Running as Python Script (Development)
When running `python run.py` during development, the config file is created in the **project root directory**.

**Example:**
```
jazler_database_editor/
├── src/
├── tests/
├── run.py
└── config.json          ← Created here automatically
```

## How It Works

The application uses `sys.frozen` to detect if it's running as a compiled executable:

```python
if getattr(sys, 'frozen', False):
    # Running as EXE: use directory containing the executable
    BASE_DIR = path.dirname(sys.executable)
else:
    # Running as script: use project root
    BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
```

## Config File Contents

The config file is automatically created with default values on first run:

```json
{
    "db_path_live": "\\\\ONAIR\\Jazler RadioStar 2\\Databases\\JZRS2DB-V5.accdb",
    "db_path_test": "\\\\ONAIR\\Jazler RadioStar 2\\Databases - Copy\\JZRS2DB-V5.accdb",
    "drive_map": {
        "b:": "z:"
    },
    "genre_rules": {
        "path_overrides": {
            "domoljubne": "z:\\songs\\cro\\domoljubne\\",
            "religijske": "z:\\songs\\religiozne\\"
        },
        "no_year_subfolder": ["rock"],
        "no_genre_subfolder": ["pop"],
        "standard_subfolder": []
    },
    "last_query": {
        "field": "artist",
        "match": "contains",
        "value": "Beatles",
        "position": 5
    }
}
```

## Persistence

- **Development**: Config persists in the project directory
- **Standalone EXE**: Config persists next to the EXE, so settings are preserved between runs
- **Portable**: You can move the EXE to a different location, and it will create a new config there

## Deployment Notes

When distributing the application:
1. The EXE can be placed anywhere
2. Config will be created automatically on first run
3. Users can manually edit `config.json` to customize paths and settings
4. Ensure the user has write permissions in the directory where the EXE is located
