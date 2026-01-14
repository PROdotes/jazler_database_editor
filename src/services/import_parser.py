"""
Import Parser - Standalone module for parsing metadata from audio files.

This module is designed to be reusable in other projects.
NO database access. NO framework dependencies (except mutagen for ID3).

Usage:
    parser = ImportParser()
    metadata = parser.parse("C:/Music/Madonna - Vogue.mp3")
    # Or with pre-read ID3 tags:
    metadata = parser.parse(filepath, id3_tags={'artist': 'Madonna', ...})
"""

import os
import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class ParseSource(Enum):
    """Where the metadata came from."""
    ID3 = "id3"
    FILENAME = "filename"
    FALLBACK = "fallback"


class ImportStatus(Enum):
    """Result of duplicate/conflict detection."""
    NEW = "new"              # No match found - safe to import
    DUPLICATE = "duplicate"  # Same path exists - skip
    CONFLICT = "conflict"    # Same artist+title but different path - user decides


# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class ParsedMetadata:
    """
    Result of parsing a single file.
    Pure data - no DB references.
    """
    artist: str
    title: str
    album: str = ""
    year: int = 0
    genre: str = ""           # Raw ID3 genre string (e.g. "Rock" or "Rock, Pop")
    duration: float = 0.0
    composer: str = ""
    publisher: str = ""
    isrc: str = ""

    # Metadata about the parse
    source: ParseSource = ParseSource.FALLBACK
    confidence: float = 0.0   # 0.0-1.0, how confident we are

    def normalized_artist(self) -> str:
        """For duplicate comparison."""
        return ImportParser.normalize_for_comparison(self.artist)

    def normalized_title(self) -> str:
        """For duplicate comparison."""
        return ImportParser.normalize_for_comparison(self.title)


@dataclass
class ImportCandidate:
    """
    A file ready for import consideration.
    Combines parsed data with path info.
    """
    file_path: str            # Full path to the orphan file
    metadata: ParsedMetadata

    # Resolved after DB lookup
    status: ImportStatus = ImportStatus.NEW
    existing_song_id: Optional[int] = None  # If DUPLICATE or CONFLICT
    existing_path: Optional[str] = None     # Path of existing match

    # Resolved artist linkage
    artist_id: Optional[int] = None
    artist_is_new: bool = False

    # Resolved category linkages
    genre_ids: List[int] = field(default_factory=lambda: [18, 0, 0])  # [Cat1a, Cat1b, Cat1c], default=za obradu (18)
    decade_id: int = 0        # fldCat2

    # User decision for conflicts
    user_decision: Optional[str] = None  # "import", "skip", "merge"

    # Full existing record data for conflicts (side-by-side comparison)
    existing_data: Optional[Dict[str, Any]] = None


@dataclass
class ImportResult:
    """Result of importing a single file."""
    file_path: str
    success: bool
    song_id: Optional[int] = None    # New AUID if created
    artist_id: Optional[int] = None
    error: Optional[str] = None
    action: str = ""  # "created", "skipped", "merged", "error"


@dataclass
class ImportSummary:
    """Summary of a batch import operation."""
    total_files: int = 0
    successful: int = 0
    skipped: int = 0
    errors: int = 0
    new_artists_created: int = 0
    conflicts_resolved: int = 0
    results: List[ImportResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return self.errors > 0


# ─────────────────────────────────────────────────────────────
# Import Parser Class
# ─────────────────────────────────────────────────────────────

class ImportParser:
    """
    Pure parsing logic for extracting metadata from files.

    NO database access. NO external dependencies except mutagen for ID3.
    This class is designed to be extracted and reused in other projects.

    Usage:
        parser = ImportParser()
        metadata = parser.parse("C:/Music/Madonna - Vogue.mp3")
        # Or with pre-read ID3 tags:
        metadata = parser.parse(filepath, id3_tags={'artist': 'Madonna', ...})
    """

    # Separator pattern: space-hyphen-space
    SEPARATOR = " - "

    # Pattern for track numbers (e.g., "01", "1", "01.")
    TRACK_NUMBER_PATTERN = re.compile(r'^(\d{1,3}\.?\s*)$')

    def __init__(self, fallback_artist: str = "Unknown", fallback_title: str = "Unknown"):
        """
        Initialize parser.

        Args:
            fallback_artist: Default artist when nothing can be parsed
            fallback_title: Default title when nothing can be parsed
        """
        self.fallback_artist = fallback_artist
        self.fallback_title = fallback_title

    def parse(
        self,
        filepath: str,
        id3_tags: Optional[Dict[str, Any]] = None,
        read_id3: bool = True
    ) -> ParsedMetadata:
        """
        Parse metadata from a file path and optional ID3 tags.

        Priority: ID3 Tags > Filename > Fallback

        Args:
            filepath: Full path to the audio file
            id3_tags: Pre-read ID3 tags dict (optional)
            read_id3: If True and id3_tags not provided, read from file

        Returns:
            ParsedMetadata with best-effort extraction
        """
        # Step 1: Parse from filename (always, as fallback)
        filename_meta = self._parse_filename(filepath)

        # Step 2: Get ID3 tags
        if id3_tags is None and read_id3:
            id3_tags = self._read_id3_tags(filepath)

        # Step 3: Merge with priority
        if id3_tags and self._has_valid_id3(id3_tags):
            return self._merge_metadata(id3_tags, filename_meta, filepath)
        else:
            return filename_meta

    def _parse_filename(self, filepath: str) -> ParsedMetadata:
        """
        Extract artist/title from filename.

        Rules:
        1. Split by " - " (space-hyphen-space)
        2. If 2 parts: Part1=Artist, Part2=Title
        3. If 3+ parts (e.g., "01 - Artist - Title"): Skip first if numeric, use rest
        """
        filename = os.path.basename(filepath)
        name_without_ext = os.path.splitext(filename)[0]

        # Clean up: collapse multiple spaces
        name_clean = re.sub(r'\s+', ' ', name_without_ext).strip()

        parts = name_clean.split(self.SEPARATOR)

        artist = self.fallback_artist
        title = self.fallback_title
        confidence = 0.0

        if len(parts) == 2:
            # "Artist - Title"
            artist = parts[0].strip()
            title = parts[1].strip()
            confidence = 0.7

        elif len(parts) >= 3:
            # "01 - Artist - Title" or "Artist - Album - Title"
            first_part = parts[0].strip()

            # Check if first part looks like a track number
            if self._is_track_number(first_part):
                artist = parts[1].strip()
                title = self.SEPARATOR.join(parts[2:]).strip()
                confidence = 0.6
            else:
                # Assume "Artist - Something - Title"
                artist = parts[0].strip()
                title = parts[-1].strip()  # Last part is title
                confidence = 0.5

        elif len(parts) == 1:
            # No separator found - just use filename as title
            title = name_clean
            confidence = 0.3

        return ParsedMetadata(
            artist=artist or self.fallback_artist,
            title=title or self.fallback_title,
            source=ParseSource.FILENAME,
            confidence=confidence
        )

    def _is_track_number(self, text: str) -> bool:
        """Check if text looks like a track number."""
        text = text.strip()
        # Match: "01", "1", "01.", etc.
        if self.TRACK_NUMBER_PATTERN.match(text):
            return True
        if text.isdigit() and len(text) <= 3:
            return True
        return False

    def _read_id3_tags(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Read ID3 tags from file using mutagen."""
        try:
            from mutagen.easyid3 import EasyID3
            from mutagen.mp3 import MP3

            audio = MP3(filepath, ID3=EasyID3)

            # Get duration from audio info
            duration = getattr(audio.info, 'length', 0.0)

            # Try to get TLEN (metadata override) for duration
            try:
                tlen_ms = audio.get('TLEN', [None])[0]
                if tlen_ms and str(tlen_ms).strip() not in ('0', ''):
                    duration = float(tlen_ms) / 1000.0
            except:
                pass  # Keep physical duration

            return {
                'artist': audio.get('artist', [''])[0],
                'title': audio.get('title', [''])[0],
                'album': audio.get('album', [''])[0],
                'year': self._parse_year(audio.get('date', [''])[0]),
                'genre': audio.get('genre', [''])[0],
                'composer': audio.get('composer', [''])[0],
                'publisher': audio.get('organization', [''])[0],
                'duration': duration,
                'isrc': audio.get('isrc', [''])[0] if 'isrc' in audio else '',
            }
        except Exception as e:
            logger.debug(f"Failed to read ID3 tags from {filepath}: {e}")
            return None

    def _parse_year(self, year_str: str) -> int:
        """Parse year from ID3 date field."""
        if not year_str:
            return 0
        try:
            # Handle formats like "2024", "2024-01-15", etc.
            return int(str(year_str)[:4])
        except (ValueError, TypeError):
            return 0

    def _has_valid_id3(self, tags: Dict[str, Any]) -> bool:
        """Check if ID3 tags have meaningful artist/title."""
        artist = (tags.get('artist') or '').strip()
        title = (tags.get('title') or '').strip()
        return bool(artist) or bool(title)

    def _merge_metadata(
        self,
        id3: Dict[str, Any],
        filename_meta: ParsedMetadata,
        filepath: str
    ) -> ParsedMetadata:
        """Merge ID3 tags with filename fallbacks."""
        artist = (id3.get('artist') or '').strip()
        title = (id3.get('title') or '').strip()

        # Use filename as fallback for missing ID3 fields
        if not artist:
            artist = filename_meta.artist
        if not title:
            title = filename_meta.title

        return ParsedMetadata(
            artist=artist or self.fallback_artist,
            title=title or self.fallback_title,
            album=(id3.get('album') or '').strip(),
            year=id3.get('year', 0) or 0,
            genre=(id3.get('genre') or '').strip(),
            duration=id3.get('duration', 0.0) or 0.0,
            composer=(id3.get('composer') or '').strip(),
            publisher=(id3.get('publisher') or '').strip(),
            isrc=(id3.get('isrc') or '').strip(),
            source=ParseSource.ID3,
            confidence=0.9 if artist and title else 0.7
        )

    # ─────────────────────────────────────────────────────────────
    # Normalization Utilities (for duplicate detection)
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def normalize_for_comparison(text: str) -> str:
        """
        Normalize text for duplicate comparison.

        - Case insensitive
        - Trim whitespace
        - Collapse multiple spaces
        - Preserve hyphens (AC-DC stays AC-DC)
        - Preserve special chars (P!nk stays P!nk)
        """
        if not text:
            return ""
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize file path for comparison."""
        if not path:
            return ""
        # Lowercase, backslash, strip
        p = path.lower().replace('/', '\\').strip()
        return p
