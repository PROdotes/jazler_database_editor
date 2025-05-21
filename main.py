import shutil
from tkinter import *
from tkinter import messagebox
from pyodbc import connect
from my_methods import *

# Constants and Configuration
file = '\\\\ONAIR\\Jazler RadioStar 2\\Databases\\JZRS2DB-V5.accdb'
table_name = 'snDatabase'
#file = live_file

conn = connect('Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + file)
cursor = conn.cursor()

table_names(cursor)

column_names(cursor, table_name)

genre_map = generate_genre_map(cursor)
reverse_genre_map = {v: k for k, v in genre_map.items()}

decade_map = generate_decade_map(cursor)
reverse_decade_map = {v: k for k, v in decade_map.items()}

tempo_map = generate_tempo_map(cursor)

#cursor.execute("SELECT * from " + table_name)
#cursor.execute("SELECT * from " + table_name + " WHERE fldCat2 = 0")
#cursor.execute("SELECT * from " + table_name + " WHERE fldYear = 2024")
#cursor.execute("SELECT * from " + table_name + " WHERE fldTitle LIKE '%Prije sna%'")
#cursor.execute("SELECT * from " + table_name + " WHERE fldFilename LIKE '%z:%'")
cursor.execute("SELECT * from " + table_name + " WHERE fldArtistName LIKE '%Fall Out Boy%'")
song_query = cursor.fetchall()
position = 0
song, id3, tag = get_data(song_query, position, genre_map, decade_map, tempo_map)


def update_fields():
    global label_counter, text_jump
    insert_string(song.artist, id3.artist, texts_db["artist"], texts_id3["artist"])
    insert_string(song.title, id3.title, texts_db["title"], texts_id3["title"])
    insert_string(song.album, id3.album, texts_db["album"], texts_id3["album"])
    insert_string(song.composer, id3.composer, texts_db["composer"], texts_id3["composer"])
    insert_string(song.publisher, id3.publisher, texts_db["publisher"], texts_id3["publisher"])
    insert_string(song.year, id3.year, texts_db["year"], texts_id3["year"])
    insert_string(song.genre, id3.genre, texts_db["genre"], texts_id3["genre"])
    insert_string(song.isrc, id3.isrc, texts_db["isrc"], texts_id3["isrc"])
    label_counter.config(text=str(position + 1) + "/" + str(len(song_query)))
    label_id3_error.config(text=id3.error)
    if id3.error != "No error":
        label_id3_error.config(bg="light salmon")
    else:
        label_id3_error.config(bg="DarkSeaGreen")
    text_jump.delete(1.0, END)
    text_jump.insert(1.0, str(position + 1))
    label_counter.config(text=str(position + 1) + "/" + str(len(song_query)))
    label_filename.config(text=(song.location_local + " ----- " + song.location_correct).replace("z:\\songs\\", ""))
    if song.location_local.lower() == song.location_correct.lower():
        label_filename.config(bg="DarkSeaGreen")
    else:
        label_filename.config(bg="light salmon")


def song_rename():
    global song
    location_db = song.location_correct.replace("z:", "b:")
    cursor.execute("UPDATE " + table_name + " SET fldFilename = ? WHERE AUID = ?", location_db, song.id)
    conn.commit()
    if not os.path.exists(song.location_correct):
        os.makedirs(os.path.dirname(song.location_correct), exist_ok=True)
    shutil.move(song.location_local, song.location_correct)
    song.location_local = song.location_correct
    song_query[position][20] = song.location_correct


def save_song(rename):
    global song, id3, tag
    # song.artist = texts_db["artist"].get("1.0", END).strip()
    song.title = texts_db["title"].get("1.0", END).strip()
    song.album = texts_db["album"].get("1.0", END).strip()
    song.composer = texts_db["composer"].get("1.0", END).strip()
    song.publisher = texts_db["publisher"].get("1.0", END).strip()
    song.year = texts_db["year"].get("1.0", END).strip()
    song.genre = texts_db["genre"].get("1.0", END).strip()
    song.isrc = texts_db["isrc"].get("1.0", END).strip()
    song.decade = calc_decade(int(song.year))
    song.genre_04_name = song.decade
    if not song.year == "0":
        song.genre_04_id = reverse_decade_map[song.decade]

    id3.artist = texts_id3["artist"].get("1.0", END).strip()
    id3.title = texts_id3["title"].get("1.0", END).strip()
    id3.album = texts_id3["album"].get("1.0", END).strip()
    id3.composer = texts_id3["composer"].get("1.0", END).strip()
    id3.publisher = texts_id3["publisher"].get("1.0", END).strip()
    id3.year = texts_id3["year"].get("1.0", END).strip()
    id3.genre = texts_id3["genre"].get("1.0", END).strip()
    id3.isrc = texts_id3["isrc"].get("1.0", END).strip()


    def is_valid_attribute(value):
        return value is not None and value != ""

    def check_all():
        attributes = ['artist', 'title', 'album', 'year', 'composer', 'publisher', 'genre']
        for attr in attributes:
            if not is_valid_attribute(getattr(song, attr)):
                return False
            if not getattr(song, attr) == getattr(id3, attr):
                return False
            if not song.isrc == id3.isrc:
                return False
        return True

    field_check = check_all()
    year_check = True
    if song.year == "0":
        year_check = False

    genre_id = get_genre_id(song.genre, reverse_genre_map)
    genre_id_check = (genre_id != -1)

    if not year_check:
        messagebox.showwarning("Warning", "Year not set!")
    if not genre_id_check:
        messagebox.showwarning("Warning", "Genre not found!")
    if not field_check:
        messagebox.showwarning("Warning", "Not all fields are filled in correctly!")
    if field_check and genre_id_check and year_check:
        cursor.execute(
            "UPDATE " + table_name + " SET fldTitle = ?, fldAlbum = ?, fldYear = ?, fldComposer = ?, fldLabel = ?," +
            " fldCat1a = ?, fldCDKey = ?, fldCat2 = ?, fldDuration = ? WHERE AUID = ?",
            song.title, song.album, song.year, song.composer, song.publisher, genre_id, song.isrc, song.genre_04_id,
            song.duration, song.id)
        conn.commit()
        tag["TPE1"] = id3.artist
        tag["TIT2"] = id3.title
        tag["TALB"] = id3.album
        tag["TCOM"] = id3.composer
        tag["TPUB"] = id3.publisher
        tag["TYER"] = id3.year
        tag["TCON"] = id3.genre
        tag["TSRC"] = id3.isrc
        tag["TLEN"] = id3.duration
        tag.write()
        cursor.execute("SELECT * from " + table_name + " WHERE AUID = ?", song.id)
        result = cursor.fetchall()[0]
        song_query[position] = result
        print(result)
        messagebox.showinfo("Info", "Song saved!")
        if rename:
            song_rename()
    update_fields()


def get_song(delta):
    global position, song, id3, tag
    if delta is None:
        delta = 0
        test = text_jump.get(1.0, END)
        print("-" + test + "-")
        position = int(test) - 1
        if position == 0:
            position = 1
    position += delta
    if position == -1:
        position = 0
    if position == len(song_query):
        position = len(song_query) - 1
    song, id3, tag = get_data(song_query, position, genre_map, decade_map, tempo_map)
    update_fields()



window = Tk()

# Create dictionaries to store widgets
labels_db = {}
labels_id3 = {}
texts_db = {}
texts_id3 = {}
buttons_db = {}
buttons_id3 = {}

# Initial labels
row_count = 1
label_counter = Label(window, text="0/0")
label_counter.grid(row=row_count, column=7)
label_id3_error = Label(window, text="")
label_id3_error.grid(row=row_count, column=8)
label_filename = Label(window, text="File: ")
label_filename.grid(row=row_count, column=2, columnspan=5)
row_count += 1

# Create widgets for each field
fields = ["artist", "title", "album", "composer", "publisher", "year", "genre", "isrc"]
for field in fields:
    # Create labels
    labels_db[field] = Label(window, text=f"{field} DB: ")
    labels_id3[field] = Label(window, text=f"{field} ID3: ")

    # Create text widgets
    texts_db[field] = Text(window, height=1, width=40)
    texts_id3[field] = Text(window, height=1, width=40)

    # Create buttons
    buttons_db[field] = Button(window, text="->")
    if field != "artist":
        buttons_id3[field] = Button(window, text="<-")

    # Grid the widgets
    labels_db[field].grid(row=row_count, column=1)
    texts_db[field].grid(row=row_count, column=2, columnspan=2)
    buttons_db[field].grid(row=row_count, column=4)
    buttons_db[field].bind("<Button-1>", lambda event, f=field: copy_text(texts_db[f], texts_id3[f]))
    if field != "artist":
        buttons_id3[field].grid(row=row_count, column=5)
        buttons_id3[field].bind("<Button-1>", lambda event, f=field: copy_text(texts_id3[f], texts_db[f]))
    texts_id3[field].grid(row=row_count, column=6, columnspan=2)
    labels_id3[field].grid(row=row_count, column=8)

    # Increment row count
    row_count += 1


row_count += 1
button_google = Button(text="Google (F8)", command=lambda : google_lookup(song))
button_google.grid(row=row_count, column=1)
button_discog = Button(text="Discogs (F9)", command=lambda : discogs_lookup(song))
button_discog.grid(row=row_count, column=2)
button_save = Button(text="Save (F5)", command=lambda : save_song(False))
button_save.grid(row=row_count, column=3)

button_next = Button(text="Next →→", command=lambda : get_song(1))
button_next.grid(row=row_count, column=7)
button_previous = Button(text="←← Prev", command=lambda : get_song(-1))
button_previous.grid(row=row_count, column=6)

text_jump = Text(height=1, width=5)
text_jump.insert(1.0, "1")
text_jump.grid(row=row_count, column=8)
button_jump = Button(text="▲ Jump ▲", command=lambda : text_jump.focus())
button_jump.grid(row=row_count, column=9)

button_rename = Button(text="Rename (F6)", command=lambda : save_song(True))
button_rename.grid(row=1, column=1)

window.bind("<Return>", lambda event: get_song(None))
window.bind("<Control-Left>", lambda event: get_song(-1))
window.bind("<Control-Right>", lambda event: get_song(1))
window.bind("<Up>", lambda event: text_jump.focus())
window.bind("<F5>", lambda event: save_song(False))
window.bind("<F6>", lambda event: save_song(True))
window.bind("<F8>", lambda event: google_lookup(song))
window.bind("<F9>", lambda event: discogs_lookup(song))


update_fields()

window.mainloop()
