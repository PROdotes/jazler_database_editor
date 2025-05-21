from os import system
from tkinter import END

import stagger
from stagger.id3 import *

from Song import *


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


def get_data(song_query, number, genre_map, decade_map, tempo_map):
    row = song_query[number]
    song = Song(row, genre_map, decade_map, tempo_map)

    song.id3_data()
    #print(song.duration)
    if song.duration == 0:
        song.duration = song_length(song.location_local)
    print(song.location_local)

    if song.exists:
        try:
            tag = stagger.read_tag(song.location_local)
            id3_error = ""
        except Exception as e:
            print(f"---Error while reading tag: {e}")
            id3_error = "ID3 tag error"
            tag = stagger.default_tag()
        i3d_tags = ["TPE1", "TIT2", "TCOM", "TALB", "TCON", "TPUB", "TSRC", "TDRC", "TLEN"]
        for id3_name in i3d_tags:
            if not tag.__contains__(id3_name):
                tag.__setitem__(id3_name, "")
        # print(f'Artist: {tag[TPE1]}, Title: {tag[TIT2]}, Composer: {tag[TCOM]}, Album: {tag[TALB]}, '
        #       f'Year: {tag[TDRC]}, Genres: {tag[TCON]}, Publisher: {tag[TPUB]}, ISRC: {tag[TSRC]}')
        id3 = SongID3(tag.artist, tag.title, tag.composer, tag.album,
                      tag[TDRC].text[0], tag.genre.lower(), tag[TPUB].text[0], tag[TSRC].text[0], tag[TLEN].text[0],
                      id3_error)
        return song, id3, tag


def get_genre_id(genre, reverse_genre_map):
    genre=genre.lower()
    if genre in reverse_genre_map:
        return reverse_genre_map[genre]
    else:
        return -1


def copy_text(text_1, text_2):
    text_2.delete(1.0, END)
    text_2.insert(END, text_1.get("1.0", END))
    text_1.config(bg="white")
    text_2.config(bg="white")


def insert_string(string1, string2, label_db, label_id3):
    if string1 == "-":
        string1 = ""
    if string2 == "-":
        string2 = ""
    if string1 is None or string1 == "":
        string1 = string2
    if string2 is None or string2 == "":
        string2 = string1
    label_db.delete(1.0, END)
    label_db.insert(1.0, string1)
    label_id3.delete(1.0, END)
    label_id3.insert(1.0, string2)
    if str(string1) == "" or str(string1) != str(string2):
        label_db.config(bg="light salmon")
    else:
        label_db.config(bg="white")
    if str(string2) == "" or str(string1) != str(string2):
        label_id3.config(bg="light salmon")
    else:
        label_id3.config(bg="white")


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
