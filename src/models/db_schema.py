"""
Database schema definitions for Jazler RadioStar database.

This module contains column index mappings for database records.
Table: snDatabase
"""
from enum import IntEnum


class SongColumns(IntEnum):
    """
    Column indices for the snDatabase (Songs) table in the Jazler database.
    
    These map to the positions in the tuple returned by database queries.
    """
    # Primary identifiers
    AUID = 0                        # Primary key (ID)
    ARTIST_CODE = 1                 # fldArtistCode - Foreign key to Artists
    TITLE = 2                       # fldTitle
    
    # Genre categories
    CAT1A = 3                       # fldCat1a - Primary genre
    CAT1B = 4                       # fldCat1b - Secondary genre
    CAT1C = 5                       # fldCat1c - Tertiary genre
    CAT2 = 6                        # fldCat2 - Decade category
    CAT3 = 7                        # fldCat3 - Tempo category
    
    # Metadata
    YEAR = 8                        # fldYear
    VOCAL_PRESENT = 9               # fldVocalPresent
    BEATS_PER_MINUTE = 10           # fldBeatsPerMinute (BPM)
    PRIORITY = 11                   # fldPriority
    
    # Playback settings
    ENABLED = 12                    # fldEnabled
    ENABLED_AUTO = 13               # fldEnabledAuto (Autoplay)
    DURATION = 14                   # fldDuration
    INTRO_POS = 15                  # fldIntroPos
    MIX_POS = 16                    # fldMixPos
    FADE_DUR = 17                   # fldFadeDur
    FADE_POS = 18                   # fldFadePos
    
    # Broadcast info
    LAST_BROADCAST = 19             # fldLastBroadcast
    
    # File info
    FILENAME = 20                   # fldFilename - Path to audio file
    VOTE_COUNT = 21                 # fldVoteCount
    START_POS = 22                  # fldStartPos
    
    # Credits
    SONG_WRITER = 23                # fldSongWriter
    COMPOSER = 24                   # fldComposer
    ALBUM = 25                      # fldAlbum
    VOLUME = 26                     # fldVolume
    CD_KEY = 27                     # fldCDKey - ISRC code
    
    # Statistics
    BROADCASTS = 28                 # fldBroadcasts
    BAR_CODE = 29                   # fldBarCode
    ENTRY_DATE = 30                 # fldEntryDate
    RELEASE_DATE = 31               # fldReleaseDate
    
    # Publisher / Label
    LABEL = 32                      # fldLabel (Publisher)
    
    # More stats/metadata
    BROADCASTS_DATE = 33            # fldBroadcastsDate
    COMMENTS = 34                   # fldComments
    LEAST_BROADCAST = 35            # fldLeastBroadcast
    
    # Artist info (joined)
    ARTIST_NAME = 36                # fldArtistName
    
    # Additional settings
    NO_RDS = 37                     # fldNoRDS
    FADE_IN_DUR = 38                # fldFadeInDur
    NEXT_AVAILABLE = 39             # fldNextAvailable
    SELECTED_PLAYLIST = 40          # fldSelectedPlaylist
    PROPERTIES = 41                 # fldProperties
    PLAYLISTER_CODE = 42            # fldPlaylisterCode
    DO_NOT_AUTO_ALTER = 43          # fldDoNotAutoAlter
    PL_NEXT_AVAILABLE = 44          # fldPLNextAvailable
    PL_VOTE_COUNT = 45              # fldPLVoteCount
    CODE_STRING = 46                # fldCodeString
    TIME_SLOTS = 47                 # fldTimeSlots
    LINKED_SONGS = 48               # fldLinkedSongs
    SONG_URL = 49                   # fldSongURL
    ARTIST_URL = 50                 # fldArtistURL
    METADATA_TITLE = 51             # fldMetadataTitle


# Aliases for backward compatibility with old IDX_* names
ID = SongColumns.AUID
ARTIST_ID = SongColumns.ARTIST_CODE
GENRE_1_ID = SongColumns.CAT1A
GENRE_2_ID = SongColumns.CAT1B
GENRE_3_ID = SongColumns.CAT1C
GENRE_4_ID = SongColumns.CAT2
GENRE_5_ID = SongColumns.CAT3
AUTOPLAY = SongColumns.ENABLED_AUTO
ISRC = SongColumns.CD_KEY
PUBLISHER = SongColumns.LABEL
