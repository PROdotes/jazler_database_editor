import pytest
from unittest.mock import MagicMock, patch
from src.validators.song_validator import SongValidator
from src.models.song import Song, SongID3
from src.validators.validation_result import ValidationResult

class TestSongValidator:
    @pytest.fixture
    def validator(self):
        genre_map = {0: "x", 1: "pop", 2: "rock", 3: "jazz"}
        return SongValidator(genre_map)

    @pytest.fixture
    def mock_song(self):
        song = MagicMock(spec=Song)
        song.artist = "Artist"
        song.title = "Title"
        song.album = "Album"
        song.year = 2000
        song.composer = "Comp"
        song.publisher = "Pub"
        song.isrc = "US12345"
        song.genres_all = "pop, rock"
        song.genre_01_name = "pop"
        song.location_local = "z:\\songs\\pop\\2000\\artist - title.mp3"
        song.location_correct = "z:\\songs\\pop\\2000\\artist - title.mp3"
        return song

    @pytest.fixture
    def mock_id3(self):
        id3 = MagicMock(spec=SongID3)
        id3.artist = "Artist"
        id3.title = "Title"
        id3.album = "Album"
        id3.year = 2000
        id3.composer = "Comp"
        id3.publisher = "Pub"
        id3.isrc = "US12345"
        id3.genres_all = "pop, rock"
        return id3

    def test_validate_success(self, validator, mock_song, mock_id3):
        with patch('src.validators.song_validator.app_config') as mock_config, \
             patch('src.models.song.Song.check_genre', return_value=True):
            
            # Setup genre rules
            mock_config.genre_rules = {
                "standard_subfolder": ["pop"],
                "path_overrides": {},
                "no_year_subfolder": [],
                "no_genre_subfolder": []
            }
            
            result = validator.validate(mock_song, mock_id3)
            assert result.is_valid
            assert len(result.issues) == 0

    def test_validate_field_mismatch(self, validator, mock_song, mock_id3):
        mock_id3.title = "Different Title"
        result = validator.validate(mock_song, mock_id3)
        assert not result.is_valid
        assert len(result.issues) > 0
        assert "not the same" in result.issues[0].message

    def test_validate_year_missing(self, validator, mock_song, mock_id3):
        mock_song.year = 0
        mock_id3.year = 0 # Match ID3 so it doesn't fail on "year not the same"
        result = validator.validate(mock_song, mock_id3)
        assert not result.is_valid
        assert "Year not set" in result.issues[0].message

    def test_validate_genre_invalid(self, validator, mock_song, mock_id3):
        mock_song.genres_all = "invalid_genre"
        result = validator.validate(mock_song, mock_id3)
        assert not result.is_valid
        assert "not found" in result.issues[0].message

    def test_validate_path_mismatch(self, validator, mock_song, mock_id3):
        with patch('src.validators.song_validator.app_config') as mock_config, \
             patch('src.models.song.Song.check_genre', return_value=True):
            
            mock_config.genre_rules = {
                "standard_subfolder": ["pop"],
                "path_overrides": {},
                "no_year_subfolder": [],
                "no_genre_subfolder": []
            }
            
            mock_song.location_local = "z:\\wrong\\path.mp3"
            
            result = validator.validate(mock_song, mock_id3)
            assert not result.is_valid
            assert "wrong folder" in result.issues[0].message
