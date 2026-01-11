import csv
import json
import io
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ExportService:
    """
    Handles exporting database records to various formats.
    """
    
    def __init__(self, song_service):
        self.song_service = song_service

    def to_csv(self, records: List[Any], include_resolved: bool = True) -> str:
        """
        Export list of Records to CSV string.
        """
        if not records:
            return ""

        output = io.StringIO()
        
        # Get all keys from the first record as header
        # We use display names or aliases for better readability
        field_names = [
            'id', 'artist', 'title', 'album', 'year', 'filename', 
            'genre', 'decade', 'tempo', 'composer', 'publisher', 'bpm'
        ]
        
        writer = csv.DictWriter(output, fieldnames=field_names, extrasaction='ignore')
        writer.writeheader()

        # Prepare lookup maps if resolving
        genre_map = self.song_service.genre_map if include_resolved else {}
        decade_map = self.song_service.decade_map if include_resolved else {}
        tempo_map = self.song_service.tempo_map if include_resolved else {}

        for record in records:
            row = record.to_dict(use_display_names=True)
            
            # Add alias-mapped basics
            entry = {
                'id': record.primary_key,
                'artist': record.artist,
                'title': record.title,
                'album': record.album,
                'year': record.year,
                'filename': record.filename,
                'composer': record.composer,
                'publisher': record.publisher,
                'bpm': record.get('bpm')
            }

            # Handle resolved lookups
            if include_resolved:
                entry['genre'] = genre_map.get(record.genre, record.genre)
                entry['decade'] = decade_map.get(record.decade, record.decade)
                entry['tempo'] = tempo_map.get(record.tempo, record.tempo)
            else:
                entry['genre'] = record.genre
                entry['decade'] = record.decade
                entry['tempo'] = record.tempo

            writer.writerow(entry)

        return output.getvalue()

    def to_json(self, records: List[Any], include_resolved: bool = True) -> str:
        """
        Export list of Records to JSON string.
        """
        data = []
        
        genre_map = self.song_service.genre_map if include_resolved else {}
        decade_map = self.song_service.decade_map if include_resolved else {}
        tempo_map = self.song_service.tempo_map if include_resolved else {}

        for record in records:
            entry = record.to_dict()
            if include_resolved:
                # Add human-readable versions
                entry['genre_name'] = genre_map.get(record.genre)
                entry['decade_name'] = decade_map.get(record.decade)
                entry['tempo_name'] = tempo_map.get(record.tempo)
            data.append(entry)

        def datetime_handler(x):
            if isinstance(x, datetime):
                return x.isoformat()
            raise TypeError("Unknown type")

        return json.dumps(data, default=datetime_handler, indent=4)
