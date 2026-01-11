import json
import os
import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class SchemaSettingsService:
    """
    Manages persistence for schema browsing preferences,
    such as hidden tables and hidden fields.
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.hidden_tables: Set[str] = set()
        self.hidden_fields: Dict[str, Set[str]] = {} # table_name -> set(field_names)
        self.show_hidden = False
        self.load()

    def load(self):
        """Load settings from JSON file."""
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                self.hidden_tables = set(data.get('hidden_tables', []))
                
                hf = data.get('hidden_fields', {})
                self.hidden_fields = {k: set(v) for k, v in hf.items()}
                
                self.show_hidden = data.get('show_hidden', False)
            logger.info(f"Loaded schema settings from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load schema settings: {e}")

    def save(self):
        """Save settings to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {
                'hidden_tables': list(self.hidden_tables),
                'hidden_fields': {k: list(v) for k, v in self.hidden_fields.items()},
                'show_hidden': self.show_hidden
            }
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save schema settings: {e}")

    def toggle_table_visibility(self, table_name: str):
        """Toggle whether a table is hidden."""
        if table_name in self.hidden_tables:
            self.hidden_tables.remove(table_name)
        else:
            self.hidden_tables.add(table_name)
        self.save()

    def is_table_hidden(self, table_name: str) -> bool:
        return table_name in self.hidden_tables

    def toggle_field_visibility(self, table_name: str, field_name: str):
        """Toggle whether a field in a table is hidden."""
        if table_name not in self.hidden_fields:
            self.hidden_fields[table_name] = set()
        
        if field_name in self.hidden_fields[table_name]:
            self.hidden_fields[table_name].remove(field_name)
        else:
            self.hidden_fields[table_name].add(field_name)
        self.save()

    def is_field_hidden(self, table_name: str, field_name: str) -> bool:
        return field_name in self.hidden_fields.get(table_name, set())

    def toggle_show_hidden(self):
        """Toggle global view of hidden items."""
        self.show_hidden = not self.show_hidden
        self.save()
