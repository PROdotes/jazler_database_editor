from config import DRIVE_MAP, GENRE_RULES
from os import path
from mp3_stuff import get_tag, song_length

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


from typing import List, Dict, Any, Tuple, Optional

def get_location(artist: str, title: str, genre: str, year: int) -> str:
    genre = genre.lower()
    filename = f'{artist} - {title}.mp3'
    
    # Check overrides
    if genre in GENRE_RULES["path_overrides"]:
        folder = GENRE_RULES["path_overrides"][genre]
        return path.join(folder, filename)

    folder = f'z:\\songs\\{genre}\\{year}\\'.lower()
    
    if genre in GENRE_RULES["no_year_subfolder"]:
        folder = f'z:\\songs\\{genre}\\'.lower()
        
    if genre in GENRE_RULES["no_genre_subfolder"]:
        folder = f'z:\\songs\\{year}\\'.lower()

    return path.join(folder, filename)


def list_to_string(genre0: str, strings: List[str]) -> str:
    return ', '.join(strings).replace(f', {genre0}', "")


def calc_decade(year: Any) -> str:
    if year == "" or year is None:
        return "Not Entered"
    else:
        year = int(year)
        return str(year - year % 10) + "'s"


def get_genre_id(genre: str, reverse_genre_map: Dict[str, int]) -> int:
    genre = genre.lower()
    if genre in reverse_genre_map:
        return reverse_genre_map[genre]
    else:
        return -1


def check_genre(database_genre: str, id3_genre: str) -> bool:
    list_db = list(dict.fromkeys(database_genre.split(", ")))[:3]
    list_id3 = list(dict.fromkeys(id3_genre.split(", ")))
    for item in list_db:
        if item not in list_id3:
            print("Genre mismatch")
            print("DB: ", item)
            print("ID3: ", list_id3)
            return False
    return True


def get_data(database_entry: Tuple[Any, ...], genre_map: Dict[int, str], decade_map: Dict[int, str], tempo_map: Dict[int, str]) -> Tuple[Song, Optional[SongID3]]:
    song = Song(database_entry, genre_map, decade_map, tempo_map)

    song.id3_data()
    if song.duration == 0:
        song.duration = song_length(song.location_local)
    print(song.location_local)

    if song.exists:
        tag = None
        try:
            tag = get_tag(song.location_local)
            id3_error = ""
        except Exception as e:
            print(f"---Error while reading tag: {e}")
            id3_error = "ID3 error"
        # Using safely imported mutagen specific logic or just dict access if get_tag returns dict-like
        # mp3_stuff.get_tag returns MP3 object which is dict-like
        id3 = SongID3(tag.get("TPE1"), tag.get("TIT2"), tag.get("TCOM"), tag.get("TALB"), tag.get("TDRC"),
                      tag.get("TCON"), tag.get("TPUB"), tag.get("TSRC"), tag.get("TLEN"), id3_error)
        if id3.duration == "":
            id3.duration = song_length(song.location_local)
        return song, id3
    else:
        print("File does not exist")
        return song, None





class Song:
    def __init__(self, input_data: Tuple[Any, ...], genres: Dict[int, str], decades: Dict[int, str], tempos: Dict[int, str]):
        print(input_data)
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
        self.genres_all = list_to_string(genres[0], [self.genre_01_name, self.genre_02_name, self.genre_03_name])
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
        for k, v in DRIVE_MAP.items():
            self.location_local = self.location_local.replace(k, v)
            
        self.composer = input_data[IDX_COMPOSER]
        self.album = input_data[IDX_ALBUM]
        self.isrc = input_data[IDX_ISRC]
        self.publisher = input_data[IDX_PUBLISHER]
        self.artist = input_data[IDX_ARTIST_NAME]
        self.exists = path.isfile(self.location_local)
        self.location_correct = get_location(self.artist, self.title, self.genre_01_name, self.year)

    def basic_data(self) -> None:
        print(f'Artist: {self.artist}, Title: {self.title}, Album: {self.album}')

    def id3_data(self) -> None:
        print(f'Artist: {self.artist}, Title: {self.title}, Composer: {self.composer}, Album: {self.album}, '
              f'Year: {self.year}, Genres: {self.genres_all}, Decade: {self.decade}, Tempo: {self.tempo}, Publisher: {self.publisher}, '
              f'ISRC: {self.isrc}, ID: {self.id}', f'Duration: {self.duration} seconds')


class SongID3:
    def __init__(self, artist: str, title: str, composer: str, album: str, year: Optional[int], genres: str, publisher: str, isrc: str, duration: float, error: str):
        self.artist = artist
        self.title = title
        self.composer = composer
        self.album = album
        if year is None:
            self.year = 0
        else:
            self.year = int(str(year))
        self.genres_all = str(genres).lower()
        self.publisher = publisher
        self.isrc = isrc
        self.duration = duration
        self.error = error
        if self.error == "":
            self.error = "No error"



