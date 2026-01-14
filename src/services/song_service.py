"""
Song Service - orchestrates song-related operations.

Provides high-level operations for:
- Searching songs
- Getting song by ID
- Updating songs
- Loading lookup maps (genre, decade, tempo)
"""

import logging
from typing import Dict, Any, Optional, List
from src.backends.base import Backend
from src.core.schema.registry import SchemaRegistry
from src.core.models.record import Record, RecordSet

logger = logging.getLogger(__name__)


class SongService:
    """
    Service for song-related operations.
    
    Usage:
        service = SongService(backend, registry)
        
        # Search
        results = service.search("artist", "Beatles")
        
        # Get by ID
        song = service.get_by_id(12345)
        
        # Update
        song.title = "New Title"
        service.save(song)
    """
    
    # Default table name for songs
    DEFAULT_TABLE = "snDatabase"
    DEFAULT_PK = "AUID"
    
    def __init__(self, backend: Backend, registry: SchemaRegistry):
        """
        Initialize song service.
        
        Args:
            backend: Database backend
            registry: Schema registry with table definitions
        """
        self.backend = backend
        self.registry = registry
        self._table = self.DEFAULT_TABLE
        self._schema = registry.get_table(self._table)
        
        # Lookup maps (lazy loaded)
        self._genre_map: Optional[Dict[int, str]] = None
        self._decade_map: Optional[Dict[int, str]] = None
        self._tempo_map: Optional[Dict[int, str]] = None
    
    # ─────────────────────────────────────────────────────────────
    # Lookup Maps
    # ─────────────────────────────────────────────────────────────
    
    def _load_lookup_map(self, table: str, key_col: str = "AUID", value_col: str = "fldMusicType") -> Dict[int, str]:
        """Load a lookup table into a dict."""
        try:
            rows = self.backend.fetch(table, columns=[key_col, value_col], limit=1000)
            return {int(row[key_col]): row[value_col] for row in rows if row[key_col] is not None}
        except Exception as e:
            logger.warning(f"Could not load lookup table '{table}': {e}")
            return {}
    
    @property
    def genre_map(self) -> Dict[int, str]:
        """Get genre ID -> name mapping."""
        if self._genre_map is None:
            self._genre_map = self._load_lookup_map("snCat1", "AUID", "fldMusicType")
            self._genre_map[0] = ""  # Handle null/zero genre
        return self._genre_map
    
    @property
    def decade_map(self) -> Dict[int, str]:
        """Get decade ID -> name mapping."""
        if self._decade_map is None:
            self._decade_map = self._load_lookup_map("snCat2", "AUID", "fldMusicType")
            self._decade_map[0] = ""
        return self._decade_map
    
    @property
    def tempo_map(self) -> Dict[int, str]:
        """Get tempo ID -> name mapping."""
        if self._tempo_map is None:
            self._tempo_map = self._load_lookup_map("snCat3", "AUID", "fldMusicType")
            self._tempo_map[0] = ""
        return self._tempo_map
    
    def resolve_genre(self, genre_id: int) -> str:
        """Convert genre ID to name."""
        return self.genre_map.get(genre_id, f"Unknown({genre_id})")
    
    def resolve_decade(self, decade_id: int) -> str:
        """Convert decade ID to name."""
        return self.decade_map.get(decade_id, f"Unknown({decade_id})")
    
    def resolve_tempo(self, tempo_id: int) -> str:
        """Convert tempo ID to name."""
        return self.tempo_map.get(tempo_id, f"Unknown({tempo_id})")
    
    # ─────────────────────────────────────────────────────────────
    # CRUD Operations
    # ─────────────────────────────────────────────────────────────
    
    def _row_to_record(self, row: Dict[str, Any]) -> Record:
        """Convert a database row to a Record."""
        return Record(row, self._schema)
    
    def get_by_id(self, song_id: int) -> Optional[Record]:
        """
        Get a song by its primary key (AUID).
        
        Args:
            song_id: The song's AUID
            
        Returns:
            Record if found, None otherwise
        """
        row = self.backend.fetch_one(
            self._table, 
            song_id, 
            primary_key_column=self.DEFAULT_PK
        )
        if row:
            return self._row_to_record(row)
        return None

    def get_all(self, limit: int = 200000) -> RecordSet:
        """
        Get all songs.
        
        Args:
            limit: Maximum number of songs to retrieve (default: 200,000)
            
        Returns:
            RecordSet of all songs
        """
        rows = self.backend.fetch(self._table, limit=limit)
        records = [self._row_to_record(row) for row in rows]
        return RecordSet(records)

    def get_all_paths(self) -> List[str]:
        """Get list of all filenames in DB."""
        # Use a large limit to ensure we get all paths. 
        # Access backend defaults to 100 if not specified.
        rows = self.backend.fetch(self._table, columns=['fldFilename'], limit=200000)
        return [row['fldFilename'] for row in rows if row.get('fldFilename')]

    def get_searchable_fields(self) -> List[tuple[str, str]]:
        """
        Get list of (key, label) for search dropdowns based on Config/Schema.
        """
        fields = []
        # Create reverse alias map for friendly URLs
        reverse_aliases = {}
        if self._schema and self._schema.aliases:
            reverse_aliases = {v: k for k, v in self._schema.aliases.items()}
        
        for col in self._schema.columns:
            if col.display_name and not col.is_ignored:
                # Determine the "key" (url parameter)
                # 1. Use friendly alias if available (e.g. fldArtistName -> artist)
                # 2. Else use column name
                key = reverse_aliases.get(col.name, col.name)
                
                fields.append((key, col.display_name))
        
        # Sort by label for nice UI
        return sorted(fields, key=lambda x: x[1])

    def get_grid_columns(self, view_name: str = 'default') -> List[Any]:
        """
        Get list of column definitions for a named grid view.
        Returns list of objects (col.name, col.label, col.type, etc.)
        """
        col_names = self.registry.get_grid_view(view_name)
        columns = []
        
        if self._schema:
            for name in col_names:
                col = self._schema.get_column(name)
                if col:
                    columns.append(col)
        return columns

    def get_form_fields(self, layout_name: str = 'default') -> List[Any]:
        """
        Get list of field definitions for a named form layout.
        Returns list of objects (col.name, col.label, col.type, etc.)
        """
        layout = self.registry.overrides.get('form_layouts', {}).get(layout_name, ['*'])
        
        fields = []
        if not self._schema:
            return []
            
        if layout == ['*']:
            # Return all non-ignored fields
            return [c for c in self._schema.columns if not c.is_ignored]
            
        for name in layout:
            col = self._schema.get_column(name)
            if col:
                fields.append(col)
        return fields

    def search(
        self, 
        field: str, 
        value: str, 
        match_type: str = "contains",
        limit: int = 1000
    ) -> RecordSet:
        """Legacy search wrapper."""
        return self.search_advanced([{'field': field, 'value': value, 'match': match_type}], limit)

    def search_advanced(self, criteria_list: List[Dict[str, str]], limit: int = 1000) -> RecordSet:
        """
        Multi-criteria search with AND logic.
        
        Args:
            criteria_list: List of dicts with 'field', 'value', 'match'
            limit: Max results
        """
        if not criteria_list:
            return self.get_all(limit)
            
        sql_parts = []
        params = []
        
        for criteria in criteria_list:
            field = criteria.get('field')
            value = criteria.get('value', '').strip()
            match = criteria.get('match', 'contains')
            
            # Resolve field name
            actual_field = self._resolve_field_name(field)
            
            # Handle Lookups (Genre, etc)
            snippet, p = self._build_lookup_filter(actual_field, value, match)
            if snippet:
                sql_parts.append(f"({snippet})")
                params.extend(p)
                continue
                
            # Handle Standard Fields
            snippet, p = self._build_standard_filter(actual_field, value, match)
            if snippet:
                sql_parts.append(f"({snippet})")
                params.extend(p)
                
        if not sql_parts:
            return self.get_all(limit)
            
        where_clause = " AND ".join(sql_parts)
        query = f"SELECT TOP {limit} * FROM [{self._table}] WHERE {where_clause}"
        
        rows = self.backend.fetch_sql(query, tuple(params))
        records = [self._row_to_record(row) for row in rows]
        return RecordSet(records)

    def _build_lookup_filter(self, field: str, value: str, match: str) -> tuple[Optional[str], List[Any]]:
        """Build SQL snippet for lookup fields."""
        lookup_map = None
        if field in ['fldCat1a', 'fldCat1b', 'fldCat1c']:
            self.genre_map # ensure loaded
            lookup_map = self._genre_map
        elif field == 'fldCat2':
            self.decade_map # ensure loaded
            lookup_map = self._decade_map
        elif field == 'fldCat3':
            self.tempo_map # ensure loaded
            lookup_map = self._tempo_map
            
        if not lookup_map or (not value and match != 'is_empty'):
            return None, []
            
        if match == 'is_empty':
             # For numeric IDs, empty is usually 0
            return f"[{field}] = 0 OR [{field}] IS NULL", []

        # Find matching IDs
        matching_ids = []
        search_val_lower = value.lower()
        
        for id_val, name in lookup_map.items():
            if not name: continue
            name_lower = name.lower()
            is_match = False
            
            if match == 'equals': is_match = (name_lower == search_val_lower)
            elif match == 'starts_with': is_match = name_lower.startswith(search_val_lower)
            elif match == 'contains': is_match = (search_val_lower in name_lower)
                
            if is_match: matching_ids.append(id_val)
        
        if not matching_ids:
            return "1=0", [] # Force no match
            
        ids_str = ",".join(str(i) for i in matching_ids)
        
        # Special logic for Genre: search all 3 columns if looking for "Rock"
        if field == 'fldCat1a':
             return f"fldCat1a IN ({ids_str}) OR fldCat1b IN ({ids_str}) OR fldCat1c IN ({ids_str})", []
             
        return f"[{field}] IN ({ids_str})", []

    def _build_standard_filter(self, field: str, value: str, match: str) -> tuple[str, List[Any]]:
        """Build standard Text/Numeric SQL filter."""
        # Determine column type if possible
        is_numeric = False
        if self._schema:
            col = self._schema.get_column(field)
            if col and col.type_name in ('INTEGER', 'LONG', 'SHORT', 'BYTE', 'CURRENCY', 'SINGLE', 'DOUBLE', 'NUMERIC'):
                is_numeric = True

        if match == 'is_empty':
            if is_numeric:
                return f"[{field}] IS NULL OR [{field}] = 0", []
            else:
                return f"[{field}] IS NULL OR [{field}] = ''", []
            
        if match == 'equals':
            return f"[{field}] = ?", [value]
        elif match == 'starts_with':
            return f"[{field}] LIKE ?", [f"{value}%"]
        elif match == 'ends_with':
             return f"[{field}] LIKE ?", [f"%{value}"]
        else: # contains
            return f"[{field}] LIKE ?", [f"%{value}%"]
    
    # FIELD_ALIASES removed - now handled by table schema
    
    def _resolve_field_name(self, field: str) -> str:
        """
        Resolve a field name to the actual column name.
        
        Handles:
        - Direct column names: "fldArtistName"
        - Display names: "Artist" 
        - Aliases: "artist" -> "fldArtistName"
        - Short names: "artistname" -> "fldArtistName"
        """
        if not self._schema:
            return field
        
        # Check direct match (exact column name)
        col = self._schema.get_column(field)
        if col:
            return field
        
        field_lower = field.lower()
        
        # Check display names first (case insensitive)
        for col in self._schema.columns:
            if col.display_name and col.display_name.lower() == field_lower:
                return col.name
                
        # Check aliases from schema
        if self._schema and self._schema.aliases:
            if field_lower in self._schema.aliases:
                return self._schema.aliases[field_lower]
        
        # Check simplified name (fldArtistName -> artistname)
        for col in self._schema.columns:
            simple = col.name.lower()
            if simple.startswith('fld'):
                simple = simple[3:]
            if simple == field_lower:
                return col.name
        
        # Fallback to original (let the database error if invalid)
        return field
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count songs matching filters."""
        return self.backend.count(self._table, filters)
    
    def save(self, record: Record) -> bool:
        """
        Save changes to a song record.
        
        Args:
            record: The Record with changes
            
        Returns:
            True if save was successful
        """
        if not record.has_changes:
            return True  # Nothing to save
        
        pk = record.primary_key
        if pk is None:
            raise ValueError("Cannot save record without primary key")
        
        success = self.backend.update(
            self._table,
            pk,
            record.changes,
            primary_key_column=self.DEFAULT_PK
        )
        
        if success:
            record.clear_changes()
        
        return success
    
    def update_field(self, song_id: int, field: str, value: Any) -> bool:
        """
        Update a single field on a song.
        
        Args:
            song_id: The song's AUID
            field: Field name to update
            value: New value
            
        Returns:
            True if update was successful
        """
        actual_field = self._resolve_field_name(field)
        return self.backend.update(
            self._table,
            song_id,
            {actual_field: value},
            primary_key_column=self.DEFAULT_PK
        )
    
    def update_filename(self, song_id: int, new_filename: str) -> bool:
        """Update the file path for a song."""
        return self.update_field(song_id, "fldFilename", new_filename)
    
    # ─────────────────────────────────────────────────────────────
    # Bulk Operations
    # ─────────────────────────────────────────────────────────────
    
    def get_bulk_summary(self, song_ids: List[int]) -> Dict[str, Any]:
        """
        Analyze a list of songs and find common field values.
        Returns a dict of fields: value (or "__mixed__" if different).
        """
        songs = [self.get_by_id(sid) for sid in song_ids]
        songs = [s for s in songs if s]
        
        if not songs:
            return {}

        fields = ['genre', 'decade', 'tempo', 'album', 'publisher', 'year']
        summary = {f: getattr(songs[0], f) for f in fields}
        
        for s in songs[1:]:
            for f in fields:
                if getattr(s, f) != summary[f]:
                    summary[f] = "__mixed__"
        
        return summary

    def perform_bulk_update(self, song_ids: List[int], updates: Dict[str, Any]) -> int:
        """
        Update multiple songs at once.
        Returns the number of successful updates.
        """
        if not updates:
            return 0
            
        count = 0
        for sid in song_ids:
            try:
                if self.backend.update(self._table, sid, updates, primary_key_column=self.DEFAULT_PK):
                    count += 1
            except Exception as e:
                logger.error(f"Bulk update failed for #{sid}: {e}")
        return count
    
    # ─────────────────────────────────────────────────────────────
    # Enriched Record Access
    # ─────────────────────────────────────────────────────────────
    
    def get_display_data(self, record: Record) -> Dict[str, Any]:
        """
        Get a record with resolved lookups for display.
        
        Returns a dict with:
        - All original fields
        - Resolved genre/decade/tempo names
        - Computed display values
        """
        data = record.raw_data
        
        # Resolve lookups
        cat1a = data.get('fldCat1a', 0) or 0
        cat1b = data.get('fldCat1b', 0) or 0
        cat1c = data.get('fldCat1c', 0) or 0
        
        genres = []
        for gid in [cat1a, cat1b, cat1c]:
            if gid:
                name = self.resolve_genre(gid)
                if name:
                    genres.append(name)
        
        cat2 = data.get('fldCat2', 0) or 0
        cat3 = data.get('fldCat3', 0) or 0
        
        return {
            **data,
            'genres_resolved': genres,
            'genre_display': ', '.join(genres),
            'decade_display': self.resolve_decade(cat2),
            'tempo_display': self.resolve_tempo(cat3),
            # Pass raw duration for precision sync
            'duration_raw': data.get('fldDuration', 0.0)
        }
