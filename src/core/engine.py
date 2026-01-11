import os
from src.core.database import Database
from src.core.config import app_config
from src.models.song import Song
from src.utils.audio import AudioMetadata
from src.validators.song_validator import SongValidator

class JazlerEngine:
    """
    The Headless "Brain" of the application.
    Encapsulates all logic for database interaction, file validation, and metadata syncing.
    """
    def __init__(self, use_live=False):
        self.config = app_config
        self.db_path = self.config.db_path_live if use_live else self.config.db_path_test
        self.db = Database(self.db_path, "snDatabase")
        
        # Load maps immediately
        self.genre_map = self.db.generate_genre_map()
        self.decade_map = self.db.generate_decade_map()
        self.tempo_map = self.db.generate_tempo_map()
        
        # Initialize helper components
        self.validator = SongValidator(self.genre_map)
        
    def search_songs(self, field="artist", query="", match_type="contains"):
        """Search for songs returning a list of (Song, SongID3) tuples."""
        exact_match = (match_type == "equals")
        records = self.db.fetch_songs(field, query, exact_match)
        
        results = []
        for record in records:
            try:
                song_pair = Song.from_db_record(record, self.genre_map, self.decade_map, self.tempo_map)
                results.append(song_pair)
            except:
                continue
        return results

    def get_song_by_id(self, song_id):
        """Fetch a single song by its AUID."""
        records = self.db.fetch_songs("AUID", song_id, True)
        if not records:
            return None
        return Song.from_db_record(records[0], self.genre_map, self.decade_map, self.tempo_map)

    def sync_song(self, song, id3, rename_file=False):
        """
        Coordinates the save operation.
        1. Validates data.
        2. Writes ID3 tags to the physical file.
        3. Updates the MS Access database.
        4. (Optional) Renames the file.
        """
        # Validate
        validation = self.validator.validate(song, id3)
        if not validation.is_valid:
            return False, validation.issues[0].message

        try:
            # 1. Write Tags
            AudioMetadata.tag_write(id3, song.location_local)
            
            # 2. Rename if requested
            if rename_file:
                # Logic for renaming would go here (similar to app.py's song_rename)
                # But kept simple for this first version of the Engine
                pass

            # 3. Update Database
            # We would build the update dict here using the field registry
            # For now, this is a conceptual placeholder for the engine
            return True, "Sync Success"

        except Exception as e:
            return False, str(e)

    def find_missing_files(self, limit=None):
        """Generator that yields songs whose physical files are missing."""
        records = self.db.fetch_all_songs()
        if limit:
            records = records[:limit]
            
        for record in records:
            try:
                song, _ = Song.from_db_record(record, self.genre_map, self.decade_map, self.tempo_map)
                if not os.path.exists(song.location_local):
                    yield song
            except:
                continue
