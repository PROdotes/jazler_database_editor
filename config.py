import json
from os import path
from typing import Dict, Any, Optional

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "db_path_live": r"\\ONAIR\Jazler RadioStar 2\Databases\JZRS2DB-V5.accdb",
    "db_path_test": r"\\ONAIR\Jazler RadioStar 2\Databases - Copy\JZRS2DB-V5.accdb",
    "drive_map": {
        "b:": "z:"
    },
    "genre_rules": {
        "path_overrides": {
            "domoljubne": "z:\\songs\\cro\\domoljubne\\",
            "religijske": "z:\\songs\\religiozne\\"
        },
        "no_year_subfolder": ["rock"],
        "no_genre_subfolder": ["pop"]
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
                # Ensure new keys exist if loading old config
                if "genre_rules" not in loaded:
                    loaded["genre_rules"] = DEFAULT_CONFIG["genre_rules"]
                return loaded
        except Exception as e:
            print(f"Error loading config: {e}")
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
                "value": value
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(current_config, f, indent=4)
            self._data = current_config
        except Exception as e:
            print(f"Error saving last query: {e}")

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

    def set_db_mode(self, use_live: bool) -> str:
        """Returns the selected database file path based on mode."""
        return self.db_path_live if use_live else self.db_path_test


# Global Singleton Instance
app_config = Config()
