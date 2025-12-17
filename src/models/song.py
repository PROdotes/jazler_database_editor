from src.core.config import app_config
from os import path
from src.utils.audio import AudioMetadata
from typing import List, Dict, Any, Tuple, Optional
from src.utils.error_handler import ErrorHandler

# DB Column Indices
IDX_ID = 0
IDX_ARTIST_ID = 1
IDX_TITLE = 2
IDX_GENRE_1_ID = 3
IDX_GENRE_2_ID = 4
IDX_GENRE_3_ID = 5
IDX_GENRE_4_ID = 6
IDX_GENRE_5_ID = 7
IDX_YEAR = 8
IDX_ENABLED = 12
IDX_AUTOPLAY = 13
IDX_DURATION = 14
IDX_FILENAME = 20
IDX_COMPOSER = 24
IDX_ALBUM = 25
IDX_ISRC = 27
IDX_PUBLISHER = 32
IDX_ARTIST_NAME = 36


class Song:
    def __init__(self, input_data: Tuple[Any, ...], genres: Dict[int, str], decades: Dict[int, str], tempos: Dict[int, str]):
        self.id = input_data[IDX_ID]
        self.artist_id = input_data[IDX_ARTIST_ID]
        self.title = input_data[IDX_TITLE]
        self.genre_01_id = input_data[IDX_GENRE_1_ID]
        self.genre_01_name = genres[self.genre_01_id]
        self.genre_02_id = input_data[IDX_GENRE_2_ID]
        self.genre_02_name = genres[self.genre_02_id]
        self.genre_03_id = input_data[IDX_GENRE_3_ID]
        self.genre_03_name = genres[self.genre_03_id]
        self.genre_04_id = input_data[IDX_GENRE_4_ID]
        self.genre_04_name = decades[self.genre_04_id]
        self.genre_05_id = input_data[IDX_GENRE_5_ID]
        self.genre_05_name = tempos[self.genre_05_id]
        
        self.genres_all = Song.list_to_string(genres[0], [self.genre_01_name, self.genre_02_name, self.genre_03_name])
        self.decade = self.genre_04_name
        self.tempo = self.genre_05_name
        
        try:
            self.year = int(input_data[IDX_YEAR])
        except (ValueError, TypeError):
            self.year = 0
            
        self.enabled = input_data[IDX_ENABLED]
        self.auto_play = input_data[IDX_AUTOPLAY]
        self.duration = input_data[IDX_DURATION]
        self.location = input_data[IDX_FILENAME]
        
        # Apply drive mapping
        self.location_local = self.location.lower()
        for k, v in app_config.drive_map.items():
            self.location_local = self.location_local.replace(k, v)
            
        self.composer = input_data[IDX_COMPOSER]
        self.album = input_data[IDX_ALBUM]
        self.isrc = input_data[IDX_ISRC]
        self.publisher = input_data[IDX_PUBLISHER]
        self.artist = input_data[IDX_ARTIST_NAME]
        
        self.exists = path.isfile(self.location_local)
        self.location_correct = self.get_expected_path()

    @classmethod
    def from_db_record(cls, database_entry: Tuple[Any, ...], genre_map: Dict[int, str], decade_map: Dict[int, str], tempo_map: Dict[int, str]) -> Tuple['Song', Optional['SongID3']]:
        song = cls(database_entry, genre_map, decade_map, tempo_map)

        # song.id3_data() # Removed debug print
        if song.duration == 0:
            song.duration = AudioMetadata.song_length(song.location_local)
        
        # print(song.location_local) # Removed debug print

        if song.exists:
            tag = None
            try:
                tag = AudioMetadata.get_tag(song.location_local)
                id3_error = ""
            except Exception as e:
                ErrorHandler.log_silent(e, "Reading ID3 tag")
                id3_error = "ID3 error"
                tag = {}
                
            # Fallback for Year: TDRC (Recording Time) preferred, TYER (Year) fallback for ID3v2.3
            year_tag = tag.get("TDRC")
            if year_tag is None:
                year_tag = tag.get("TYER")
                
            # Fallback for Key/Done: TKEY1 preferred, TKEY as fallback
            key_tag = tag.get("TKEY1")
            if key_tag is None:
                key_tag = tag.get("TKEY")
                
            id3 = SongID3(tag.get("TPE1"), tag.get("TIT2"), tag.get("TCOM"), tag.get("TALB"), year_tag,
                          tag.get("TCON"), tag.get("TPUB"), tag.get("TSRC"), tag.get("TLEN"), key_tag, id3_error)
            
            if id3.duration == "" or id3.duration is None:
                id3.duration = AudioMetadata.song_length(song.location_local)
            return song, id3
        else:
            # print("File does not exist") # Removed debug print, could log instead
            return song, None

    def get_expected_path(self) -> str:
        genre = self.genre_01_name.lower()
        filename = f'{self.artist} - {self.title}.mp3'
        
        # Check overrides
        if genre in app_config.genre_rules["path_overrides"]:
            folder = app_config.genre_rules["path_overrides"][genre]
            return path.join(folder, filename)

        folder = f'z:\\songs\\{genre}\\{self.year}\\'.lower()
        
        if genre in app_config.genre_rules["no_year_subfolder"]:
            folder = f'z:\\songs\\{genre}\\'.lower()
            
        if genre in app_config.genre_rules["no_genre_subfolder"]:
            folder = f'z:\\songs\\{self.year}\\'.lower()

        return path.join(folder, filename)

    @staticmethod
    def list_to_string(genre0: str, strings: List[str]) -> str:
        return ', '.join(strings).replace(f', {genre0}', "")

    @staticmethod
    def calc_decade(year: Any) -> str:
        if year == "" or year is None:
            return "Not Entered"
        else:
            year = int(year)
            return str(year - year % 10) + "'s"

    @staticmethod
    def get_genre_id(genre: str, reverse_genre_map: Dict[str, int]) -> int:
        genre = genre.lower()
        if genre in reverse_genre_map:
            return reverse_genre_map[genre]
        else:
            return -1

    @staticmethod
    def check_genre(database_genre: str, id3_genre: str) -> bool:
        list_db = list(dict.fromkeys(database_genre.split(", ")))[:3]
        list_id3 = list(dict.fromkeys(id3_genre.split(", ")))
        
        for item in list_db:
            item_clean = item.lower().strip()
            
            # Special Exclusion: Database genre "za obradu" doesn't need to be in ID3
            if item_clean == "za obradu":
                continue
                
            found = False
            for id3_item in list_id3:
                # Partial match: DB "Zabavne" matches ID3 "Cro Zabavne"
                if item_clean in id3_item.lower():
                    found = True
                    break
            
            if not found:
                return False
        return True

    def __repr__(self):
        return f"<Song id={self.id} artist='{self.artist}' title='{self.title}'>"

    def normalize_genres(self, default_genre: str):
        """
        Deduplicates genres and reformats the genres_all string.
        """
        genre_list = self.genres_all.split(", ")
        # Deduplicate preserving order
        genre_list = list(dict.fromkeys(genre_list))
        self.genres_all = Song.list_to_string(default_genre, genre_list)

    def update_genre_ids(self, reverse_genre_map: Dict[str, int], default_genre: str):
        """
        Updates individual genre fields (01-03) based on genres_all string.
        """
        # Re-parse from the normalized string (logic mirrors app.py)
        # However, list_to_string removes the default genre. 
        # app.py logic uses the list BEFORE stringification for setting IDs?
        # No, app.py uses `genre_ids` which was deduped list.
        # But `list_to_string` filters out `default_genre` (usually 'x').
        
        # If we re-split self.genres_all, we get the valid genres.
        current_genres = [g for g in self.genres_all.split(", ") if g and g != default_genre]
        
        # Ensure at least 3 slots
        self.genre_01_name = current_genres[0] if len(current_genres) > 0 else default_genre
        self.genre_01_id = Song.get_genre_id(self.genre_01_name, reverse_genre_map)
        
        self.genre_02_name = current_genres[1] if len(current_genres) > 1 else default_genre
        self.genre_02_id = Song.get_genre_id(self.genre_02_name, reverse_genre_map)
        
        self.genre_03_name = current_genres[2] if len(current_genres) > 2 else default_genre
        self.genre_03_id = Song.get_genre_id(self.genre_03_name, reverse_genre_map)

    def __str__(self):
        return f"{self.artist} - {self.title} ({self.year})"


class SongID3:
    def __init__(self, artist: str, title: str, composer: str, album: str, year: Optional[int], genres: str, publisher: str, isrc: str, duration: float, key: str, error: str):
        self.artist = artist
        self.title = title
        self.composer = composer
        self.album = album
        if year is None:
            self.year = 0
        else:
            try:
                # TDRC might be a full date like '2025-04-24'
                # Extract first 4 chars which SHOULD be the year
                cleaned_year = str(year).strip()[:4]
                self.year = int(cleaned_year)
            except ValueError:
                self.year = 0
        self.genres_all = str(genres).lower()
        self.publisher = publisher
        self.isrc = isrc
        self.duration = duration
        # Store key raw or logical? Java stores "true"/"false" string in DB/ID3?
        # Java checkDone.setSelected(id3Data.getData(ID3Header.KEY).equals("true"));
        # So it expects the string "true".
        self.done = str(key).lower() == "true"
        self.error = error
        if self.error == "":
            self.error = "No error"
            
    def __repr__(self):
        return f"<SongID3 artist='{self.artist}' title='{self.title}'>"
