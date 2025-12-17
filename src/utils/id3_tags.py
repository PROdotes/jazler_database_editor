"""
ID3 Tag Frame Constants.

These constants map to the ID3v2 frame identifiers used by the mutagen library.
Reference: https://id3.org/id3v2.3.0
"""


class ID3Tags:
    """ID3v2 frame identifiers for audio metadata."""
    
    # Text Information Frames
    ARTIST = "TPE1"        # Lead performer(s)/Soloist(s)
    TITLE = "TIT2"         # Title/Songname/Content description
    ALBUM = "TALB"         # Album/Movie/Show title
    COMPOSER = "TCOM"      # Composer
    PUBLISHER = "TPUB"     # Publisher
    YEAR = "TDRC"          # Recording time (ID3v2.4) / Year (preferred)
    YEAR_LEGACY = "TYER"   # Year (ID3v2.3 fallback)
    GENRE = "TCON"         # Content type (genre)
    DURATION = "TLEN"      # Length in milliseconds
    ISRC = "TSRC"          # ISRC (International Standard Recording Code)
    KEY = "TKEY"           # Initial key (used for "Done" status)
    KEY_LEGACY = "TKEY1"   # Custom key field (fallback)
