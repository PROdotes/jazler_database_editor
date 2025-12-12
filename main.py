import shutil
import sys
import threading
import webbrowser
from typing import Any, Tuple
from os import makedirs
from os import path
from tkinter import Tk, Toplevel, Label, Button, Text, END, messagebox
from tkinter.ttk import Combobox
from Song import SongID3, list_to_string, calc_decade, get_genre_id, check_genre, get_data
from mp3_stuff import tag_write
from database import Database
from config import DB_PATH_LIVE, DB_PATH_TEST, save_last_query, load_last_query


class JazlerEditor(Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide the main window immediately
        
        # Determine database
        self.use_live, self.file, self.table_name = self.setup_database_config()
        self.db = self.connect_database()

        # Data Maps
        self.genre_map = self.db.generate_genre_map()
        self.reverse_genre_map = {v: k for k, v in self.genre_map.items()}
        self.decade_map = self.db.generate_decade_map()
        self.reverse_decade_map = {v: k for k, v in self.decade_map.items()}
        self.tempo_map = self.db.generate_tempo_map()

        # State Variables
        self.song = None
        self.id3 = None
        self.song_query = self.get_initial_query()
        self.position = 0

        # UI Initialization
        self.setup_ui()
        
        # Load first song
        if self.song_query:
            self.get_song(0)
        else:
            messagebox.showinfo("Info", "No songs found for initial query.")

    def setup_database_config(self):
        start_root = Tk()
        start_root.withdraw()
        start_root.attributes('-topmost', True)
        use_live = messagebox.askyesno(
            "Select Database", 
            "Do you want to use the LIVE database?\n\nYES: Live (Databases)\nNO: Test (Databases - Copy)", 
            parent=start_root
        )
        start_root.destroy()

        if use_live:
            file = DB_PATH_LIVE
        else:
            file = DB_PATH_TEST
        
        return use_live, file, 'snDatabase'

    def connect_database(self):
        try:
            return Database(self.file, self.table_name)
        except Exception as e:
            root = Tk()
            root.withdraw()
            messagebox.showerror("Connection Error", f"Could not connect to Database at:\n{self.file}\n\nError: {e}")
            sys.exit(1)

    def setup_ui(self):
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.title(f"Jazler Editor - [{'LIVE' if self.use_live else 'TEST'}]")

        # Database Status Indicator
        db_status_text = "⚠️ CAUTION: LIVE DATABASE ⚠️" if self.use_live else "SAFE MODE: Test Database"
        db_status_bg = "red" if self.use_live else "forest green"
        label_db_status = Label(self, text=db_status_text, bg=db_status_bg, fg="white", font=("Helvetica", 12, "bold"))
        label_db_status.grid(row=0, column=1, columnspan=8, sticky="ew", pady=(5, 5))

        # Containers
        self.labels_db = {}
        self.labels_id3 = {}
        self.texts_db = {}
        self.texts_id3 = {}
        self.buttons_db = {}
        self.buttons_id3 = {}

        # Initial labels
        row_count = 1
        self.label_filename = Label(self, text="File: ")
        self.label_filename.grid(row=row_count, column=1, columnspan=8)
        row_count += 1

        # Create widgets for each field
        fields = ["artist", "title", "album", "composer", "publisher", "year", "decade", "genre", "isrc", "duration"]
        for field in fields:
            self.labels_db[field] = Label(self, text=f"{field} DB: ", width=15, anchor="e")
            self.labels_id3[field] = Label(self, text=f"{field} ID3: ", width=15, anchor="w")

            self.texts_db[field] = Text(self, height=1, width=50)
            self.texts_id3[field] = Text(self, height=1, width=50)

            if field in ["decade", "duration", "artist"]:
                self.texts_db[field].config(state="disabled", fg="gray")
                if field != "artist":
                    self.texts_id3[field].config(state="disabled", fg="gray")

            self.buttons_db[field] = Button(self, text="->", width=3)
            self.buttons_id3[field] = Button(self, text="<-", width=3)

            self.labels_db[field].grid(row=row_count, column=1)
            self.texts_db[field].grid(row=row_count, column=2, columnspan=2)
            self.buttons_db[field].grid(row=row_count, column=4)
            self.buttons_db[field].bind("<Button-1>", lambda event, f=field: copy_text(self.texts_db[f], self.texts_id3[f], END))

            if field != "artist":
                self.buttons_id3[field].grid(row=row_count, column=5)
                self.buttons_id3[field].bind("<Button-1>", lambda event, f=field: copy_text(self.texts_id3[f], self.texts_db[f], END))

            self.texts_id3[field].grid(row=row_count, column=6, columnspan=2)
            self.labels_id3[field].grid(row=row_count, column=8)
            row_count += 1

        # Control Buttons
        self.button_query = Button(self, text="Query (F1)", command=self.query_db)
        self.button_query.grid(row=row_count, column=1)
        
        self.button_google = Button(self, text="Google (F3)", command=lambda: google_lookup(self.song))
        self.button_google.grid(row=row_count, column=2)
        
        self.button_discog = Button(self, text="Discogs (F4)", command=lambda: discogs_lookup(self.song))
        self.button_discog.grid(row=row_count, column=3)
        
        self.button_save = Button(self, text="Save (F5)", command=lambda: self.save_song(False))
        self.button_save.grid(row=row_count, column=6)
        
        self.button_rename = Button(self, text="Rename (F6)", command=lambda: self.save_song(True))
        self.button_rename.grid(row=row_count, column=7)
        
        self.label_id3_error = Label(self, text="")
        self.label_id3_error.grid(row=row_count, column=8)
        
        row_count += 1
        
        self.button_previous = Button(self, text="Prev (F9)", command=lambda: self.get_song(-1))
        self.button_previous.grid(row=row_count, column=2)
        
        self.button_next = Button(self, text="Next (F10)", command=lambda: self.get_song(1))
        self.button_next.grid(row=row_count, column=3)
        
        self.button_jump = Button(self, text="Jump (F11)", command=lambda: self.get_song(None))
        self.button_jump.grid(row=row_count, column=6)
        
        self.text_jump = Text(self, height=1, width=5)
        self.text_jump.insert(1.0, "1")
        self.text_jump.grid(row=row_count, column=7)
        
        self.label_counter = Label(self, text="0/0")
        self.label_counter.grid(row=row_count, column=8)
        self.label_counter.config(bg="DarkSeaGreen")

        # Key Bindings
        self.bind("<F1>", lambda event: self.query_db())
        self.bind("<F3>", lambda event: google_lookup(self.song))
        self.bind("<F4>", lambda event: discogs_lookup(self.song))
        self.bind("<F5>", lambda event: self.save_song(False))
        self.bind("<F6>", lambda event: self.save_song(True))
        self.bind("<F9>", lambda event: self.get_song(-1))
        self.bind("<F10>", lambda event: self.get_song(1))
        self.bind("<F11>", lambda event: self.get_song(None))
        self.bind("<F12>", lambda event: self.text_jump.focus())

    def toggle_controls(self, state="normal"):
        """Enable or disable navigations buttons to prevent race conditions."""
        state_val = "normal" if state else "disabled"
        buttons = [
            self.button_previous, self.button_next, self.button_jump,
            self.button_query, self.button_save, self.button_rename,
            self.button_google, self.button_discog
        ]
        for btn in buttons:
            btn.config(state=state_val)

    def query_execute(self, field_in, match, query):
        save_last_query(field_in, match, query)
        field_out = "fldArtistName"
        mapping = {
            "artist": "fldArtistName",
            "title": "fldTitle",
            "album": "fldAlbum",
            "composer": "fldComposer",
            "publisher": "fldLabel",
            "year": "fldYear"
        }
        if field_in in mapping:
            field_out = mapping[field_in]

        if match == "contains":
            return self.db.fetch_songs(field_out, query, False)
        elif match == "equals":
            return self.db.fetch_songs(field_out, query, True)
        return []

    def get_initial_query(self):
        last_query = load_last_query()
        if last_query:
            try:
                print(f"Loading last query: {last_query}")
                return self.query_execute(last_query["field"], last_query["match"], last_query["value"])
            except Exception as e:
                print(f"Error executing last query: {e}")
                
        return self.db.fetch_all_songs()

    def update_fields(self):
        if self.id3 is None:
            choice = messagebox.askyesno("Error", "No song selected! Delete database entry?")
            if choice:
                self.db.delete_song(self.song_query[self.position][0])
                self.song_query = self.get_initial_query()
                self.get_song(0)
                return
            else:
                self.id3 = SongID3("", "", "", "", "0", "", "", "", "0", "FILE NOT FOUND")

        self.texts_db["artist"].config(state="normal")
        self._update_text_field("artist", self.song.artist, self.id3.artist)
        self.texts_db["artist"].config(state="disabled")
        
        for field in ["title", "album", "composer", "publisher", "year", "genres_all", "isrc"]:
            val_song = getattr(self.song, field)
            val_id3 = getattr(self.id3, field)
            # Map 'genres_all' to 'genre' widget
            widget_key = "genre" if field == "genres_all" else field
            self._update_text_field(widget_key, val_song, val_id3)

        # Decade
        self.texts_db["decade"].config(state="normal")
        self.texts_id3["decade"].config(state="normal")
        self._update_text_field("decade", self.song.decade, self.song.decade)
        self.texts_db["decade"].config(state="disabled")
        self.texts_id3["decade"].config(state="disabled")

        # Duration
        self.texts_db["duration"].config(state="normal")
        self.texts_id3["duration"].config(state="normal")
        self._update_text_field("duration", self.song.duration, self.song.duration)
        self.texts_db["duration"].config(state="disabled")
        self.texts_id3["duration"].config(state="disabled")

        self._update_status_indicators()

    def _update_text_field(self, field, val_song, val_id3):
        txt_db = self.texts_db[field]
        txt_id3 = self.texts_id3[field]
        
        val1, val2, color = process_string_comparison(val_song, val_id3)
        
        txt_db.delete(1.0, END)
        txt_db.insert(1.0, val1)
        txt_db.config(bg=color)
        
        txt_id3.delete(1.0, END)
        txt_id3.insert(1.0, val2)
        txt_id3.config(bg=color)

    def _update_status_indicators(self):
        # Genre Validation
        test_genre = check_genre(self.song.genres_all, self.id3.genres_all)
        bg_genre = "white" if test_genre else "light salmon"
        self.texts_db["genre"].config(bg=bg_genre)
        self.texts_id3["genre"].config(bg=bg_genre)
            
        # ISRC Validation
        if not self.song.isrc and not self.id3.isrc:
            self.texts_db["isrc"].config(bg="white")
            self.texts_id3["isrc"].config(bg="white")
            
        # Count & Error Validation
        self.label_counter.config(text=f"{self.position + 1}/{len(self.song_query)}")
        self.label_id3_error.config(text=self.id3.error)
        bg_error = "DarkSeaGreen" if self.id3.error == "No error" else "light salmon"
        self.label_id3_error.config(bg=bg_error)
            
        self.text_jump.delete(1.0, END)
        self.text_jump.insert(1.0, str(self.position + 1))
        
        # File Validation
        clean_loc = (self.song.location_local + "    <--->    " + self.song.location_correct).replace("z:\\songs\\", "")
        self.label_filename.config(text=clean_loc)
        
        bg_file = "DarkSeaGreen" if self.song.location_local.lower() == self.song.location_correct.lower() else "light salmon"
        self.label_filename.config(bg=bg_file)

    def song_rename(self):
        location_db = self.song.location_correct.replace("z:", "b:")
        self.db.update_song_filename(self.song.id, location_db)
        if not path.exists(self.song.location_correct):
            makedirs(path.dirname(self.song.location_correct), exist_ok=True)
        shutil.move(self.song.location_local, self.song.location_correct)
        self.song.location_local = self.song.location_correct
        # Update specific item in query tuple - wait, tuples are immutable from fetchall? 
        # Usually pyodbc returns tuples. We need to handle this. For now assuming list or mutable.
        # Actually fetchall usually returns rows which might be tuples.
        # If it throws error we will need to convert query to list of lists.
        # Original code did: song_query[position][20] = ... which implies it worked or was not tested fully.
        # Let's trust original logic for now or convert if needed.
        # Actually, let's wrap it in try-except or convert row to list to be safe if it matters.
        # But for now strict port.
        try:
             self.song_query[self.position][20] = self.song.location_correct
        except TypeError:
             # Tuples are immutable
             temp_list = list(self.song_query[self.position])
             temp_list[20] = self.song.location_correct
             self.song_query[self.position] = tuple(temp_list)

    def _gather_data_from_ui(self):
        """Extracts data from UI widgets and updates self.song/self.id3 objects."""
        # Common fields
        fields = ["title", "album", "composer", "publisher", "isrc", "genres_all"]
        for field in fields:
            # Map 'genres_all' to 'genre' widget
            widget_key = "genre" if field == "genres_all" else field
            
            val = self.texts_db[widget_key].get("1.0", END).strip()
            setattr(self.song, field, val)
            
            val_id3 = self.texts_id3[widget_key].get("1.0", END).strip()
            setattr(self.id3, field, val_id3)
            
        self.id3.artist = self.texts_id3["artist"].get("1.0", END).strip()

        # Year handling
        try:
            self.song.year = int(self.texts_db["year"].get("1.0", END).strip())
        except ValueError:
            self.song.year = 0
            
        try:
            self.id3.year = int(self.texts_id3["year"].get("1.0", END).strip())
        except ValueError:
            self.id3.year = 0

        # Derived fields
        self.song.decade = calc_decade(self.song.year)
        self.song.genre_04_name = self.song.decade
        if self.song.year != 0:
            self.song.genre_04_id = self.reverse_decade_map.get(self.song.decade, 0)

    def save_song(self, rename):
        self._gather_data_from_ui()

        # Validation functions inside save_song to access self easily
        def is_valid_attribute(value):
            return value is not None and value != ""

        def check_all():
            attributes = ['artist', 'title', 'album', 'year', 'composer', 'publisher']
            for attr in attributes:
                if not is_valid_attribute(getattr(self.song, attr)):
                    messagebox.showwarning("Warning", f"'{attr}' not set!")
                    return False
                # Original code logic: compare song vs id3
                val_song = getattr(self.song, attr)
                val_id3 = getattr(self.id3, attr)
                # Ensure types match for comparison
                if str(val_song) != str(val_id3):
                    messagebox.showwarning("Warning", f"'{attr}' not the same!")
                    return False
                if not self.song.isrc == self.id3.isrc:
                    return False
            return True

        field_check = check_all()
        year_check = True
        if self.song.year == 0:
            messagebox.showwarning("Warning", "Year not set!")
            year_check = False

        genre_id_check = True
        genre_ids = self.song.genres_all.split(", ")
        genre_ids = list(dict.fromkeys(genre_ids))
        print(genre_ids)
        
        self.texts_db["genre"].delete(1.0, END)
        self.song.genres_all = list_to_string(self.genre_map[0], genre_ids)
        self.texts_db["genre"].insert(1.0, self.song.genres_all)
        
        genre_ids = genre_ids[:3]
        for genre_id in genre_ids:
            if genre_id not in self.genre_map.values():
                messagebox.showwarning("Warning", f"Genre '{genre_id}' not found!")
                genre_id_check = False
                break
                
        genre_test = check_genre(self.song.genres_all, self.id3.genres_all)
        if not genre_test:
            messagebox.showwarning("Warning", "Genres not the same!")
            
        genre_id_check = genre_id_check and genre_test
        
        if genre_id_check:
            self.song.genre_01_name = genre_ids[0]
            self.song.genre_01_id = get_genre_id(genre_ids[0], self.reverse_genre_map)
            
            if len(genre_ids) > 1:
                self.song.genre_02_name = genre_ids[1]
                self.song.genre_02_id = get_genre_id(genre_ids[1], self.reverse_genre_map)
            else:
                self.song.genre_02_name = self.genre_map[0]
                self.song.genre_02_id = 0
                
            if len(genre_ids) > 2:
                self.song.genre_03_name = genre_ids[2]
                self.song.genre_03_id = get_genre_id(genre_ids[2], self.reverse_genre_map)
            else:
                self.song.genre_03_name = self.genre_map[0]
                self.song.genre_03_id = 0

        if field_check and genre_id_check and year_check:
            update_fields_dict = {
                "fldTitle": self.song.title,
                "fldAlbum": self.song.album,
                "fldYear": self.song.year,
                "fldComposer": self.song.composer,
                "fldLabel": self.song.publisher,
                "fldCat1a": get_genre_id(self.song.genre_01_name, self.reverse_genre_map),
                "fldCat1b": get_genre_id(self.song.genre_02_name, self.reverse_genre_map),
                "fldCat1c": get_genre_id(self.song.genre_03_name, self.reverse_genre_map),
                "fldCDKey": self.song.isrc,
                "fldCat2": self.song.genre_04_id,
                "fldDuration": self.song.duration,
            }

            if rename:
                 self.song_rename()

            try:
                 self.db.update_song_fields(self.song.id, update_fields_dict)
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save changes to database:\n{e}")
                return

            tag_write(self.id3, self.song.location_local)
            
            # Check validation
            if not check_genre(self.song.genres_all, self.id3.genres_all):
                return

            # Next song
            try:
                # Re-fetch to update local state
                result = self.db.fetch_songs("AUID", self.song.id, True)
                
                if result and len(result) > 0:
                    result = result[0]
                
                try:
                    self.song_query[self.position] = result
                except TypeError:
                    pass
                    
                self.get_song(1)
                
            except IndexError:
                 pass
            except Exception as e:
                print(f"Error refreshing after save: {e}")
                
        self.update_fields()

    def get_song(self, delta):
        if delta is None:
            delta = 0
            test = self.text_jump.get(1.0, END).strip()
            print("-" + test + "-")
            try:
                self.position = int(test) - 1
            except ValueError:
                self.position = 0
                
            if self.position == -1:
                self.position = 0
        
        self.position += delta
        
        if self.position <= -1:
            self.position = 0
        if self.position >= len(self.song_query):
            self.position = len(self.song_query) - 1
            
        if self.song_query:
            self.toggle_controls(False)
            threading.Thread(target=self._load_song_thread_job, args=(self.position,), daemon=True).start()

    def _load_song_thread_job(self, pos):
        """Worker thread for loading song data."""
        try:
            data = get_data(self.song_query[pos], self.genre_map, self.decade_map, self.tempo_map)
            self.after(0, self._finish_load_song, data)
        except Exception as e:
            print(f"Error loading song: {e}")
            self.after(0, self.toggle_controls, True)

    def _finish_load_song(self, data):
        """Update UI with loaded data on main thread."""
        self.song, self.id3 = data
        self.update_fields()
        self.toggle_controls(True)

    def query_db(self):
        window_query = Toplevel(self)
        window_query.title("Database query")
        
        dropdown_field = Combobox(window_query, values=["artist", "title", "album", "composer", "publisher", "year"])
        dropdown_field.grid(row=0, column=0)
        dropdown_field.set("artist")
        
        dropdown_match = Combobox(window_query, values=["contains", "equals"])
        dropdown_match.grid(row=0, column=1)
        dropdown_match.set("contains")
        
        text_query = Text(window_query, height=1, width=50)
        text_query.grid(row=0, column=2)
        
        button_send_query = Button(window_query, text="Query",
                                   command=lambda: self.query_button_click(dropdown_field.get(), dropdown_match.get(),
                                                                      text_query.get("1.0", END).strip(), window_query))
        button_send_query.grid(row=0, column=3)
        
        window_query.bind("<Return>", lambda event: self.query_button_click(dropdown_field.get(), dropdown_match.get(),
                                                                       text_query.get("1.0", END).strip(), window_query))
        self.withdraw()

    def query_button_click(self, drop_field, drop_match, text_query, window_sent):
        self.toggle_controls(False)
        window_sent.withdraw() # Hide immediately
        threading.Thread(target=self._query_thread_job, args=(drop_field, drop_match, text_query, window_sent), daemon=True).start()

    def _query_thread_job(self, drop_field, drop_match, text_query, window_sent):
        results = self.query_execute(drop_field, drop_match, text_query)
        self.after(0, self._finish_query, results, window_sent)

    def _finish_query(self, results, window_sent):
        self.song_query = results
        if not self.song_query:
            messagebox.showinfo("Info", "No results found.")
            window_sent.destroy()
            self.deiconify()
            self.toggle_controls(True)
            return
            
        self.position = 0
        self.toggle_controls(True) 
        self.get_song(0) 
        self.deiconify()


def copy_text(text_1, text_2, end):
    text_2.delete(1.0, end)
    text_2.insert(end, text_1.get("1.0", end))
    text_1.config(bg="white")
    text_2.config(bg="white")


def process_string_comparison(val1: Any, val2: Any) -> Tuple[str, str, str]:
    """
    Cleans up two values and determines if they match.
    Returns: (clean_val1, clean_val2, bg_color_name)
    """
    if val1 == "-" or val1 is None:
        val1 = ""
    if val2 == "-" or val2 is None:
        val2 = ""
    
    val1 = str(val1)
    val2 = str(val2)
    
    bg_color = "white"
    if val1 == "" or val1 != val2:
        bg_color = "light salmon"
        
    return val1, val2, bg_color


def _clean_lookup_string(song):
    s = song.artist + " " + song.title
    s = s.replace(" ", "%20")
    s = s.replace("-", "").replace("&", "").replace("#", "").replace("\\", "")
    return s

def discogs_lookup(song):
    query = _clean_lookup_string(song)
    webbrowser.open("https://www.discogs.com/search?q=" + query)


def google_lookup(song):
    query = _clean_lookup_string(song)
    webbrowser.open("https://duckduckgo.com/?q=" + query)


if __name__ == "__main__":
    app = JazlerEditor()
    app.mainloop()
