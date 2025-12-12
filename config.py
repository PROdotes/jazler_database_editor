import json
from os import path

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

def load_config():
    if not path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded = json.load(f)
            # Ensure new keys exist if loading old config
            if "genre_rules" not in loaded:
                loaded["genre_rules"] = DEFAULT_CONFIG["genre_rules"]
            return loaded
    except Exception:
        return DEFAULT_CONFIG

config = load_config()

DB_PATH_LIVE = config.get("db_path_live", DEFAULT_CONFIG["db_path_live"])
DB_PATH_TEST = config.get("db_path_test", DEFAULT_CONFIG["db_path_test"])
DRIVE_MAP = config.get("drive_map", DEFAULT_CONFIG["drive_map"])
GENRE_RULES = config.get("genre_rules", DEFAULT_CONFIG["genre_rules"])

def save_last_query(field, match, value):
    try:
        current_config = load_config()
        current_config["last_query"] = {
            "field": field,
            "match": match,
            "value": value
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
    except Exception as e:
        print(f"Error saving last query: {e}")

def load_last_query():
    try:
        current_config = load_config()
        return current_config.get("last_query", None)
    except Exception:
        return None
