"""
Integration tests for ImportService with mocked dependencies.

Tests duplicate detection, artist linking, genre/decade resolution,
and the execute import flow.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.services.import_parser import (
    ImportParser, ImportStatus, ImportCandidate, ParsedMetadata, ParseSource
)
from src.services.import_service import ImportService, JazlerDefaults


class TestImportServicePreview:
    """Test the preview_import (dry run) functionality."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock database backend."""
        backend = MagicMock()
        backend.fetch.return_value = []
        backend.insert.return_value = 12345
        backend.update.return_value = True
        return backend

    @pytest.fixture
    def mock_artist_service(self):
        """Create a mock artist service."""
        service = MagicMock()
        service.get_by_name.return_value = None
        service.create.return_value = 100
        return service

    @pytest.fixture
    def mock_song_service(self):
        """Create a mock song service."""
        service = MagicMock()
        service.get_all_paths.return_value = []
        # Genre map: ID -> Name
        type(service).genre_map = PropertyMock(return_value={
            0: "",
            1: "Rock",
            2: "Pop",
            3: "Dance",
            18: "za obradu"
        })
        # Decade map: ID -> Name
        type(service).decade_map = PropertyMock(return_value={
            0: "",
            1: "1970's",
            2: "1980's",
            3: "1990's",
            4: "2000's",
            5: "2010's",
            6: "2020's"
        })
        return service

    @pytest.fixture
    def import_service(self, mock_backend, mock_artist_service, mock_song_service):
        """Create ImportService with mocked dependencies."""
        return ImportService(
            backend=mock_backend,
            artist_service=mock_artist_service,
            song_service=mock_song_service
        )

    # ─────────────────────────────────────────────────────────────
    # Duplicate Detection Tests
    # ─────────────────────────────────────────────────────────────

    def test_detects_duplicate_path(self, import_service, mock_song_service):
        """Test that duplicate paths are detected."""
        mock_song_service.get_all_paths.return_value = ["C:\\Music\\Existing.mp3"]

        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", source=ParseSource.FILENAME, confidence=0.7
            )
            candidates = import_service.preview_import(["C:\\Music\\Existing.mp3"])

        assert len(candidates) == 1
        assert candidates[0].status == ImportStatus.DUPLICATE

    def test_duplicate_detection_case_insensitive(self, import_service, mock_song_service):
        """Test that path comparison is case-insensitive."""
        mock_song_service.get_all_paths.return_value = ["C:\\Music\\EXISTING.MP3"]

        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", source=ParseSource.FILENAME, confidence=0.7
            )
            candidates = import_service.preview_import(["c:\\music\\existing.mp3"])

        assert candidates[0].status == ImportStatus.DUPLICATE

    def test_detects_conflict_artist_title(self, import_service, mock_backend):
        """Test that artist+title conflicts are detected."""
        mock_backend.fetch.return_value = [
            {'AUID': 99, 'fldArtistName': 'Madonna', 'fldTitle': 'Vogue', 'fldFilename': 'B:\\Old.mp3'}
        ]

        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Madonna", title="Vogue", source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\New\\Madonna - Vogue.mp3"])

        assert len(candidates) == 1
        assert candidates[0].status == ImportStatus.CONFLICT
        assert candidates[0].existing_song_id == 99
        assert candidates[0].existing_path == 'B:\\Old.mp3'

    def test_conflict_detection_case_insensitive(self, import_service, mock_backend):
        """Test that artist+title comparison is case-insensitive."""
        mock_backend.fetch.return_value = [
            {'AUID': 99, 'fldArtistName': 'MADONNA', 'fldTitle': 'VOGUE', 'fldFilename': 'B:\\Old.mp3'}
        ]

        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="madonna", title="vogue", source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\New\\file.mp3"])

        assert candidates[0].status == ImportStatus.CONFLICT

    def test_new_file_detected(self, import_service):
        """Test that genuinely new files are detected as NEW."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="NewArtist", title="NewSong", source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\NewArtist - NewSong.mp3"])

        assert len(candidates) == 1
        assert candidates[0].status == ImportStatus.NEW

    # ─────────────────────────────────────────────────────────────
    # Artist Linking Tests
    # ─────────────────────────────────────────────────────────────

    def test_links_existing_artist(self, import_service, mock_artist_service):
        """Test that existing artists are linked."""
        mock_artist_record = MagicMock()
        mock_artist_record.__getitem__ = lambda s, k: 50 if k == 'AUID' else None
        mock_artist_service.get_by_name.return_value = mock_artist_record

        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Queen", title="Bohemian", source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\Queen - Bohemian.mp3"])

        assert candidates[0].artist_id == 50
        assert candidates[0].artist_is_new is False

    def test_marks_new_artist(self, import_service, mock_artist_service):
        """Test that new artists are marked for creation."""
        mock_artist_service.get_by_name.return_value = None

        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="NewBand", title="NewSong", source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\NewBand - NewSong.mp3"])

        assert candidates[0].artist_id is None
        assert candidates[0].artist_is_new is True

    # ─────────────────────────────────────────────────────────────
    # Genre Resolution Tests
    # ─────────────────────────────────────────────────────────────

    def test_resolves_single_genre(self, import_service):
        """Test resolving a single genre from ID3."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", genre="Rock",
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].genre_ids[0] == 1  # Rock = ID 1
        assert candidates[0].genre_ids[1] == 0
        assert candidates[0].genre_ids[2] == 0

    def test_resolves_multiple_genres(self, import_service):
        """Test resolving comma-delimited genres."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", genre="Rock, Pop, Dance",
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].genre_ids[0] == 1  # Rock
        assert candidates[0].genre_ids[1] == 2  # Pop
        assert candidates[0].genre_ids[2] == 3  # Dance

    def test_defaults_to_za_obradu_when_no_match(self, import_service):
        """Test that unmatched genres default to 'za obradu' (ID 18)."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", genre="UnknownGenre",
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].genre_ids[0] == 18  # za obradu
        assert candidates[0].genre_ids[1] == 0
        assert candidates[0].genre_ids[2] == 0

    def test_defaults_to_za_obradu_when_empty(self, import_service):
        """Test that empty genre defaults to 'za obradu' (ID 18)."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", genre="",
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].genre_ids[0] == 18  # za obradu

    def test_genre_matching_case_insensitive(self, import_service):
        """Test that genre matching is case-insensitive."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", genre="ROCK",
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].genre_ids[0] == 1  # Rock

    # ─────────────────────────────────────────────────────────────
    # Decade Resolution Tests
    # ─────────────────────────────────────────────────────────────

    def test_resolves_decade_from_year(self, import_service):
        """Test resolving decade from year."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", year=1985,
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].decade_id == 2  # 1980's

    def test_resolves_decade_2000s(self, import_service):
        """Test resolving decade for 2000s."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", year=2005,
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].decade_id == 4  # 2000's

    def test_decade_zero_when_no_year(self, import_service):
        """Test that decade is 0 when year is missing."""
        with patch.object(import_service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(
                artist="Artist", title="Title", year=0,
                source=ParseSource.ID3, confidence=0.9
            )
            candidates = import_service.preview_import(["C:\\Music\\file.mp3"])

        assert candidates[0].decade_id == 0


class TestImportServiceExecute:
    """Test the execute_import functionality."""

    @pytest.fixture
    def mock_backend(self):
        backend = MagicMock()
        backend.fetch.return_value = []
        backend.insert.return_value = 12345
        backend.update.return_value = True
        return backend

    @pytest.fixture
    def mock_artist_service(self):
        service = MagicMock()
        service.get_by_name.return_value = None
        service.create.return_value = 100
        return service

    @pytest.fixture
    def mock_song_service(self):
        service = MagicMock()
        service.get_all_paths.return_value = []
        type(service).genre_map = PropertyMock(return_value={0: "", 1: "Rock", 18: "za obradu"})
        type(service).decade_map = PropertyMock(return_value={0: "", 2: "1980's"})
        return service

    @pytest.fixture
    def import_service(self, mock_backend, mock_artist_service, mock_song_service):
        return ImportService(
            backend=mock_backend,
            artist_service=mock_artist_service,
            song_service=mock_song_service
        )

    # ─────────────────────────────────────────────────────────────
    # Execute Tests
    # ─────────────────────────────────────────────────────────────

    def test_creates_new_song(self, import_service, mock_backend, mock_artist_service):
        """Test creating a new song record."""
        candidate = ImportCandidate(
            file_path="C:\\Music\\New.mp3",
            metadata=ParsedMetadata(
                artist="NewArtist", title="NewSong", album="Album",
                year=1985, duration=180.5, genre="Rock"
            ),
            status=ImportStatus.NEW,
            artist_id=None,
            artist_is_new=True,
            genre_ids=[1, 0, 0],
            decade_id=2
        )

        summary = import_service.execute_import([candidate])

        assert summary.successful == 1
        assert summary.new_artists_created == 1
        mock_artist_service.create.assert_called_once_with("NewArtist")
        mock_backend.insert.assert_called_once()

        # Verify the data passed to insert
        call_args = mock_backend.insert.call_args
        data = call_args[0][1]
        assert data['fldArtistCode'] == 100  # Created artist ID
        assert data['fldArtistName'] == "NewArtist"
        assert data['fldTitle'] == "NewSong"
        assert data['fldCat1a'] == 1  # Rock
        assert data['fldCat2'] == 2   # 1980's
        assert data['fldPriority'] == 5  # Default priority
        assert data['fldEnabled'] is True

    def test_skips_duplicate(self, import_service, mock_backend):
        """Test that duplicates are skipped."""
        candidate = ImportCandidate(
            file_path="C:\\Music\\Dup.mp3",
            metadata=ParsedMetadata(artist="X", title="Y"),
            status=ImportStatus.DUPLICATE
        )

        summary = import_service.execute_import([candidate])

        assert summary.successful == 0
        assert summary.skipped == 1
        mock_backend.insert.assert_not_called()

    def test_conflict_user_skip(self, import_service, mock_backend):
        """Test conflict resolution: user chooses skip."""
        candidate = ImportCandidate(
            file_path="C:\\Music\\Conflict.mp3",
            metadata=ParsedMetadata(artist="X", title="Y"),
            status=ImportStatus.CONFLICT,
            existing_song_id=99,
            user_decision="skip"
        )

        summary = import_service.execute_import([candidate])

        assert summary.skipped == 1
        mock_backend.insert.assert_not_called()
        mock_backend.update.assert_not_called()

    def test_conflict_user_merge(self, import_service, mock_backend):
        """Test conflict resolution: user chooses merge."""
        candidate = ImportCandidate(
            file_path="C:\\Music\\NewPath.mp3",
            metadata=ParsedMetadata(artist="Madonna", title="Vogue"),
            status=ImportStatus.CONFLICT,
            existing_song_id=99,
            user_decision="merge"
        )

        summary = import_service.execute_import([candidate])

        assert summary.successful == 1
        assert summary.conflicts_resolved == 1
        mock_backend.update.assert_called_once()

        # Verify update call
        call_args = mock_backend.update.call_args
        assert call_args[0][1] == 99  # existing song ID
        assert call_args[0][2] == {'fldFilename': "C:\\Music\\NewPath.mp3"}

    def test_conflict_user_import(self, import_service, mock_backend, mock_artist_service):
        """Test conflict resolution: user chooses import (create new)."""
        mock_artist_record = MagicMock()
        mock_artist_record.__getitem__ = lambda s, k: 50 if k == 'AUID' else None
        mock_artist_service.get_by_name.return_value = mock_artist_record

        candidate = ImportCandidate(
            file_path="C:\\Music\\NewVersion.mp3",
            metadata=ParsedMetadata(artist="Madonna", title="Vogue"),
            status=ImportStatus.CONFLICT,
            existing_song_id=99,
            artist_id=50,
            artist_is_new=False,
            user_decision="import"
        )

        summary = import_service.execute_import([candidate])

        assert summary.successful == 1
        mock_backend.insert.assert_called_once()  # New record created

    def test_conflict_default_skip(self, import_service, mock_backend):
        """Test that conflicts default to skip if no user_decision."""
        candidate = ImportCandidate(
            file_path="C:\\Music\\Conflict.mp3",
            metadata=ParsedMetadata(artist="X", title="Y"),
            status=ImportStatus.CONFLICT,
            existing_song_id=99,
            user_decision=None  # No decision
        )

        summary = import_service.execute_import([candidate])

        assert summary.skipped == 1

    def test_links_existing_artist_on_execute(self, import_service, mock_backend, mock_artist_service):
        """Test that existing artists are linked without creating new."""
        candidate = ImportCandidate(
            file_path="C:\\Music\\Song.mp3",
            metadata=ParsedMetadata(artist="ExistingArtist", title="Song"),
            status=ImportStatus.NEW,
            artist_id=50,  # Already resolved
            artist_is_new=False
        )

        summary = import_service.execute_import([candidate])

        assert summary.successful == 1
        assert summary.new_artists_created == 0  # No new artist
        mock_artist_service.create.assert_not_called()

        call_args = mock_backend.insert.call_args
        data = call_args[0][1]
        assert data['fldArtistCode'] == 50

    def test_batch_import(self, import_service, mock_backend, mock_artist_service):
        """Test importing multiple files."""
        candidates = [
            ImportCandidate(
                file_path=f"C:\\Music\\Song{i}.mp3",
                metadata=ParsedMetadata(artist=f"Artist{i}", title=f"Song{i}"),
                status=ImportStatus.NEW,
                artist_id=None,
                artist_is_new=True
            )
            for i in range(5)
        ]

        summary = import_service.execute_import(candidates)

        assert summary.total_files == 5
        assert summary.successful == 5
        assert summary.new_artists_created == 5
        assert mock_backend.insert.call_count == 5

    def test_handles_insert_failure(self, import_service, mock_backend, mock_artist_service):
        """Test handling of insert failures."""
        mock_backend.insert.return_value = None  # Insert fails

        candidate = ImportCandidate(
            file_path="C:\\Music\\Song.mp3",
            metadata=ParsedMetadata(artist="Artist", title="Song"),
            status=ImportStatus.NEW,
            artist_id=None,
            artist_is_new=True
        )

        summary = import_service.execute_import([candidate])

        assert summary.successful == 0
        assert summary.errors == 1
        assert summary.results[0].action == "error"

    def test_progress_callback(self, import_service, mock_backend):
        """Test that progress callback is called."""
        callback = MagicMock()

        candidates = [
            ImportCandidate(
                file_path=f"C:\\Music\\Song{i}.mp3",
                metadata=ParsedMetadata(artist="Artist", title=f"Song{i}"),
                status=ImportStatus.NEW,
                artist_id=100,
                artist_is_new=False
            )
            for i in range(3)
        ]

        import_service.execute_import(candidates, progress_callback=callback)

        assert callback.call_count == 3
        # Check first call: (1, 3, action)
        assert callback.call_args_list[0][0][0] == 1
        assert callback.call_args_list[0][0][1] == 3


class TestJazlerDefaults:
    """Test the JazlerDefaults configuration."""

    def test_default_values(self):
        """Test that defaults match expected Jazler settings."""
        defaults = JazlerDefaults()

        assert defaults.fldEnabled is True
        assert defaults.fldEnabledAuto is True
        assert defaults.fldPriority == 5
        assert defaults.fldFadeDur == 1.0
        assert defaults.DEFAULT_GENRE_ID == 18  # za obradu

    def test_custom_defaults(self):
        """Test using custom defaults."""
        custom = JazlerDefaults(fldPriority=10, fldFadeDur=5.0)

        assert custom.fldPriority == 10
        assert custom.fldFadeDur == 5.0


class TestCacheManagement:
    """Test cache management functionality."""

    @pytest.fixture
    def mock_backend(self):
        backend = MagicMock()
        backend.fetch.return_value = []
        return backend

    @pytest.fixture
    def mock_artist_service(self):
        service = MagicMock()
        service.get_by_name.return_value = None
        return service

    @pytest.fixture
    def mock_song_service(self):
        service = MagicMock()
        service.get_all_paths.return_value = []
        type(service).genre_map = PropertyMock(return_value={0: ""})
        type(service).decade_map = PropertyMock(return_value={0: ""})
        return service

    def test_clear_cache(self, mock_backend, mock_artist_service, mock_song_service):
        """Test that clear_cache resets all cached data."""
        service = ImportService(
            backend=mock_backend,
            artist_service=mock_artist_service,
            song_service=mock_song_service
        )

        # Trigger cache load
        with patch.object(service.parser, 'parse') as mock_parse:
            mock_parse.return_value = ParsedMetadata(artist="A", title="T")
            service.preview_import(["file.mp3"])

        # Caches should be populated
        assert service._existing_paths is not None

        # Clear cache
        service.clear_cache()

        # Caches should be None
        assert service._existing_paths is None
        assert service._existing_artist_titles is None
        assert service._genre_name_to_id is None
        assert service._decade_name_to_id is None
