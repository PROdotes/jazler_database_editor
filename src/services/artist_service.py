import logging
from typing import List, Optional, Dict, Any
from src.core.models.record import Record

from src.services.lookup_service import LookupService

logger = logging.getLogger(__name__)

class ArtistService:
    """
    Service for managing Artists (snArtists table).
    Extends generic lookup functionality but with specific artist logic.
    """
    
    def __init__(self, backend, registry):
        self.backend = backend
        self.registry = registry
        self.table_name = "snArtists"
        
    def search(self, query: str, limit: int = 20) -> List[Record]:
        """Search artists by name."""
        if not query:
            return []
            
        return self.backend.search(
            table=self.table_name,
            column="fldName",
            value=query,
            match_type="contains"
        )

    def get_by_id(self, artist_id: int) -> Optional[Record]:
        """Get artist by ID."""
        data = self.backend.fetch_one(
            self.table_name, 
            artist_id, 
            primary_key_column="AUID"
        )
        if data:
            return Record(data, self.registry.get_table(self.table_name))
        return None

    def get_by_name(self, name: str) -> Optional[Record]:
        """Find exact match for artist name."""
        results = self.backend.fetch(
            self.table_name,
            filters={"fldName": name},
            limit=1
        )
        if results:
            return Record(results[0], self.registry.get_table(self.table_name))
        return None

    def create(self, name: str, surname: str = "", artist_type: int = 0) -> int:
        """
        Create a new artist.
        Returns the new Artist ID.
        """
        # Check if exists first
        existing = self.get_by_name(name)
        if existing:
            return existing['AUID']
            
        data = {
            "fldName": name,
            "fldSurname": surname,
            "fldArtistType": artist_type
            # Default other fields (F1, F2...) will be handled by DB or ignored
        }
        
        pk = self.backend.insert(self.table_name, data)
        logger.info(f"Created new artist '{name}' with ID {pk}")
        return pk

    def update(self, artist_id: int, data: Dict[str, Any]) -> bool:
        """Update artist details."""
        return self.backend.update(
            self.table_name, 
            artist_id, 
            data,
            primary_key_column="AUID"
        )
