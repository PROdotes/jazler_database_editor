from typing import Dict
from src.models.song import Song, SongID3
from src.validators.validation_result import ValidationResult
from src.core.config import app_config

class SongValidator:
    def __init__(self, genre_map: Dict[int, str]):
        self.genre_map = genre_map

    def validate(self, song: Song, id3: SongID3) -> ValidationResult:
        """
        Validates the song state for saving.
        Assumes song.genres_all has been normalized and song.genre_0X_id/name have been updated.
        """
        result = ValidationResult()
        
        # 1. Field Validation
        if not self._validate_fields(song, id3, result):
            return result
            
        # 2. Year Validation
        if not self._validate_year(song, result):
            return result
            
        # 3. Genre Validation
        if not self._validate_genres(song, id3, result):
            return result
            
        # 4. Path Validation
        self._validate_path(song, result)
        
        return result

    def _validate_fields(self, song: Song, id3: SongID3, result: ValidationResult) -> bool:
        attributes = ['artist', 'title', 'album', 'year', 'composer', 'publisher']
        
        for attr in attributes:
            val_song = getattr(song, attr)
            
            # Check if set
            if val_song is None or val_song == "":
                 result.add_error(f"'{attr}' not set!", attr)
                 return False # Fail fast to match legacy behavior
                 
            val_song_str = str(val_song)
            val_id3_str = str(getattr(id3, attr))
            
            # Check match
            if attr == 'artist':
                if val_song_str and not val_id3_str.startswith(val_song_str):
                    result.add_error(f"'{attr}' not the same!", attr)
                    return False
            else:
                if val_song_str != val_id3_str:
                    result.add_error(f"'{attr}' not the same!", attr)
                    return False

        if not song.isrc == id3.isrc:
             # ISRC mismatch prevents save but had no explicit message in old code
             # We'll add one for clarity, or keep it silent if necessary?
             # Old code just returned False.
             result.add_error("ISRC mismatch", "isrc")
             return False
             
        return True

    def _validate_year(self, song: Song, result: ValidationResult) -> bool:
        if song.year == 0:
            result.add_error("Year not set!", "year")
            return False
        return True

    def _validate_genres(self, song: Song, id3: SongID3, result: ValidationResult) -> bool:
        # Check if genres exist in map
        # song.genres_all is expected to be normalized (no 'x' unless empty)
        
        current_genres = [g for g in song.genres_all.split(", ") if g and g != self.genre_map[0]]
        
        # Check validity (limit to 3)
        for genre in current_genres[:3]:
            # self.genre_map.values() contains all valid genre names
            if genre not in self.genre_map.values():
                result.add_error(f"Genre '{genre}' not found!", "genre")
                return False
                
        # Check vs ID3
        if not Song.check_genre(song.genres_all, id3.genres_all):
             result.add_error("Genres not the same!", "genre")
             return False
             
        return True

    def _validate_path(self, song: Song, result: ValidationResult) -> bool:
        g1 = song.genre_01_name.lower()
        rules = app_config.genre_rules

        # Safety check for missing config keys
        standard = rules.get("standard_subfolder", [])
        overrides = rules.get("path_overrides", {})
        no_year = rules.get("no_year_subfolder", [])
        no_genre = rules.get("no_genre_subfolder", [])

        is_standard = g1 in standard
        is_special = (g1 in overrides or g1 in no_year or g1 in no_genre)

        if not is_standard and not is_special:
             result.add_error(f"Genre '{song.genre_01_name}' is not defined in config rules!", "path")
             return False

        is_path_correct = song.location_local.lower() == song.location_correct.lower()
        if not is_path_correct:
             if is_standard:
                  result.add_error(f"File is in the wrong folder!\nExpected: {song.location_correct}", "path")
                  return False

        return True
