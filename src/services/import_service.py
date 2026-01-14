"""
Import Service - Orchestrates the import of orphan files.

Coordinates between:
- ImportParser (parsing logic)
- ArtistService (artist lookup/creation)
- SongService (duplicate detection)
- Backend (database writes)
"""

import logging
import os
from os import path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

from src.core.config import app_config

from src.services.import_parser import (
    ImportParser, ImportCandidate, ImportResult, ImportSummary,
    ParsedMetadata, ImportStatus
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Jazler Defaults Configuration
# ─────────────────────────────────────────────────────────────

@dataclass
class JazlerDefaults:
    """Default values for new Jazler song records."""
    fldEnabled: bool = True
    fldEnabledAuto: bool = True
    fldVocalPresent: bool = False
    fldPriority: int = 5              # User confirmed default
    fldIntroPos: float = 0.0
    fldMixPos: float = 0.0
    fldFadeDur: float = 1.0
    fldFadePos: float = 0.0
    fldStartPos: float = 0.0
    fldFadeInDur: float = 0.0
    fldVolume: int = 100
    fldBroadcasts: int = 0
    fldVoteCount: int = 1
    fldNoRDS: bool = False
    fldDoNotAutoAlter: bool = False
    fldCat3: int = 0                  # Tempo (no auto-matching available)

    # Default genre ID when no match found
    DEFAULT_GENRE_ID: int = 18        # "za obradu"


# ─────────────────────────────────────────────────────────────
# Import Service Class
# ─────────────────────────────────────────────────────────────

class ImportService:
    """
    Service for importing orphan files into the database.

    Uses dependency injection for all external services.

    Usage:
        service = ImportService(
            backend=access_backend,
            artist_service=artist_service,
            song_service=song_service
        )

        # Preview what would happen
        candidates = service.preview_import(["/path/to/file.mp3", ...])

        # User reviews and approves
        for c in candidates:
            if c.status == ImportStatus.CONFLICT:
                c.user_decision = "import"  # or "skip" or "merge"

        # Execute the import
        summary = service.execute_import(candidates)
    """

    TABLE_NAME = "snDatabase"
    PK_COLUMN = "AUID"

    def __init__(
        self,
        backend,  # AccessBackend
        artist_service,  # ArtistService
        song_service,  # SongService
        parser: Optional[ImportParser] = None,
        defaults: Optional[JazlerDefaults] = None
    ):
        """
        Initialize ImportService.

        Args:
            backend: Database backend for inserts
            artist_service: For artist lookup/creation
            song_service: For duplicate detection and genre maps
            parser: Optional custom parser (uses default if None)
            defaults: Optional custom Jazler defaults
        """
        self.backend = backend
        self.artist_service = artist_service
        self.song_service = song_service
        self.parser = parser or ImportParser()
        self.defaults = defaults or JazlerDefaults()

        # Cached lookup maps
        self._genre_name_to_id: Optional[Dict[str, int]] = None
        self._decade_name_to_id: Optional[Dict[str, int]] = None
        self._existing_paths: Optional[set] = None
        self._existing_artist_titles: Optional[Dict[str, Dict]] = None

    # ─────────────────────────────────────────────────────────────
    # Preview Mode (Dry Run)
    # ─────────────────────────────────────────────────────────────

    def preview_import(
        self,
        file_paths: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ImportCandidate]:
        """
        Analyze files and determine what would happen on import.

        Does NOT modify the database.

        Args:
            file_paths: List of full paths to orphan files
            progress_callback: Optional callback(current, total) for progress

        Returns:
            List of ImportCandidate objects with status set
        """
        # Load/cache lookup data
        self._load_existing_data()

        candidates = []
        total = len(file_paths)

        for idx, path in enumerate(file_paths):
            try:
                candidate = self._analyze_file(path)
                candidates.append(candidate)
            except Exception as e:
                logger.error(f"Failed to analyze {path}: {e}")
                # Create error candidate
                candidates.append(ImportCandidate(
                    file_path=path,
                    metadata=ParsedMetadata(
                        artist="Error",
                        title=str(e),
                        confidence=0.0
                    ),
                    status=ImportStatus.NEW
                ))

            if progress_callback:
                progress_callback(idx + 1, total)

        return candidates

    def _load_existing_data(self) -> None:
        """Load/cache data needed for duplicate detection."""
        if self._existing_paths is None:
            # Get all existing file paths
            paths = self.song_service.get_all_paths()
            self._existing_paths = {
                self.parser.normalize_path(p) for p in paths
            }

        if self._existing_artist_titles is None:
            # Build artist+title index for conflict detection
            # Fetch full record data for side-by-side comparison
            self._existing_artist_titles = {}
            try:
                # Fetch columns needed for comparison view
                rows = self.backend.fetch(
                    self.TABLE_NAME,
                    columns=[
                        'AUID', 'fldArtistName', 'fldTitle', 'fldFilename',
                        'fldAlbum', 'fldYear', 'fldDuration', 'fldComposer', 'fldLabel',
                        'fldCat1a', 'fldCat1b', 'fldCat1c', 'fldCat2', 'fldCat3',
                        'fldEnabled', 'fldEnabledAuto', 'fldPriority', 'fldCDKey'
                    ],
                    limit=200000
                )
                for row in rows:
                    artist = self.parser.normalize_for_comparison(row.get('fldArtistName') or '')
                    title = self.parser.normalize_for_comparison(row.get('fldTitle') or '')
                    key = f"{artist}|||{title}"
                    self._existing_artist_titles[key] = {
                        'id': row['AUID'],
                        'path': row['fldFilename'],
                        # Full record data for comparison
                        'full_record': {
                            'artist': row.get('fldArtistName') or '',
                            'title': row.get('fldTitle') or '',
                            'album': row.get('fldAlbum') or '',
                            'year': row.get('fldYear') or 0,
                            'duration': row.get('fldDuration') or 0.0,
                            'composer': row.get('fldComposer') or '',
                            'publisher': row.get('fldLabel') or '',
                            'isrc': row.get('fldCDKey') or '',
                            'genre_ids': [
                                row.get('fldCat1a') or 0,
                                row.get('fldCat1b') or 0,
                                row.get('fldCat1c') or 0,
                            ],
                            'decade_id': row.get('fldCat2') or 0,
                            'tempo_id': row.get('fldCat3') or 0,
                            'enabled': row.get('fldEnabled'),
                            'enabled_auto': row.get('fldEnabledAuto'),
                            'priority': row.get('fldPriority') or 0,
                            'path': row.get('fldFilename') or '',
                        }
                    }
            except Exception as e:
                logger.error(f"Failed to load existing artist+titles: {e}")
                self._existing_artist_titles = {}

        if self._genre_name_to_id is None:
            # Build reverse genre map (name -> ID)
            genre_map = self.song_service.genre_map  # ID -> name
            self._genre_name_to_id = {}
            for gid, name in genre_map.items():
                if name and gid > 0:
                    self._genre_name_to_id[name.lower().strip()] = gid

        if self._decade_name_to_id is None:
            # Build reverse decade map (name -> ID)
            decade_map = self.song_service.decade_map  # ID -> name
            self._decade_name_to_id = {}
            for did, name in decade_map.items():
                if name and did > 0:
                    self._decade_name_to_id[name.lower().strip()] = did

    def _analyze_file(self, file_path: str) -> ImportCandidate:
        """Analyze a single file for import readiness."""
        # Parse metadata
        metadata = self.parser.parse(file_path)

        candidate = ImportCandidate(
            file_path=file_path,
            metadata=metadata
        )

        # Check for duplicate by path
        norm_path = self.parser.normalize_path(file_path)
        if norm_path in self._existing_paths:
            candidate.status = ImportStatus.DUPLICATE
            return candidate

        # Check for conflict by artist+title
        norm_artist = self.parser.normalize_for_comparison(metadata.artist)
        norm_title = self.parser.normalize_for_comparison(metadata.title)
        key = f"{norm_artist}|||{norm_title}"

        if key in self._existing_artist_titles:
            existing = self._existing_artist_titles[key]
            candidate.status = ImportStatus.CONFLICT
            candidate.existing_song_id = existing['id']
            candidate.existing_path = existing['path']
            
            # Fetch FULL existing record for deep comparison
            try:
                full_existing = self.backend.fetch_one(
                    self.TABLE_NAME, 
                    primary_key_value=candidate.existing_song_id,
                    primary_key_column="AUID"
                )
                candidate.existing_data = full_existing
                
                # Pre-calculate what we WOULD create so we can diff it
                self._resolve_artist(candidate)
                self._resolve_genres(candidate)
                self._resolve_decade(candidate)
                
                payload = self.get_insertion_data(candidate)
                
                # Compute diff: What changes in the database if we "merge" or "overwrite"?
                # Note: Insertion payload has keys like 'fldTitle', 'fldYear'
                # Existing record has the same keys
                diff = {}
                for k, v in payload.items():
                    # Skip internal logic/placeholder like artist_code -1
                    if k == 'fldArtistCode':
                        continue
                        
                    old_val = full_existing.get(k)
                    
                    # Normalize for comparison (None vs 0 vs 0.0)
                    v_norm = v
                    old_norm = old_val
                    
                    if isinstance(v, float) and isinstance(old_val, float):
                         # Fuzzy float compare
                        if abs(v - old_val) < 0.01:
                            continue
                            
                    # Treat None, 0, "" slightly loosely for equality to reduce noise?
                    # No, strict is better for "Raw Data Diff"
                    
                    if v_norm != old_norm:
                        diff[k] = {
                            'new': v,
                            'old': old_val
                        }
                
                # Normalize raw record to "pretty" format expected by frontend
                normalized_existing = {
                    'artist': full_existing.get('fldArtistName') or '',
                    'title': full_existing.get('fldTitle') or '',
                    'album': full_existing.get('fldAlbum') or '',
                    'year': full_existing.get('fldYear') or 0,
                    'duration': full_existing.get('fldDuration') or 0.0,
                    'composer': full_existing.get('fldComposer') or '',
                    'publisher': full_existing.get('fldLabel') or '',
                    'isrc': full_existing.get('fldCDKey') or '',
                    'genre_ids': [
                        full_existing.get('fldCat1a') or 0,
                        full_existing.get('fldCat1b') or 0,
                        full_existing.get('fldCat1c') or 0,
                    ],
                    'decade_id': full_existing.get('fldCat2') or 0,
                    'tempo_id': full_existing.get('fldCat3') or 0,
                    'enabled': full_existing.get('fldEnabled'),
                    'enabled_auto': full_existing.get('fldEnabledAuto'),
                    'priority': full_existing.get('fldPriority') or 0,
                    'path': full_existing.get('fldFilename') or '',
                    '_diff': diff
                }
                
                candidate.existing_data = normalized_existing
                
            except Exception as e:
                logger.error(f"Failed to fetch comparison record: {e}")
                candidate.existing_data = existing.get('full_record')

            return candidate

        # It's new - resolve artist, genres, and decade
        candidate.status = ImportStatus.NEW
        self._resolve_artist(candidate)
        self._resolve_genres(candidate)
        self._resolve_decade(candidate)

        return candidate

    def _resolve_artist(self, candidate: ImportCandidate) -> None:
        """Look up or mark artist for creation."""
        artist_name = candidate.metadata.artist
        existing = self.artist_service.get_by_name(artist_name)

        if existing:
            candidate.artist_id = existing['AUID']
            candidate.artist_is_new = False
        else:
            # Will be created during execute
            candidate.artist_id = None
            candidate.artist_is_new = True

    def _resolve_genres(self, candidate: ImportCandidate) -> None:
        """
        Match ID3 genre string(s) to snCat1 IDs.
        Handles comma-delimited genres (up to 3).
        Falls back to DEFAULT_GENRE_ID ("za obradu") if no match.
        """
        genre_str = candidate.metadata.genre or ""

        # Split by comma and normalize
        raw_genres = [g.strip().lower() for g in genre_str.split(",") if g.strip()]

        # Match up to 3 genres
        matched_ids = []
        for genre in raw_genres[:3]:
            if genre in self._genre_name_to_id:
                matched_ids.append(self._genre_name_to_id[genre])

        # Assign to genre_ids [Cat1a, Cat1b, Cat1c]
        # Default primary genre to "za obradu" (18) if no matches
        candidate.genre_ids = [
            matched_ids[0] if len(matched_ids) > 0 else self.defaults.DEFAULT_GENRE_ID,
            matched_ids[1] if len(matched_ids) > 1 else 0,
            matched_ids[2] if len(matched_ids) > 2 else 0,
        ]

    def _resolve_decade(self, candidate: ImportCandidate) -> None:
        """
        Match year to decade via snCat2 lookup.
        Decade names in snCat2 are formatted as "1930's", "1980's", "2000's", etc.
        """
        year = candidate.metadata.year
        if not year or year < 1900:
            candidate.decade_id = 0
            return

        # Calculate decade string: 1985 -> "1980's", 2015 -> "2010's"
        decade_start = (year // 10) * 10  # 1985 -> 1980, 2015 -> 2010
        decade_str = f"{decade_start}'s"  # "1980's", "2010's"

        # Try to match (case-insensitive)
        candidate.decade_id = self._decade_name_to_id.get(decade_str.lower(), 0)

    # ─────────────────────────────────────────────────────────────
    # Execute Mode (Database Writes)
    # ─────────────────────────────────────────────────────────────

    def execute_import(
        self,
        candidates: List[ImportCandidate],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> ImportSummary:
        """
        Execute the actual import for approved candidates.

        Args:
            candidates: List of candidates (with user_decision set for conflicts)
            progress_callback: Optional callback(current, total, message)

        Returns:
            ImportSummary with results
        """
        summary = ImportSummary(total_files=len(candidates))

        for idx, candidate in enumerate(candidates):
            try:
                result = self._import_candidate(candidate)
                summary.results.append(result)

                if result.success:
                    summary.successful += 1
                    if candidate.artist_is_new and result.action == "created":
                        summary.new_artists_created += 1
                    if candidate.status == ImportStatus.CONFLICT:
                        summary.conflicts_resolved += 1
                else:
                    if result.action == "skipped":
                        summary.skipped += 1
                    else:
                        summary.errors += 1

            except Exception as e:
                logger.error(f"Import failed for {candidate.file_path}: {e}")
                summary.errors += 1
                summary.results.append(ImportResult(
                    file_path=candidate.file_path,
                    success=False,
                    error=str(e),
                    action="error"
                ))

            if progress_callback:
                status = summary.results[-1].action if summary.results else "processing"
                progress_callback(idx + 1, len(candidates), status)

        return summary

    def _import_candidate(self, candidate: ImportCandidate) -> ImportResult:
        """Import a single candidate."""
        # Handle duplicates
        if candidate.status == ImportStatus.DUPLICATE:
            return ImportResult(
                file_path=candidate.file_path,
                success=False,
                action="skipped",
                error="Duplicate path exists"
            )

        # Handle conflicts
        if candidate.status == ImportStatus.CONFLICT:
            decision = candidate.user_decision or "skip"

            if decision == "skip":
                return ImportResult(
                    file_path=candidate.file_path,
                    success=False,
                    action="skipped",
                    error="Conflict - user chose to skip"
                )
            elif decision == "merge":
                # Update existing record's path instead of creating new
                return self._merge_into_existing(candidate)
            # else: decision == "import" - fall through to create new

        # Create new record
        return self._create_song(candidate)

    def get_insertion_data(self, candidate: ImportCandidate) -> Dict[str, Any]:
        """
        Get the data dictionary that would be inserted for this candidate.
        Useful for debugging and preview.
        """
        meta = candidate.metadata

        # Resolve artist ID placeholder
        artist_id = candidate.artist_id
        if artist_id is None and candidate.artist_is_new:
            artist_id = -1  # Placeholder for "New Artist"

        # Determine Filename
        # 1. If it's a conflict/existing song, we normally preserve the existing DB path 
        #    (assuming we are updating metadata or overwriting the physical file in place).
        #    We definitely don't want to point the DB to a temporary browser upload path.
        if candidate.existing_path:
            final_filename = candidate.existing_path
        else:
            # 2. For new songs, use the file path but apply Reverse Drive Mapping
            #    e.g. Map 'Z:\Songs\...' to 'B:\Songs\...' matching the server config
            final_filename = candidate.file_path
            if app_config.drive_map:
                for server_prefix, local_prefix in app_config.drive_map.items():
                    if final_filename.lower().startswith(local_prefix.lower()):
                         final_filename = server_prefix + final_filename[len(local_prefix):]
                         break

        # Build record data
        data = {
            # Core fields
            'fldArtistCode': artist_id,
            'fldArtistName': meta.artist,
            'fldTitle': meta.title,
            'fldFilename': final_filename, 
            'fldDuration': meta.duration,
            'fldAlbum': meta.album,
            'fldYear': meta.year,
            'fldComposer': meta.composer,
            'fldLabel': meta.publisher,
            'fldCDKey': meta.isrc,

            # Category fields
            'fldCat1a': candidate.genre_ids[0] if len(candidate.genre_ids) > 0 else 0,
            'fldCat1b': candidate.genre_ids[1] if len(candidate.genre_ids) > 1 else 0,
            'fldCat1c': candidate.genre_ids[2] if len(candidate.genre_ids) > 2 else 0,
            'fldCat2': candidate.decade_id,
            'fldCat3': self.defaults.fldCat3,

            # Jazler defaults
            'fldEnabled': self.defaults.fldEnabled,
            'fldEnabledAuto': self.defaults.fldEnabledAuto,
            'fldVocalPresent': self.defaults.fldVocalPresent,
            'fldPriority': self.defaults.fldPriority,
            'fldIntroPos': self.defaults.fldIntroPos,
            'fldMixPos': self.defaults.fldMixPos,
            'fldFadeDur': self.defaults.fldFadeDur,
            'fldFadePos': self.defaults.fldFadePos,
            'fldStartPos': self.defaults.fldStartPos,
            'fldFadeInDur': self.defaults.fldFadeInDur,
            'fldVolume': self.defaults.fldVolume,
            'fldBroadcasts': self.defaults.fldBroadcasts,
            'fldVoteCount': self.defaults.fldVoteCount,
            'fldNoRDS': self.defaults.fldNoRDS,
            'fldDoNotAutoAlter': self.defaults.fldDoNotAutoAlter,
        }
        return data

    def _create_song(self, candidate: ImportCandidate) -> ImportResult:
        """Create a new song record in the database."""
        meta = candidate.metadata

        # Resolve artist (create if needed)
        artist_id = candidate.artist_id
        if artist_id is None and candidate.artist_is_new:
            artist_id = self.artist_service.create(meta.artist)
            if not artist_id:
                return ImportResult(
                    file_path=candidate.file_path,
                    success=False,
                    action="error",
                    error="Failed to create artist"
                )

        # Build record data using the same logic as get_insertion_data
        # but with the real artist_id
        data = self.get_insertion_data(candidate)
        data['fldArtistCode'] = artist_id

        # Insert into database
        try:
            new_id = self.backend.insert(self.TABLE_NAME, data)

            if new_id:
                # Update caches
                norm_path = self.parser.normalize_path(candidate.file_path)
                if self._existing_paths is not None:
                    self._existing_paths.add(norm_path)

                return ImportResult(
                    file_path=candidate.file_path,
                    success=True,
                    song_id=new_id,
                    artist_id=artist_id,
                    action="created"
                )
            else:
                return ImportResult(
                    file_path=candidate.file_path,
                    success=False,
                    action="error",
                    error="Insert returned no ID"
                )
        except Exception as e:
            logger.error(f"Database insert failed: {e}")
            return ImportResult(
                file_path=candidate.file_path,
                success=False,
                action="error",
                error=str(e)
            )

    def _merge_into_existing(self, candidate: ImportCandidate) -> ImportResult:
        """Update existing record's path to point to new file."""
        if not candidate.existing_song_id:
            return ImportResult(
                file_path=candidate.file_path,
                success=False,
                action="error",
                error="No existing song ID for merge"
            )

        try:
            success = self.backend.update(
                self.TABLE_NAME,
                candidate.existing_song_id,
                {'fldFilename': candidate.file_path},
                primary_key_column=self.PK_COLUMN
            )

            if success:
                return ImportResult(
                    file_path=candidate.file_path,
                    success=True,
                    song_id=candidate.existing_song_id,
                    action="merged"
                )
            else:
                return ImportResult(
                    file_path=candidate.file_path,
                    success=False,
                    action="error",
                    error="Merge update failed"
                )
        except Exception as e:
            logger.error(f"Merge update failed: {e}")
            return ImportResult(
                file_path=candidate.file_path,
                success=False,
                action="error",
                error=str(e)
            )

    # ─────────────────────────────────────────────────────────────
    # Cache Management
    # ─────────────────────────────────────────────────────────────

    def clear_cache(self) -> None:
        """Clear cached lookup data. Call if DB state changes externally."""
        self._existing_paths = None
        self._existing_artist_titles = None
        self._genre_name_to_id = None
        self._decade_name_to_id = None
