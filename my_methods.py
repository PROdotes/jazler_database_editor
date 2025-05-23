from os import system
from Song import *
from mp3_stuff import *


def table_names(cursor):
    print("Table names: ")
    tables = cursor.tables()
    for row in tables:
        print(row.table_name)
    print("")


def column_names(cursor, table_name):
    print("Column names: ")
    cursor.execute('SELECT * FROM ' + table_name)
    column_names_ = [name[0] for name in cursor.description]
    for column_name in column_names_:
        print(column_name)
    print("")


def calc_decade(year):
    if year == "" or year is None:
        return "Not Entered"
    else:
        year = int(year)
        return str(year - year % 10) + "'s"


def generate_genre_map(cursor):
    cursor.execute("SELECT * from snCat1")
    genre_query = cursor.fetchall()
    genre_map = dict()
    for entry in genre_query:
        genre_map[entry[0]] = entry[1].lower()
    genre_map[0] = "X"
    return genre_map


def generate_decade_map(cursor):
    cursor.execute("SELECT * from snCat2")
    decade_query = cursor.fetchall()
    decade_map = dict()
    for entry in decade_query:
        decade_map[entry[0]] = entry[1]
    return decade_map


def generate_tempo_map(cursor):
    cursor.execute("SELECT * from snCat3")
    tempo_query = cursor.fetchall()
    tempo_map = dict()
    for entry in tempo_query:
        tempo_map[entry[0]] = entry[1]
    return tempo_map


def get_data(database_entry, genre_map, decade_map, tempo_map):
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
        id3 = SongID3(tag.get("TPE1"), tag.get("TIT2"), tag.get("TCOM"), tag.get("TALB"), tag.get("TDRC"),
                      tag.get("TCON"), tag.get("TPUB"), tag.get("TSRC"), tag.get("TLEN"), id3_error)
        if id3.duration is "":
            id3.duration = song_length(song.location_local)
        return song, id3
    else:
        print("File does not exist")
        return song, None


def get_genre_id(genre, reverse_genre_map):
    genre = genre.lower()
    if genre in reverse_genre_map:
        return reverse_genre_map[genre]
    else:
        return -1


def copy_text(text_1, text_2, end):
    text_2.delete(1.0, end)
    text_2.insert(end, text_1.get("1.0", end))
    text_1.config(bg="white")
    text_2.config(bg="white")


def insert_string(string1, string2, label_db, label_id3, end):
    if string1 == "-" or string1 is None:
        string1 = ""
    if string2 == "-" or string2 is None:
        string2 = ""
    label_db.delete(1.0, end)
    label_db.insert(1.0, string1)
    label_db.config(bg="white")
    label_id3.delete(1.0, end)
    label_id3.insert(1.0, string2)
    label_id3.config(bg="white")
    if str(string1) == "" or str(string1) != str(string2):
        label_db.config(bg="light salmon")
        label_id3.config(bg="light salmon")


def check_genre(database_genre, id3_genre):
    list_db = list(dict.fromkeys(database_genre.split(", ")))[:3]
    list_id3 = list(dict.fromkeys(id3_genre.split(", ")))
    for item in list_db:
        if item not in list_id3:
            print("Genre mismatch")
            print("DB: ", item)
            print("ID3: ", list_id3)
            return False
    return True


def discogs_lookup(song):
    google_string = song.artist + " " + song.title
    google_string = google_string.replace(" ", "%20")
    google_string = google_string.replace("-", "").replace("&", "").replace("#", "").replace("\\", "")
    system("start https://www.discogs.com/search?q=" + google_string)


def google_lookup(song):
    google_string = song.artist + " " + song.title
    google_string = google_string.replace(" ", "%20")
    google_string = google_string.replace("-", "").replace("&", "").replace("#", "").replace("\\", "")
    system("start https://duckduckgo.com/?q=" + google_string)
