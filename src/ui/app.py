import shutil
import sys
import threading
import webbrowser
from typing import Any, Tuple
from os import makedirs
from os import path
from tkinter import Tk, Toplevel, Label, Button, Entry, END, messagebox, ttk, Frame, Checkbutton, BooleanVar
from tkinter.ttk import Combobox

# Updated Imports for New Structure
from src.models.song import Song, SongID3
from src.utils.audio import AudioMetadata
from src.core.database import Database
from src.core.config import app_config


class JazlerEditor(Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide the main window immediately
        
        # Determine database
        self.use_live = self.ask_database_mode()
        self.file = app_config.set_db_mode(self.use_live)
        self.table_name = 'snDatabase'
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
        # Load saved position
        last_query_data = app_config.load_last_query()
        if last_query_data and "position" in last_query_data:
            try:
                saved_pos = int(last_query_data["position"])
                if 0 <= saved_pos < len(self.song_query):
                    self.position = saved_pos
            except ValueError:
                self.position = 0
        else:
            self.position = 0

        self.is_loading = False
        
        # Handle Window Close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # UI Initialization
        self.setup_ui()
        
        # Load first song
        if self.song_query:
            self.get_song(0)
        else:
            messagebox.showinfo("Info", "No songs found for initial query.")

    def ask_database_mode(self):
        start_root = Tk()
        start_root.withdraw()
        start_root.attributes('-topmost', True)
        use_live = messagebox.askyesno(
            "Select Database", 
            "Do you want to use the LIVE database?\n\nYES: Live (Databases)\nNO: Test (Databases - Copy)", 
            parent=start_root
        )
        start_root.destroy()
        return use_live

    def connect_database(self):
        try:
            return Database(self.file, self.table_name)
        except Exception as e:
            root = Tk()
            root.withdraw()
            messagebox.showerror("Connection Error", f"Could not connect to Database at:\n{self.file}\n\nError: {e}")
            sys.exit(1)

    def on_closing(self):
        try:
            app_config.save_last_position(self.position)
        except Exception as e:
            print(f"Error saving state: {e}")
        self.destroy()

    def setup_ui(self):
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.title(f"Jazler Editor - [{'LIVE' if self.use_live else 'TEST'}]")
        self.config(bg="#2b2b2b")

        # Styles (Dark Mode)
        style = ttk.Style()
        try:
             style.theme_use('clam')
        except:
             pass 
        
        # Configure Dark Theme Colors
        BG_DARK = "#2b2b2b"
        BG_LIGHTER = "#3c3f41"
        FG_WHITE = "#ffffff"
        
        style.configure("TFrame", background=BG_DARK)
        style.configure("TLabel", background=BG_DARK, foreground=FG_WHITE)
        style.configure("Bold.TLabel", background=BG_DARK, foreground=FG_WHITE, font=("Segoe UI", 9, "bold"))
        
        style.configure("TButton", background=BG_LIGHTER, foreground=FG_WHITE, borderwidth=1, focuscolor=BG_DARK)
        style.map("TButton", background=[("active", "#4c5052"), ("disabled", "#555555")])

        # Main Container
        main_frame = Frame(self, bg=BG_DARK)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Status Bar
        status_text = "⚠️ CAUTION: LIVE DATABASE ⚠️" if self.use_live else "SAFE MODE: Test Database"
        status_bg = "#dc3545" if self.use_live else "#28a745"
        
        lbl_status = Label(main_frame, text=status_text, bg=status_bg, fg="white", 
                          font=("Segoe UI", 11, "bold"), pady=8)
        lbl_status.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 15))

        # 2. Field Headers
        headers = ["Field", "Database Value", "Actions", "MP3 Tag Value"]
        for i, h in enumerate(headers):
             ttk.Label(main_frame, text=h, style="Bold.TLabel").grid(row=1, column=i, pady=(0, 5))

        # 3. Fields
        self.texts_db = {}
        self.texts_id3 = {}
        self.buttons_db = {}
        self.buttons_id3 = {}
        
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(3, weight=1)
        # Balance the layout: Col 0 (Labels) ~= Col 4 (Empty Right Margin)
        main_frame.columnconfigure(0, minsize=120)
        main_frame.columnconfigure(4, minsize=120)

        fields = ["artist", "title", "album", "composer", "publisher", "year", "decade", "genre", "isrc", "duration"]
        row_count = 2
        
        for field in fields:
            # Name
            f_name = field.capitalize()
            if field == "genres_all": f_name = "Genres"
            if field == "isrc": f_name = "ISRC"
            
            ttk.Label(main_frame, text=f_name + ":", anchor="e").grid(row=row_count, column=0, sticky="e", padx=(0, 10), pady=2)

            # DB Entry (Dark Input)
            self.texts_db[field] = Entry(main_frame, relief="solid", bd=1, font=("Segoe UI", 10), 
                                        bg=BG_LIGHTER, fg=FG_WHITE, insertbackground="white")
            self.texts_db[field].grid(row=row_count, column=1, sticky="ew", pady=2)
            
            # Action Buttons
            action_frame = Frame(main_frame, bg=BG_DARK)
            action_frame.grid(row=row_count, column=2, padx=5)
            
            self.buttons_db[field] = ttk.Button(action_frame, text="->", width=3)
            self.buttons_db[field].pack(side="left")
            self.buttons_db[field].bind("<Button-1>", lambda event, f=field: copy_text(self.texts_db[f], self.texts_id3[f], END))

            self.buttons_id3[field] = ttk.Button(action_frame, text="<-", width=3)
            if field != "artist":
                self.buttons_id3[field].pack(side="left")
                self.buttons_id3[field].bind("<Button-1>", lambda event, f=field: copy_text(self.texts_id3[f], self.texts_db[f], END))

            # ID3 Entry (Dark Input)
            self.texts_id3[field] = Entry(main_frame, relief="solid", bd=1, font=("Segoe UI", 10),
                                         bg=BG_LIGHTER, fg=FG_WHITE, insertbackground="white")
            self.texts_id3[field].grid(row=row_count, column=3, sticky="ew", pady=2)

            # Disabled styling
            if field in ["decade", "duration", "artist"]:
                 self.texts_db[field].config(state="disabled", disabledbackground="#1e1e1e", disabledforeground="#6c757d")
                 if field != "artist":
                     self.texts_id3[field].config(state="disabled", disabledbackground="#1e1e1e", disabledforeground="#6c757d")

            row_count += 1

        # Status Label for Done (Added to ID3 column)
        self.lbl_done_status = Label(main_frame, text="[ NOT DONE ]", bg=BG_DARK, fg="#6c757d", font=("Segoe UI", 10, "bold"))
        self.lbl_done_status.grid(row=row_count, column=3, sticky="w", padx=2, pady=5)

        # 4. Control Bar
        control_frame = Frame(self, bg="#1e1e1e", pady=10, padx=20) # Slightly darker for visual anchor
        control_frame.pack(fill="x", side="bottom")

        # Left: Lookup
        self.button_query = ttk.Button(control_frame, text="Query (F1)", command=self.query_db)
        self.button_query.pack(side="left", padx=2)
        
        self.button_google = ttk.Button(control_frame, text="Google (F3)", command=lambda: WebSearch.google_lookup(self.song))
        self.button_google.pack(side="left", padx=2)
        
        self.button_discog = ttk.Button(control_frame, text="Discogs (F4)", command=lambda: WebSearch.discogs_lookup(self.song))
        self.button_discog.pack(side="left", padx=2)

        # Center: Navigation
        nav_frame = Frame(control_frame, bg="#1e1e1e")
        nav_frame.pack(side="left", padx=40)
        
        self.button_jump = ttk.Button(nav_frame, text="Jump (F11)", width=6, command=lambda: self.get_song(None))
        self.button_jump.pack(side="left", padx=5)
        
        self.text_jump = Entry(nav_frame, width=5, justify="center", relief="solid", bd=1, 
                              bg=BG_LIGHTER, fg=FG_WHITE, insertbackground="white")
        self.text_jump.insert(0, "1")
        self.text_jump.pack(side="left", padx=5)
        
        self.label_counter = Label(nav_frame, text="0/0", bg="#1e1e1e", fg="white", font=("Segoe UI", 9))
        self.label_counter.pack(side="left", padx=5)

        self.button_previous = ttk.Button(nav_frame, text="< Prev (F9)", width=8, command=lambda: self.get_song(-1))
        self.button_previous.pack(side="left")
        
        self.button_next = ttk.Button(nav_frame, text="Next > (F10)", width=8, command=lambda: self.get_song(1))
        self.button_next.pack(side="left")

        # Right: Save
        self.button_rename = ttk.Button(control_frame, text="Rename (F6)", command=lambda: self.save_song(True))
        self.button_rename.pack(side="right", padx=2)
        
        self.button_save = ttk.Button(control_frame, text="Save (F5)", command=lambda: self.save_song(False))
        self.button_save.pack(side="right", padx=2)
        
        # Status footer
        footer_frame = Frame(self, bg=BG_DARK, pady=5)
        footer_frame.pack(side="bottom", fill="x")
        
        # Filename Display
        self.label_filename = Label(footer_frame, text="Filename", bg=BG_DARK, fg=FG_WHITE, font=("Segoe UI", 8))
        self.label_filename.pack(side="bottom", fill="x", pady=(5, 0))

        # Status Labels
        font_status = ("Segoe UI", 10, "bold")
        self.lbl_stat_file = Label(footer_frame, text="File Status", bg=BG_DARK, fg=FG_WHITE, font=font_status)
        self.lbl_stat_file.pack(side="left", expand=True)

        self.lbl_stat_genre = Label(footer_frame, text="Genre Status", bg=BG_DARK, fg=FG_WHITE, font=font_status)
        self.lbl_stat_genre.pack(side="left", expand=True)
        
        self.lbl_stat_isrc = Label(footer_frame, text="ISRC Status", bg=BG_DARK, fg=FG_WHITE, font=font_status)
        self.lbl_stat_isrc.pack(side="left", expand=True)

        # Key Bindings
        self.bind("<F1>", lambda event: self.query_db())
        self.bind("<F3>", lambda event: WebSearch.google_lookup(self.song))
        self.bind("<F4>", lambda event: WebSearch.discogs_lookup(self.song))
        self.bind("<F5>", lambda event: self.save_song(False))
        self.bind("<F6>", lambda event: self.save_song(True))
        self.bind("<F9>", lambda event: self.get_song(-1))
        self.bind("<F10>", lambda event: self.get_song(1))
        self.bind("<F11>", lambda event: self.get_song(None))
        self.bind("<F12>", lambda event: self.text_jump.focus())

    def toggle_controls(self, state="normal"):
        """Enable or disable navigations buttons to prevent race conditions."""
        if state is True or state == "normal":
            self.is_loading = False
            state_val = ["!disabled"]
        else:
            self.is_loading = True
            state_val = ["disabled"]
            
        buttons = [
            self.button_previous, self.button_next, self.button_jump,
            self.button_query, self.button_save, self.button_rename,
            self.button_google, self.button_discog
        ]
        for btn in buttons:
            try:
                btn.state(state_val)
            except:
                pass

    def query_execute(self, field_in, match, query, save=True):
        if save:
            app_config.save_last_query(field_in, match, query)
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
        last_query = app_config.load_last_query()
        if last_query:
            try:
                print(f"Loading last query: {last_query}")
                return self.query_execute(last_query["field"], last_query["match"], last_query["value"], save=False)
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
                self.id3 = SongID3("", "", "", "", "0", "", "", "", "0", "false", "FILE NOT FOUND")

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

        # Done Status Check
        if getattr(self.id3, "done", False):
             self.lbl_done_status.config(text="✔ DONE", fg="#28a745")
        else:
             self.lbl_done_status.config(text="[ NOT DONE ]", fg="#6c757d")

        self._update_status_indicators()

    def _update_text_field(self, field, val_song, val_id3):
        txt_db = self.texts_db[field]
        txt_id3 = self.texts_id3[field]
        
        # Determine if field is optional
        optional_fields = ["album", "composer", "publisher", "isrc", "year"] 
        is_required = field not in optional_fields
            
        val1, val2, color = process_string_comparison(val_song, val_id3, required=is_required)
        
        txt_db.delete(0, END)
        txt_db.insert(0, val1)
        txt_db.config(bg=color)
        
        txt_id3.delete(0, END)
        txt_id3.insert(0, val2)
        txt_id3.config(bg=color)

    def _update_status_indicators(self):
        # Genre Validation
        test_genre = Song.check_genre(self.song.genres_all, self.id3.genres_all)
        bg_genre = "#3c3f41" if test_genre else "#662222"
        self.texts_db["genre"].config(bg=bg_genre)
        self.texts_id3["genre"].config(bg=bg_genre)
        
        if test_genre:
             self.lbl_stat_genre.config(text="✔ Genres Match", fg="#28a745")
        else:
             self.lbl_stat_genre.config(text="⚠️ Genre Mismatch", fg="#fd7e14")
            
        # ISRC Validation
        isrc_match = str(self.song.isrc) == str(self.id3.isrc)
        
        # Override BG for empty ISRC to be normal (not error)
        if not self.song.isrc and not self.id3.isrc:
            self.texts_db["isrc"].config(bg="#3c3f41")
            self.texts_id3["isrc"].config(bg="#3c3f41")
            
        if isrc_match:
             self.lbl_stat_isrc.config(text="✔ ISRC Match", fg="#28a745")
        else:
             self.lbl_stat_isrc.config(text="⚠️ ISRC Mismatch", fg="#fd7e14")
            
        # Count & File Status
        self.label_counter.config(text=f"{self.position + 1}/{len(self.song_query)}")
        
        err = self.id3.error
        if err == "No error":
            self.lbl_stat_file.config(text="✔ File OK", fg="#28a745")
        else:
            self.lbl_stat_file.config(text=f"❌ {err}", fg="#dc3545")
            
        self.text_jump.delete(0, END)
        self.text_jump.insert(0, str(self.position + 1))
        
        # File Validation
        clean_loc = (self.song.location_local + "    <--->    " + self.song.location_correct).replace("z:\\songs\\", "")
        self.label_filename.config(text=clean_loc)
        
        bg_file = "#28a745" if self.song.location_local.lower() == self.song.location_correct.lower() else "#dc3545"
        self.label_filename.config(bg=bg_file)

    def song_rename(self):
        location_db = self.song.location_correct.replace("z:", "b:")
        self.db.update_song_filename(self.song.id, location_db)
        if not path.exists(self.song.location_correct):
            makedirs(path.dirname(self.song.location_correct), exist_ok=True)
        shutil.move(self.song.location_local, self.song.location_correct)
        self.song.location_local = self.song.location_correct

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
            
            val = self.texts_db[widget_key].get().strip()
            setattr(self.song, field, val)
            
            val_id3 = self.texts_id3[widget_key].get().strip()
            setattr(self.id3, field, val_id3)
            
        self.id3.artist = self.texts_id3["artist"].get().strip()

        # Year handling
        try:
            self.song.year = int(self.texts_db["year"].get().strip())
        except ValueError:
            self.song.year = 0
            
        try:
            self.id3.year = int(self.texts_id3["year"].get().strip())
        except ValueError:
            self.id3.year = 0

        # Derived fields
        self.song.decade = Song.calc_decade(self.song.year)
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
        
        self.texts_db["genre"].delete(0, END)
        self.song.genres_all = Song.list_to_string(self.genre_map[0], genre_ids)
        self.texts_db["genre"].insert(0, self.song.genres_all)
        
        genre_ids = genre_ids[:3]
        for genre_id in genre_ids:
            if genre_id not in self.genre_map.values():
                messagebox.showwarning("Warning", f"Genre '{genre_id}' not found!")
                genre_id_check = False
                break
                
        genre_test = Song.check_genre(self.song.genres_all, self.id3.genres_all)
        if not genre_test:
            messagebox.showwarning("Warning", "Genres not the same!")
            
        genre_id_check = genre_id_check and genre_test
        
        if genre_id_check:
            self.song.genre_01_name = genre_ids[0]
            self.song.genre_01_id = Song.get_genre_id(genre_ids[0], self.reverse_genre_map)
            
            if len(genre_ids) > 1:
                self.song.genre_02_name = genre_ids[1]
                self.song.genre_02_id = Song.get_genre_id(genre_ids[1], self.reverse_genre_map)
            else:
                self.song.genre_02_name = self.genre_map[0]
                self.song.genre_02_id = 0
                
            if len(genre_ids) > 2:
                self.song.genre_03_name = genre_ids[2]
                self.song.genre_03_id = Song.get_genre_id(genre_ids[2], self.reverse_genre_map)
            else:
                self.song.genre_03_name = self.genre_map[0]
                self.song.genre_03_id = 0

        path_check = True
        if genre_id_check:
             g1 = self.song.genre_01_name.lower()
             rules = app_config.genre_rules

             is_standard = g1 in rules.get("standard_subfolder", [])
             is_special = (g1 in rules["path_overrides"] or 
                           g1 in rules["no_year_subfolder"] or 
                           g1 in rules["no_genre_subfolder"])

             if not is_standard and not is_special:
                  messagebox.showwarning("Warning", f"Genre '{self.song.genre_01_name}' is not defined in config rules!")
                  path_check = False

             is_path_correct = self.song.location_local.lower() == self.song.location_correct.lower()
             if not is_path_correct:
                 if is_standard:
                      messagebox.showwarning("Warning", f"File is in the wrong folder!\nExpected: {self.song.location_correct}")
                      path_check = False

        if field_check and genre_id_check and year_check and path_check:
            update_fields_dict = {
                "fldTitle": self.song.title,
                "fldAlbum": self.song.album,
                "fldYear": self.song.year,
                "fldComposer": self.song.composer,
                "fldLabel": self.song.publisher,
                "fldCat1a": Song.get_genre_id(self.song.genre_01_name, self.reverse_genre_map),
                "fldCat1b": Song.get_genre_id(self.song.genre_02_name, self.reverse_genre_map),
                "fldCat1c": Song.get_genre_id(self.song.genre_03_name, self.reverse_genre_map),
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

            AudioMetadata.tag_write(self.id3, self.song.location_local)
            
            # Check validation
            if not Song.check_genre(self.song.genres_all, self.id3.genres_all):
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
                
            except IndexError:
                 pass
            except Exception as e:
                print(f"Error refreshing after save: {e}")
                
        self.update_fields()

    def get_song(self, delta):
        if self.is_loading:
            return

        if delta is None:
            delta = 0
            test = self.text_jump.get().strip()
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
            data = Song.from_db_record(self.song_query[pos], self.genre_map, self.decade_map, self.tempo_map)
            self.after(0, self._finish_load_song, data)
        except Exception as e:
            print(f"Error loading song: {e}")
            self.after(0, self.toggle_controls, True)

    def _finish_load_song(self, data):
        """Update UI with loaded data on main thread."""
        try:
            self.song, self.id3 = data
            self.update_fields()
        except Exception as e:
            print(f"Error updating UI: {e}")
            # messagebox.showerror("UI Error", str(e)) # Optional
        finally:
            self.toggle_controls(True)

    def query_db(self):
        window_query = Toplevel(self)
        window_query.title("Database query")
        window_query.config(bg="#2b2b2b")
        
        dropdown_field = Combobox(window_query, values=["artist", "title", "album", "composer", "publisher", "year"])
        dropdown_field.grid(row=0, column=0, padx=5, pady=10)
        dropdown_field.set("artist")
        
        dropdown_match = Combobox(window_query, values=["contains", "equals"])
        dropdown_match.grid(row=0, column=1, padx=5, pady=10)
        dropdown_match.set("contains")
        
        text_query = Entry(window_query, width=50, bg="#3c3f41", fg="white", insertbackground="white")
        text_query.grid(row=0, column=2, padx=5, pady=10)
        text_query.focus_set()
        
        button_send_query = ttk.Button(window_query, text="Query",
                                   command=lambda: self.query_button_click(dropdown_field.get(), dropdown_match.get(),
                                                                      text_query.get().strip(), window_query))
        button_send_query.grid(row=0, column=3, padx=5, pady=10)
        
        window_query.bind("<Return>", lambda event: self.query_button_click(dropdown_field.get(), dropdown_match.get(),
                                                                       text_query.get().strip(), window_query))
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
    text_2.delete(0, end)
    text_2.insert(0, text_1.get())
    text_1.config(bg="#3c3f41")
    text_2.config(bg="#3c3f41")


def process_string_comparison(val1: Any, val2: Any, required: bool = True) -> Tuple[str, str, str]:
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
    
    bg_color = "#3c3f41" # Dark Input BG
    
    if val1 != val2:
        bg_color = "#662222" # Mismatch
    elif required and val1 == "":
        bg_color = "#662222" # Required but empty
        
    return val1, val2, bg_color


class WebSearch:
    @staticmethod
    def _clean_lookup_string(song):
        s = song.artist + " " + song.title
        s = s.replace(" ", "%20")
        s = s.replace("-", "").replace("&", "").replace("#", "").replace("\\", "")
        return s

    @staticmethod
    def discogs_lookup(song):
        query = WebSearch._clean_lookup_string(song)
        webbrowser.open("https://www.discogs.com/search?q=" + query)

    @staticmethod
    def google_lookup(song):
        query = WebSearch._clean_lookup_string(song)
        webbrowser.open("https://duckduckgo.com/?q=" + query)
