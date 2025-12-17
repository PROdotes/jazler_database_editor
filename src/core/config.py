import json
import sys
from os import path
from typing import Dict, Any, Optional
from src.utils.error_handler import ErrorHandler

# Determine base directory for config file
# When running as PyInstaller EXE, use the directory containing the EXE
# When running as script, use the project root
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = path.dirname(sys.executable)
else:
    # Running as script: src/core/config.py -> src/core -> src -> root
    BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

CONFIG_FILE = path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "db_path_live": r"\\ONAIR\Jazler RadioStar 2\Databases\JZRS2DB-V5.accdb",
    "db_path_test": r"\\ONAIR\Jazler RadioStar 2\Databases - Copy\JZRS2DB-V5.accdb",
    "base_songs_path": r"z:\songs",
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
    }
}

class Config:
    def __init__(self):
        self._data = self._load_from_file()
        
    def _load_from_file(self) -> Dict[str, Any]:
        if not path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                # Merge with defaults: any missing keys will use default values
                merged = DEFAULT_CONFIG.copy()
                merged.update(loaded)
                
                # Handle nested dicts (like genre_rules) - merge them too
                if "genre_rules" in loaded:
                    default_genre_rules = DEFAULT_CONFIG["genre_rules"].copy()
                    default_genre_rules.update(loaded["genre_rules"])
                    merged["genre_rules"] = default_genre_rules
                
                if "drive_map" in loaded:
                    default_drive_map = DEFAULT_CONFIG["drive_map"].copy()
                    default_drive_map.update(loaded["drive_map"])
                    merged["drive_map"] = default_drive_map
                
                return merged
        except Exception as e:
            ErrorHandler.log_silent(e, "Loading config")
            return DEFAULT_CONFIG.copy()

    def reload(self):
        """Force reload from disk"""
        self._data = self._load_from_file()

    def save_last_query(self, field: str, match: str, value: str):
        try:
            # We re-load first to ensure we don't overwrite external changes or use stale internal state
            current_config = self._load_from_file()
            current_config["last_query"] = {
                "field": field,
                "match": match,
                "value": value,
                "position": 0  # Reset position on new query
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(current_config, f, indent=4)
            self._data = current_config
        except Exception as e:
            ErrorHandler.log_silent(e, "Saving last query")

    def save_last_position(self, position: int):
        try:
            current_config = self._load_from_file()
            
            # Create last_query if it doesn't exist
            if "last_query" not in current_config:
                current_config["last_query"] = {
                    "field": "artist",
                    "match": "contains",
                    "value": "",
                    "position": position
                }
            else:
                # Update existing position
                current_config["last_query"]["position"] = position
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(current_config, f, indent=4)
            self._data = current_config
        except Exception as e:
            ErrorHandler.log_silent(e, "Saving last position")

    def load_last_query(self) -> Optional[Dict[str, str]]:
        # Always read fresh for query load just in case
        data = self._load_from_file() 
        return data.get("last_query", None)

    @property
    def db_path_live(self) -> str:
        return self._data.get("db_path_live", DEFAULT_CONFIG["db_path_live"])

    @property
    def db_path_test(self) -> str:
        return self._data.get("db_path_test", DEFAULT_CONFIG["db_path_test"])

    @property
    def drive_map(self) -> Dict[str, str]:
        return self._data.get("drive_map", DEFAULT_CONFIG["drive_map"])

    @property
    def genre_rules(self) -> Dict[str, Any]:
        return self._data.get("genre_rules", DEFAULT_CONFIG["genre_rules"])

    @property
    def base_songs_path(self) -> str:
        return self._data.get("base_songs_path", DEFAULT_CONFIG["base_songs_path"])

    def set_db_mode(self, use_live: bool) -> str:
        """Returns the selected database file path based on mode."""
        return self.db_path_live if use_live else self.db_path_test


# Global Singleton Instance
app_config = Config()
