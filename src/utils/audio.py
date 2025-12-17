from mutagen.mp3 import MP3
import mutagen.id3
from typing import Optional, TYPE_CHECKING
from src.utils.error_handler import ErrorHandler
from src.utils.id3_tags import ID3Tags

if TYPE_CHECKING:
    from src.models.song import SongID3

class AudioMetadata:
    @staticmethod
    def song_length(path: str) -> Optional[float]:
        try:
            audio = MP3(path)
            length = audio.info.length
            return length
        except Exception as e:
            ErrorHandler.log_silent(e, "Getting song length")
            return None

    @staticmethod
    def get_tag(path: str) -> MP3:
        return MP3(path, ID3=mutagen.id3.ID3)

    @staticmethod
    def tag_write(id3_data: 'SongID3', location: str) -> None:
        try:
            tag = MP3(location, ID3=mutagen.id3.ID3)
        except Exception as e:
            ErrorHandler.log_silent(e, "Loading ID3 tag for write")
            return

        try:
            tag.tags[ID3Tags.ARTIST] = mutagen.id3.TPE1(encoding=3, text=[id3_data.artist])
            tag.tags[ID3Tags.TITLE] = mutagen.id3.TIT2(encoding=3, text=[id3_data.title])
            tag.tags[ID3Tags.ALBUM] = mutagen.id3.TALB(encoding=3, text=[id3_data.album])
            tag.tags[ID3Tags.COMPOSER] = mutagen.id3.TCOM(encoding=3, text=[id3_data.composer])
            tag.tags[ID3Tags.PUBLISHER] = mutagen.id3.TPUB(encoding=3, text=[id3_data.publisher])
            tag.tags[ID3Tags.YEAR] = mutagen.id3.TDRC(encoding=3, text=[str(id3_data.year)])
            tag.tags[ID3Tags.GENRE] = mutagen.id3.TCON(encoding=3, text=[id3_data.genres_all])
            try:
                duration_val = str(int(float(str(id3_data.duration))))
            except (ValueError, TypeError):
                duration_val = "0"
            tag.tags[ID3Tags.DURATION] = mutagen.id3.TLEN(encoding=3, text=[duration_val])
            if id3_data.isrc != "":
                tag.tags[ID3Tags.ISRC] = mutagen.id3.TSRC(encoding=3, text=[id3_data.isrc])
            
            # Write 'Done' status (KEY)
            # Convert boolean to "true"/"false" string to match Java app convention
            done_str = "true" if getattr(id3_data, "done", False) else "false"
            tag.tags[ID3Tags.KEY] = mutagen.id3.TKEY(encoding=3, text=[done_str])
            
            tag.save(v2_version=3)
        except Exception as e:
            ErrorHandler.show_error("Failed to write ID3 tags", str(e))

