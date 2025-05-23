from mutagen.mp3 import MP3
import mutagen.id3


def song_length(path):
    try:
        audio = MP3(path)
        length = audio.info.length
        print("Length of song: ", length)
        return length
    except Exception as e:
        print(f"Error while getting song length: {e}")
        return None


def get_tag(path):
    return MP3(path, ID3=mutagen.id3.ID3)


def tag_write(id3_data, location):
    try:
        tag = MP3(location, ID3=mutagen.id3.ID3)
    except Exception as e:
        print(e)
        tag = None

    tag.tags["TPE1"] = mutagen.id3.TPE1(encoding=3, text=[id3_data.artist])
    tag.tags["TIT2"] = mutagen.id3.TIT2(encoding=3, text=[id3_data.title])
    tag.tags["TALB"] = mutagen.id3.TALB(encoding=3, text=[id3_data.album])
    tag.tags["TCOM"] = mutagen.id3.TCOM(encoding=3, text=[id3_data.composer])
    tag.tags["TPUB"] = mutagen.id3.TPUB(encoding=3, text=[id3_data.publisher])
    tag.tags["TDRC"] = mutagen.id3.TDRC(encoding=3, text=[str(id3_data.year)])
    tag.tags["TCON"] = mutagen.id3.TCON(encoding=3, text=[id3_data.genres_all])
    tag.tags["TLEN"] = mutagen.id3.TLEN(encoding=3, text=[str(int(float(str(id3_data.duration))))])
    if id3_data.isrc != "":
        tag.tags["TSRC"] = mutagen.id3.TSRC(encoding=3, text=[id3_data.isrc])
    tag.save(v2_version=3)
