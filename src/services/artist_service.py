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
        """
        Update artist details.
        If 'fldName' is changed, propagates the new name to all linked songs in snDatabase.
        """
        # 1. Update the artist record itself
        success = self.backend.update(
            self.table_name, 
            artist_id, 
            data,
            primary_key_column="AUID"
        )
        
        if not success:
            logger.error(f"Failed to update artist {artist_id}")
            return False
            
        # 2. If name changed, propagate to snDatabase
        if 'fldName' in data:
            new_name = data['fldName']
            logger.info(f"Propagating artist name change to '{new_name}' for ArtistID {artist_id}")
            
            # Update snDatabase set fldArtistName = ? where fldArtistCode = ?
            query = "UPDATE snDatabase SET fldArtistName = ? WHERE fldArtistCode = ?"
            try:
                self.backend.execute_raw(query, (new_name, artist_id))
            except Exception as e:
                logger.error(f"Failed to propagate artist name: {e}")
                # We log but return True because the primary update succeeded
                # In a perfect world we'd transaction this, but Access logic implies best-effort here
                
        return True

    def merge(self, source_id: int, target_id: int) -> bool:
        """
        Merge source_id INTO target_id.
        1. Move all songs from source to target.
        2. Delete source artist.
        """
        # Get target details for the name
        target = self.get_by_id(target_id)
        if not target:
            logger.error(f"Merge target {target_id} not found")
            return False
            
        target_name = target['fldName']
        
        logger.info(f"Merging Artist {source_id} INTO {target_id} ('{target_name}')")
        
        try:
            # 1. Update all songs
            # Update snDatabase set fldArtistCode = target_id, fldArtistName = target_name where fldArtistCode = source_id
            query = """
                UPDATE snDatabase 
                SET fldArtistCode = ?, fldArtistName = ? 
                WHERE fldArtistCode = ?
            """
            self.backend.execute_raw(query, (target_id, target_name, source_id))
            
            # 2. Delete the source artist
            self.backend.delete(self.table_name, source_id, primary_key_column="AUID")
            
            logger.info(f"Merge complete. Source {source_id} deleted.")
            return True

        except Exception as e:
            logger.error(f"Merge failed: {e}")
            return False

    def get_all_with_counts(self, limit: int = 2000, query_filter: str = None) -> List[Dict[str, Any]]:
        """
        Get all artists with a count of their linked songs.
        Optionally filter by name.
        """
        # Base query
        sql = f"""
            SELECT TOP {limit} a.AUID, a.fldName, COUNT(s.fldArtistCode) as song_count
            FROM snArtists a
            LEFT JOIN snDatabase s ON a.AUID = s.fldArtistCode
            WHERE a.AUID <> 367806
        """
        
        params = []
        if query_filter:
            sql += " AND a.fldName LIKE ?"
            params.append(f"%{query_filter}%")
            
        sql += " GROUP BY a.AUID, a.fldName ORDER BY a.fldName"

        try:
            # logger.info(f"ArtistService: Executing query with limit {limit}, filter='{query_filter}'")
            rows = self.backend.execute_raw(sql, tuple(params))
            # logger.info(f"ArtistService: Query returned {len(rows)} rows")
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'count': row[2]
                })
            return results
        except Exception as e:
            logger.error(f"Failed to get artist counts: {e}", exc_info=True)
            return []
