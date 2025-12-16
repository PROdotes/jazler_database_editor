import pytest
import os
from unittest.mock import MagicMock, patch
from src.models.song import Song, SongID3

# Helper to create a dummy record
def create_dummy_db_record(id=1, artist="Artist", title="Title", genre1=1, year=2000, filename="z:\\songs\\Pop\\2000\\Artist - Title.mp3", duration=180.0):
    record = [None] * 40
    record[0] = id
    record[1] = 100 # ArtistID
    record[2] = title
    record[3] = genre1
    record[4] = 0
    record[5] = 0
    record[6] = 0 # Genre 4
    record[7] = 0 # Genre 5
    record[8] = year
    record[12] = True
    record[13] = True
    record[14] = duration
    record[20] = filename
    record[24] = "Composer"
    record[25] = "Album"
    record[27] = "ISRC"
    record[32] = "Publisher"
    record[36] = artist
    return tuple(record)

@pytest.fixture
def genre_map():
    return {1: "Pop", 2: "Rock", 0: "Unknown"}

@pytest.fixture
def decade_map():
    return {1: "1990s", 0: "Unknown"}

@pytest.fixture
def tempo_map():
    return {1: "Fast", 0: "Unknown"}

def test_song_initialization(genre_map, decade_map, tempo_map):
    record = create_dummy_db_record()
    song = Song(record, genre_map, decade_map, tempo_map)
    assert song.title == "Title"

def test_song_init_invalid_year(genre_map, decade_map, tempo_map):
    """Test handling of invalid year from DB."""
    record = create_dummy_db_record(year="Corrupt")
    song = Song(record, genre_map, decade_map, tempo_map)
    assert song.year == 0

def test_song_str_repr(genre_map, decade_map, tempo_map):
    """Test string representations."""
    record = create_dummy_db_record(id=99, artist="Cher", title="Believe")
    song = Song(record, genre_map, decade_map, tempo_map)
    
    assert "Cher" in str(song)
    assert "<Song id=99" in repr(song)

def test_song_path_logic_overrides(genre_map, decade_map, tempo_map, mock_config):
    """Test path generation with specific genre rules."""
    mock_config._data["genre_rules"] = {
        "path_overrides": {"cro": "z:\\custom\\"},
        "no_year_subfolder": ["rock"],
        "no_genre_subfolder": ["special"]
    }
    
    record = create_dummy_db_record(genre1=1, year=2020)
    custom_map = {1: "cro", 0: "Unknown"}
    song = Song(record, custom_map, decade_map, tempo_map)
    assert song.get_expected_path() == "z:\\custom\\Artist - Title.mp3"
    
    custom_map_2 = {1: "rock", 0: "Unknown"}
    song2 = Song(record, custom_map_2, decade_map, tempo_map)
    assert song2.get_expected_path() == "z:\\songs\\rock\\Artist - Title.mp3"
    
    custom_map_3 = {1: "special", 0: "Unknown"}
    song3 = Song(record, custom_map_3, decade_map, tempo_map)
    assert song3.get_expected_path() == "z:\\songs\\2020\\Artist - Title.mp3"

# -- Song Factory & Edge Cases --

@patch('src.models.song.AudioMetadata')
@patch('src.models.song.path.isfile')
def test_song_from_db_record_normal(mock_isfile, mock_audio, genre_map, decade_map, tempo_map):
    """Test normal factory flow."""
    mock_isfile.return_value = True
    mock_audio.get_tag.return_value = {"TIT2": "Title"}
    mock_audio.song_length.return_value = 180.0
    
    record = create_dummy_db_record()
    song, id3 = Song.from_db_record(record, genre_map, decade_map, tempo_map)
    
    assert isinstance(song, Song)
    assert id3 is not None
    assert id3.title == "Title"

@patch('src.models.song.AudioMetadata')
@patch('src.models.song.path.isfile')
def test_song_from_db_record_missing_file(mock_isfile, mock_audio, genre_map, decade_map, tempo_map):
    """Test factory when file missing."""
    mock_isfile.return_value = False
    
    record = create_dummy_db_record()
    song, id3 = Song.from_db_record(record, genre_map, decade_map, tempo_map)
    
    assert song.exists is False
    assert id3 is None

@patch('src.models.song.AudioMetadata')
@patch('src.models.song.path.isfile')
def test_song_from_db_record_zero_duration(mock_isfile, mock_audio, genre_map, decade_map, tempo_map):
    """Test logic refetching duration if DB has 0."""
    mock_isfile.return_value = True
    mock_audio.song_length.return_value = 123.4
    mock_audio.get_tag.return_value = {}
    
    record = create_dummy_db_record(duration=0) # DB says 0
    song, id3 = Song.from_db_record(record, genre_map, decade_map, tempo_map)
    
    assert song.duration == 123.4  # Updated from file
    mock_audio.song_length.assert_called()

@patch('src.models.song.AudioMetadata')
@patch('src.models.song.path.isfile')
def test_song_from_db_record_id3_error(mock_isfile, mock_audio, genre_map, decade_map, tempo_map):
    """Test robust handling of ID3 read failures."""
    mock_isfile.return_value = True
    mock_audio.get_tag.side_effect = Exception("Corrupt Tag")
    mock_audio.song_length.return_value = 100.0
    
    record = create_dummy_db_record()
    song, id3 = Song.from_db_record(record, genre_map, decade_map, tempo_map)
    
    assert id3.error == "ID3 error"
    # It should fallback to song length for ID3 duration if tag failed and duration missing
    assert id3.duration == 100.0

# -- ID3 Specific Edge Cases --

def test_song_id3_invalid_year():
    """Test parsing invalid year in ID3."""
    id3 = SongID3("A", "T", "C", "A", "NotAYear", "G", "P", "I", 100, "")
    assert id3.year == 0
    
    id3_partial = SongID3("A", "T", "C", "A", "2020-05-01", "G", "P", "I", 100, "")
    assert id3_partial.year == 2020

def test_song_id3_repr():
    id3 = SongID3("Artist", "Title", "C", "A", 2000, "G", "P", "I", 100, "")
    assert "<SongID3 artist='Artist'" in repr(id3)

# -- Static Methods --

def test_check_genre_logic():
    # Basic Case Insensitive Match
    assert Song.check_genre("Pop", "Pop") is True
    assert Song.check_genre("Pop", "pop") is True # Now case insensitive
    
    # Partial Substring Match
    assert Song.check_genre("Zabavne", "Cro Zabavne") is True
    assert Song.check_genre("Zabavne", "zabavne") is True
    assert Song.check_genre("Pop", "k-pop") is True 
    assert Song.check_genre("Rock", "Pop") is False
    
    # "za obradu" Exclusion
    assert Song.check_genre("za obradu", "Anything") is True # Exception
    assert Song.check_genre("Pop, za obradu", "Pop") is True # Pop matches, za obradu skipped
    assert Song.check_genre("Pop, za obradu", "Rock") is False # Pop mismatch
    
    # Specific User Scenario
    # DB: "Zabavne, Za obradu, Za obradu" (Duplicates handled by logic)
    # ID3: "zabavne"
    assert Song.check_genre("Zabavne, Za obradu, Za obradu", "zabavne") is True
    assert Song.check_genre("Za obradu, Zabavne", "zabavne") is True

def test_calc_decade():
    assert Song.calc_decade(1995) == "1990's"
    assert Song.calc_decade("2002") == "2000's"
    assert Song.calc_decade("") == "Not Entered"
    assert Song.calc_decade(None) == "Not Entered"

def test_get_genre_id():
    rev_map = {"pop": 1, "rock": 2} # keys must be lower per code logic?
    # Code: genre = genre.lower()... if genre in reverse_genre_map...
    
    assert Song.get_genre_id("Pop", rev_map) == 1
    assert Song.get_genre_id("Jazz", rev_map) == -1
