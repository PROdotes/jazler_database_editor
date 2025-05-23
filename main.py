import shutil
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox
from my_methods import *
from database import Database

# Constants and Configuration
# WARNING! LIVE FILE!!!
# changed database to backup database
file = '\\\\ONAIR\\Jazler RadioStar 2\\Databases - Copy\\JZRS2DB-V5.accdb'
table_name = 'snDatabase'
db = Database(file, table_name)

#print("Available tables:", db.table_names())
#print("Columns:", db.column_names())

genre_map = db.generate_genre_map()
reverse_genre_map = {v: k for k, v in genre_map.items()}

decade_map = db.generate_decade_map()
reverse_decade_map = {v: k for k, v in decade_map.items()}

tempo_map = db.generate_tempo_map()

def query_execute(field_in, match, query):
    field_out = "fldArtistName"
    if field_in == "artist":
        field_out = "fldArtistName"
    elif field_in == "title":
        field_out = "fldTitle"
    elif field_in == "album":
        field_out = "fldAlbum"
    elif field_in == "composer":
        field_out = "fldComposer"
    elif field_in == "publisher":
        field_out = "fldLabel"
    elif field_in == "year":
        field_out = "fldYear"

    if match == "contains":
        return db.fetch_songs(field_out, query, False)
    elif match == "equals":
        return db.fetch_songs(field_out, query, True)

def get_query():
    return query_execute("artist", "contains", "")

song_query = get_query()
position = 0
song, id3 = get_data(song_query[position], genre_map, decade_map, tempo_map)


def update_fields():
    global label_counter, text_jump, song_query, id3
    if id3 is None:
        choice = messagebox.askyesno("Error", "No song selected! Delete database entry?")
        if choice:
            db.delete_song(song_query[position][0])
            song_query = get_query()
            get_song(0)
        else:
            id3 = SongID3("", "", "", "", "0", "", "", "", "0", "FILE NOT FOUND")

    texts_db["artist"].config(state="normal")
    insert_string(song.artist, id3.artist, texts_db["artist"], texts_id3["artist"])
    texts_db["artist"].config(state="disabled")
    insert_string(song.title, id3.title, texts_db["title"], texts_id3["title"])
    insert_string(song.album, id3.album, texts_db["album"], texts_id3["album"])
    insert_string(song.composer, id3.composer, texts_db["composer"], texts_id3["composer"])
    insert_string(song.publisher, id3.publisher, texts_db["publisher"], texts_id3["publisher"])
    insert_string(song.year, id3.year, texts_db["year"], texts_id3["year"])
    texts_db["decade"].config(state="normal")
    texts_id3["decade"].config(state="normal")
    insert_string(song.decade, song.decade, texts_db["decade"], texts_id3["decade"])
    texts_db["decade"].config(state="disabled")
    texts_id3["decade"].config(state="disabled")
    insert_string(song.genres_all, id3.genres_all, texts_db["genre"], texts_id3["genre"])
    test_genre = check_genre(song.genres_all, id3.genres_all)
    if test_genre:
        texts_db["genre"].config(bg="white")
        texts_id3["genre"].config(bg="white")
    else:
        texts_db["genre"].config(bg="light salmon")
        texts_id3["genre"].config(bg="light salmon")
    texts_db["duration"].config(state="normal")
    texts_id3["duration"].config(state="normal")
    insert_string(song.duration, song.duration, texts_db["duration"], texts_id3["duration"])
    texts_db["duration"].config(state="disabled")
    texts_id3["duration"].config(state="disabled")
    insert_string(song.isrc, id3.isrc, texts_db["isrc"], texts_id3["isrc"])
    label_counter.config(text=str(position + 1) + "/" + str(len(song_query)))
    label_id3_error.config(text=id3.error)
    label_id3_error.config(bg="DarkSeaGreen")
    if id3.error != "No error":
        label_id3_error.config(bg="light salmon")
    text_jump.delete(1.0, END)
    text_jump.insert(1.0, str(position + 1))
    label_counter.config(text=str(position + 1) + "/" + str(len(song_query)))
    label_filename.config(text=(song.location_local + "    <--->    " + song.location_correct).replace("z:\\songs\\", ""))
    label_filename.config(bg="light salmon")
    if song.location_local.lower() == song.location_correct.lower():
        label_filename.config(bg="DarkSeaGreen")


def song_rename():
    global song
    location_db = song.location_correct.replace("z:", "b:")
    db.update_song_filename(song.id, location_db)
    if not os.path.exists(song.location_correct):
        os.makedirs(os.path.dirname(song.location_correct), exist_ok=True)
    shutil.move(song.location_local, song.location_correct)
    song.location_local = song.location_correct
    song_query[position][20] = song.location_correct


def save_song(rename):
    global song, id3
    # song.artist = texts_db["artist"].get("1.0", END).strip()
    song.title = texts_db["title"].get("1.0", END).strip()
    song.album = texts_db["album"].get("1.0", END).strip()
    song.composer = texts_db["composer"].get("1.0", END).strip()
    song.publisher = texts_db["publisher"].get("1.0", END).strip()
    song.year = int(texts_db["year"].get("1.0", END).strip())
    song.genres_all = texts_db["genre"].get("1.0", END).strip()
    song.isrc = texts_db["isrc"].get("1.0", END).strip()
    song.decade = calc_decade(song.year)
    song.genre_04_name = song.decade
    if not song.year == 0:
        song.genre_04_id = reverse_decade_map[song.decade]

    id3.artist = texts_id3["artist"].get("1.0", END).strip()
    id3.title = texts_id3["title"].get("1.0", END).strip()
    id3.album = texts_id3["album"].get("1.0", END).strip()
    id3.composer = texts_id3["composer"].get("1.0", END).strip()
    id3.publisher = texts_id3["publisher"].get("1.0", END).strip()
    id3.year = int(texts_id3["year"].get("1.0", END).strip())
    id3.genres_all = texts_id3["genre"].get("1.0", END).strip()
    id3.isrc = texts_id3["isrc"].get("1.0", END).strip()


    def is_valid_attribute(value):
        return value is not None and value != ""

    def check_all():
        attributes = ['artist', 'title', 'album', 'year', 'composer', 'publisher']
        for attr in attributes:
            if not is_valid_attribute(getattr(song, attr)):
                messagebox.showwarning("Warning", f"'{attr}' not set!")
                return False
            if not getattr(song, attr) == getattr(id3, attr):
                messagebox.showwarning("Warning", f"'{attr}' not the same!")
                return False
            if not song.isrc == id3.isrc:
                return False
        return True

    field_check = check_all()
    year_check = True
    if song.year == 0:
        messagebox.showwarning("Warning", "Year not set!")
        year_check = False

    genre_id_check = True
    genre_ids = song.genres_all.split(", ")
    genre_ids = list(dict.fromkeys(genre_ids))
    print(genre_ids)
    texts_db["genre"].delete(1.0, END)
    song.genres_all = list_to_string(genre_map[0], genre_ids)
    texts_db["genre"].insert(1.0, song.genres_all)
    genre_ids = genre_ids[:3]
    for genre_id in genre_ids:
        if genre_id not in genre_map.values():
            messagebox.showwarning("Warning", f"Genre '{genre_id}' not found!")
            genre_id_check = False
            break
    genre_test = check_genre(song.genres_all, id3.genres_all)
    if not genre_test:
        messagebox.showwarning("Warning", "Genres not the same!")
    genre_id_check = genre_id_check and genre_test
    if genre_id_check:
        song.genre_01_name = genre_ids[0]
        song.genre_01_id = get_genre_id(genre_ids[0], reverse_genre_map)
        if len(genre_ids) > 1:
            song.genre_02_name = genre_ids[1]
            song.genre_02_id = get_genre_id(genre_ids[1], reverse_genre_map)
        else:
            song.genre_02_name = genre_map[0]
            song.genre_02_id = 0
        if len(genre_ids) > 2:
            song.genre_03_name = genre_ids[2]
            song.genre_03_id = get_genre_id(genre_ids[2], reverse_genre_map)
        else:
            song.genre_03_name = genre_map[0]
            song.genre_03_id = 0

    if field_check and genre_id_check and year_check:
        # Gather fields to update
        update_fields_dict = {
            "fldTitle": song.title,
            "fldAlbum": song.album,
            "fldYear": song.year,
            "fldComposer": song.composer,
            "fldLabel": song.publisher,
            "fldCat1a": get_genre_id(song.genre_01_name, reverse_genre_map),
            "fldCat1b": get_genre_id(song.genre_02_name, reverse_genre_map),
            "fldCat1c": get_genre_id(song.genre_03_name, reverse_genre_map),
            "fldCDKey": song.isrc,
            "fldCat2": song.genre_04_id,
            "fldDuration": song.duration,
        # Add other fields as needed
        }
        db.update_song_fields(song.id, update_fields_dict)
        tag_write(id3, song.location_local)
        result = db.fetch_songs("AUID", song.id, True)
        song_query[position] = result
        print(result)
        messagebox.showinfo("Info", "Song saved!")
        if rename:
            song_rename()
    update_fields()


def get_song(delta):
    global position, song, id3
    if delta is None:
        delta = 0
        test = text_jump.get(1.0, END)
        print("-" + test + "-")
        position = int(test) - 1
        if position == -1:
            position = 0
    position += delta
    if position == -1:
        position = 0
    if position == len(song_query):
        position = len(song_query) - 1
    song, id3 = get_data(song_query[position], genre_map, decade_map, tempo_map)
    update_fields()

def query_db():
    window_query = Toplevel(window)
    window_query.title("Database query")
    dropdown_field = Combobox(window_query, values=["artist", "title", "album", "composer", "publisher", "year"])
    dropdown_field.grid(row=0, column=0)
    dropdown_field.set("artist")
    dropdown_match = Combobox(window_query, values=["contains", "equals"])
    dropdown_match.grid(row=0, column=1)
    dropdown_match.set("contains")
    text_query = Text(window_query, height=1, width=50)
    text_query.grid(row=0, column=2)
    button_send_query = Button(window_query, text="Query", command=lambda: query_button_click(dropdown_field.get(),dropdown_match.get(),
                                                                                              text_query.get("1.0", END).strip(), window_query))
    button_send_query.grid(row=0, column=3)
    window_query.bind("<Return>", lambda event: query_button_click(dropdown_field.get(), dropdown_match.get(),
                                                                   text_query.get("1.0", END).strip(), window_query))
    window.withdraw()

def query_button_click(drop_field, drop_match, text_query, window_sent):
    global song_query
    song_query = query_execute(drop_field, drop_match, text_query)
    get_song(0)
    window_sent.withdraw()
    window.deiconify()

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
label_filename = Label(window, text="File: ")
label_filename.grid(row=row_count, column=1, columnspan=8)
row_count += 1

# Create widgets for each field
fields = ["artist", "title", "album", "composer", "publisher", "year", "decade", "genre", "isrc", "duration"]
for field in fields:
    # Create labels
    labels_db[field] = Label(window, text=f"{field} DB: ", width=15, anchor="e")
    labels_id3[field] = Label(window, text=f"{field} ID3: ", width=15, anchor="w")

    # Create text widgets
    texts_db[field] = Text(window, height=1, width=50)
    texts_id3[field] = Text(window, height=1, width=50)
    #if field is "decade" lock the text widget for manual input
    if field == "decade" or field == "duration" or field == "artist":
        texts_db[field].config(state="disabled", fg="gray")
        if field != "artist":
            texts_id3[field].config(state="disabled", fg="gray")

    # Create buttons
    buttons_db[field] = Button(window, text="->", width=3)
    buttons_id3[field] = Button(window, text="<-", width=3)

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


button_query = Button(text="Query (F1)", command=lambda : query_db())
button_query.grid(row=row_count, column=1)
button_google = Button(text="Google (F3)", command=lambda : google_lookup(song))
button_google.grid(row=row_count, column=2)
button_discog = Button(text="Discogs (F4)", command=lambda : discogs_lookup(song))
button_discog.grid(row=row_count, column=3)

button_save = Button(text="Save (F5)", command=lambda : save_song(False))
button_save.grid(row=row_count, column=6)
button_rename = Button(text="Rename (F6)", command=lambda : save_song(True))
button_rename.grid(row=row_count, column=7)
label_id3_error = Label(window, text="")
label_id3_error.grid(row=row_count, column=8)



row_count += 1

button_previous = Button(text="Prev (F9)", command=lambda : get_song(-1))
button_previous.grid(row=row_count, column=2)
button_next = Button(text="Next (F10)", command=lambda : get_song(1))
button_next.grid(row=row_count, column=3)

button_jump = Button(text="Jump (F11)", command=lambda : text_jump.focus())
button_jump.grid(row=row_count, column=6)
text_jump = Text(height=1, width=5)
text_jump.insert(1.0, "1")
text_jump.grid(row=row_count, column=7)
label_counter = Label(window, text="0/0")
label_counter.grid(row=row_count, column=8)
label_counter.config(bg="DarkSeaGreen")



window.bind("<F1>", lambda event: query_db())
window.bind("<F3>", lambda event: google_lookup(song))
window.bind("<F4>", lambda event: discogs_lookup(song))
window.bind("<F5>", lambda event: save_song(False))
window.bind("<F6>", lambda event: save_song(True))
window.bind("<F9>", lambda event: get_song(-1))
window.bind("<F10>", lambda event: get_song(1))
window.bind("<F11>", lambda event: get_song(None))
window.bind("<F12>", lambda event: text_jump.focus())


get_song(0)

window.mainloop()
