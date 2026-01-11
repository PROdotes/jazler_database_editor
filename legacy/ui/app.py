import shutil
import sys
import threading
import webbrowser
from typing import Any, Tuple
from os import makedirs
from os import path
from tkinter import Tk, Toplevel, Label, Button, Entry, END, ttk, Frame
from tkinter.ttk import Combobox

# Updated Imports for New Structure
from src.models.song import Song, SongID3
from src.models.field_definition import field_registry
from src.utils.audio import AudioMetadata
from src.core.database import Database
from src.core.config import app_config
from src.ui.theme import theme
from src.utils.error_handler import ErrorHandler
from src.validators.song_validator import SongValidator


class DatabaseEditor(Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide the main window immediately
        
        # Determine database
        self.use_live = self.ask_database_mode()
        self.file = app_config.set_db_mode(self.use_live)
        self.table_name = 'snDatabase'
        self.db = self.connect_database()

        # Enforce Registry Correctness
        # This ensures we never forget to add a field to the registry
        expected_fields = {"artist", "title", "album", "composer", "publisher", 
                          "year", "decade", "genre", "isrc", "duration"}
        actual_fields = set(field_registry.names)
        
        if expected_fields != actual_fields:
            missing = expected_fields - actual_fields
            extra = actual_fields - expected_fields
            error_msg = []
            if missing:
                error_msg.append(f"Missing fields: {missing}")
            if extra:
                error_msg.append(f"Extra fields: {extra}")
            
            # Crash loudly so we can't ignore it
            full_msg = "Field Registry Error! " + "; ".join(error_msg)
            ErrorHandler.show_critical(full_msg)
            raise ValueError(full_msg)

        # Data Maps
        self.genre_map = self.db.generate_genre_map()
        self.reverse_genre_map = {v: k for k, v in self.genre_map.items()}
        self.decade_map = self.db.generate_decade_map()
        self.reverse_decade_map = {v: k for k, v in self.decade_map.items()}
        self.tempo_map = self.db.generate_tempo_map()
        
        # Validator
        self.validator = SongValidator(self.genre_map)

        # State Variables
        self.song = None
        self.id3 = None
        self.song_query = self.get_initial_query()
        # Load saved position
        last_query_data = app_config.load_last_query()
        if last_query_data and "position" in last_query_data:
            try:
                saved_pos = int(last_query_data["position"])
                # Clamp position to valid range
                if saved_pos < 0:
                    self.position = 0
                elif saved_pos >= len(self.song_query):
                    # If saved position is beyond current query, go to last song
                    self.position = max(0, len(self.song_query) - 1)
                else:
                    self.position = saved_pos
            except (ValueError, TypeError) as e:
                ErrorHandler.log_silent(e, "Loading last position")
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
            # Load song at saved position (or 0 if no saved position)
            self.get_song(0)  # Delta of 0 means stay at current position
        else:
            ErrorHandler.show_info("No songs found for initial query.")

    def ask_database_mode(self):
        """Ask user which database to use. Defaults to Test (safer option)."""
        start_root = Toplevel()
        start_root.withdraw()
        start_root.title("Select Database")
        start_root.configure(bg=theme.BG_DARK)
        start_root.resizable(False, False)
        
        # Center the window
        window_width = 400
        window_height = 180
        screen_width = start_root.winfo_screenwidth()
        screen_height = start_root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        start_root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        result = {"use_live": False}  # Default to Test database
        
        def select_live():
            result["use_live"] = True
            start_root.destroy()
        
        def select_test():
            result["use_live"] = False
            start_root.destroy()
        
        # Message
        msg_frame = Frame(start_root, bg=theme.BG_DARK, pady=20)
        msg_frame.pack(fill="both", expand=True)
        
        Label(msg_frame, text="Select Database Mode", 
              bg=theme.BG_DARK, fg=theme.FG_WHITE, 
              font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
        
        Label(msg_frame, text="Which database do you want to use?", 
              bg=theme.BG_DARK, fg=theme.FG_LIGHT_GRAY, 
              font=("Segoe UI", 9)).pack(pady=5)
        
        # Buttons
        btn_frame = Frame(start_root, bg=theme.BG_DARK, pady=10)
        btn_frame.pack(fill="x")
        
        # Test button (default - left position, will be focused)
        btn_test = Button(btn_frame, text="Test Database\n(Databases - Copy)", 
                         command=select_test, width=18, height=3,
                         bg=theme.STATUS_SUCCESS, fg=theme.FG_WHITE, font=("Segoe UI", 10, "bold"),
                         relief="raised", bd=3, cursor="hand2")
        btn_test.pack(side="left", padx=(40, 10))
        
        # Live button (right position)
        btn_live = Button(btn_frame, text="⚠️ LIVE Database ⚠️\n(Databases)", 
                         command=select_live, width=18, height=3,
                         bg=theme.STATUS_DANGER, fg=theme.FG_WHITE, font=("Segoe UI", 10, "bold"),
                         relief="raised", bd=3, cursor="hand2")
        btn_live.pack(side="left", padx=(10, 40))
        
        # Make window modal and on top
        start_root.deiconify()
        start_root.attributes('-topmost', True)
        start_root.focus_force()
        btn_test.focus_set()  # Focus on Test button (default)
        
        # Bind Enter to Test (default) and handle window close
        start_root.bind("<Return>", lambda e: select_test())
        start_root.bind("<Escape>", lambda e: select_test())
        start_root.protocol("WM_DELETE_WINDOW", select_test)
        
        start_root.wait_window()
        return result["use_live"]

    def connect_database(self):
        try:
            return Database(self.file, self.table_name)
        except Exception as e:
            root = Tk()
            root.withdraw()
            ErrorHandler.show_critical(f"Could not connect to Database at:\n{self.file}\n\nError: {e}")
            sys.exit(1)

    def on_closing(self):
        try:
            app_config.save_last_position(self.position)
        except Exception as e:
            ErrorHandler.log_silent(e, "Saving app state")
        self.destroy()

    def setup_ui(self):
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.title(f"Database Editor - [{'LIVE' if self.use_live else 'TEST'}]")
        self.config(bg=theme.BG_DARK)

        # Styles (Dark Mode)
        style = ttk.Style()
        try:
             style.theme_use('clam')
        except Exception as e:
             ErrorHandler.log_silent(e, "Setting theme 'clam'")
             pass  # Theme not available, use default 
        
        # Configure Dark Theme Colors
        BG_DARK = theme.BG_DARK
        BG_LIGHTER = theme.BG_LIGHTER
        FG_WHITE = theme.FG_WHITE
        
        style.configure("TFrame", background=BG_DARK)
        style.configure("TLabel", background=BG_DARK, foreground=FG_WHITE)
        style.configure("Bold.TLabel", background=BG_DARK, foreground=FG_WHITE, font=("Segoe UI", 9, "bold"))
        
        style.configure("TButton", background=BG_LIGHTER, foreground=FG_WHITE, borderwidth=1, focuscolor=BG_DARK)
        style.map("TButton", background=[("active", theme.BTN_ACTIVE), ("disabled", theme.BTN_DISABLED)])

        # Main Container
        main_frame = Frame(self, bg=BG_DARK)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Status Bar
        status_text = "⚠️ CAUTION: LIVE DATABASE ⚠️" if self.use_live else "SAFE MODE: Test Database"
        status_bg = theme.STATUS_DANGER if self.use_live else theme.STATUS_SUCCESS
        
        lbl_status = Label(main_frame, text=status_text, bg=status_bg, fg=theme.FG_WHITE, 
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

        # Get fields from registry
        fields = field_registry.names
        row_count = 2
        
        for field in fields:
            # Get field definition from registry
            field_def = field_registry.get(field)
            f_name = field_def.display_name if field_def else field.capitalize()
            
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
            if field_def and field_def.db_editable:  # Only show <- button if DB side is editable
                self.buttons_id3[field].pack(side="left")
                self.buttons_id3[field].bind("<Button-1>", lambda event, f=field: copy_text(self.texts_id3[f], self.texts_db[f], END))

            # ID3 Entry (Dark Input)
            self.texts_id3[field] = Entry(main_frame, relief="solid", bd=1, font=("Segoe UI", 10),
                                         bg=BG_LIGHTER, fg=FG_WHITE, insertbackground="white")
            self.texts_id3[field].grid(row=row_count, column=3, sticky="ew", pady=2)

            # Disabled styling using registry
            if field_def and field_def.is_disabled:
                 self.texts_db[field].config(state="disabled", disabledbackground=theme.BG_DISABLED, disabledforeground=theme.FG_MEDIUM_GRAY)
                 if field_def.id3_editable:  # Only disable ID3 side if it's also not editable
                     pass  # ID3 side stays enabled
                 else:
                     self.texts_id3[field].config(state="disabled", disabledbackground=theme.BG_DISABLED, disabledforeground=theme.FG_MEDIUM_GRAY)

            row_count += 1

        # Status Label for Done (Added to ID3 column)
        self.lbl_done_status = Label(main_frame, text="[ NOT DONE ]", bg=BG_DARK, fg=theme.FG_MEDIUM_GRAY, font=("Segoe UI", 10, "bold"))
        self.lbl_done_status.grid(row=row_count, column=3, sticky="w", padx=2, pady=5)

        # 4. Control Bar
        control_frame = Frame(self, bg=theme.BG_CONTROL_BAR, pady=10, padx=20) # Slightly darker for visual anchor
        control_frame.pack(fill="x", side="bottom")

        # Left: Lookup
        self.button_query = ttk.Button(control_frame, text="Query (F1)", command=self.query_db)
        self.button_query.pack(side="left", padx=2)
        
        self.button_google = ttk.Button(control_frame, text="Google (F3)", command=lambda: WebSearch.google_lookup(self.song))
        self.button_google.pack(side="left", padx=2)
        
        self.button_discog = ttk.Button(control_frame, text="Discogs (F4)", command=lambda: WebSearch.discogs_lookup(self.song))
        self.button_discog.pack(side="left", padx=2)

        # Center: Navigation
        nav_frame = Frame(control_frame, bg=theme.BG_CONTROL_BAR)
        nav_frame.pack(side="left", padx=40)
        
        self.button_jump = ttk.Button(nav_frame, text="Jump (F11)", width=6, command=lambda: self.get_song(None))
        self.button_jump.pack(side="left", padx=5)
        
        self.text_jump = Entry(nav_frame, width=5, justify="center", relief="solid", bd=1, 
                              bg=BG_LIGHTER, fg=FG_WHITE, insertbackground="white")
        self.text_jump.insert(0, "1")
        self.text_jump.pack(side="left", padx=5)
        
        self.label_counter = Label(nav_frame, text="0/0", bg=theme.BG_CONTROL_BAR, fg=theme.FG_WHITE, font=("Segoe UI", 9))
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
        
        # Error badge (clickable)
        self.error_badge = Label(footer_frame, text="0 Errors", bg=BG_DARK, 
                                fg=theme.FG_MEDIUM_GRAY, font=("Segoe UI", 9, "underline"), 
                                cursor="hand2", padx=10, relief="ridge", bd=1)
        self.error_badge.pack(side="right", padx=5)
        self.error_badge.bind("<Button-1>", lambda e: self.show_error_log())
        
        # Hover effect for error badge
        def on_enter(e):
            self.error_badge.config(relief="raised")
        def on_leave(e):
            self.error_badge.config(relief="ridge")
        self.error_badge.bind("<Enter>", on_enter)
        self.error_badge.bind("<Leave>", on_leave)
        
        # Set up ErrorHandler callback to update badge
        ErrorHandler.set_error_callback(self.update_error_badge)

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
            except Exception as e:
                ErrorHandler.log_silent(e, "Updating button state")
                pass  # Button state change failed, continue

    def query_execute(self, field_in, match, query, save=True):
        if save:
            app_config.save_last_query(field_in, match, query)
        
        # Use field registry for mapping
        field_def = field_registry.get(field_in)
        if field_def and field_def.queryable:
            field_out = field_def.db_column
        else:
            # Fallback to artist if field not found or not queryable
            field_out = "fldArtistName"

        if match == "contains":
            return self.db.fetch_songs(field_out, query, False)
        elif match == "equals":
            return self.db.fetch_songs(field_out, query, True)
        return []

    def get_initial_query(self):
        last_query = app_config.load_last_query()
        if last_query:
            try:
                ErrorHandler.log_info(f"Loading last query: {last_query}")
                return self.query_execute(last_query["field"], last_query["match"], last_query["value"], save=False)
            except Exception as e:
                ErrorHandler.log_silent(e, "Restoring last query")
                
        ErrorHandler.show_info("No previous query found.\nLoading first 2000 songs to save memory.")
        return self.db.fetch_all_songs()

    def update_fields(self):
        if self.id3 is None:
            choice = ErrorHandler.ask_yes_no("No song selected! Delete database entry?", "Error")
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
        
        # Update editable fields from registry
        for field_def in field_registry.editable():
            if field_def.name == "artist":
                continue  # Already handled above
            val_song = getattr(self.song, field_def.song_attr)
            val_id3 = getattr(self.id3, field_def.song_attr)
            self._update_text_field(field_def.name, val_song, val_id3)

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
             self.lbl_done_status.config(text="✔ DONE", fg=theme.STATUS_SUCCESS)
        else:
             self.lbl_done_status.config(text="[ NOT DONE ]", fg=theme.FG_MEDIUM_GRAY)

        self._update_status_indicators()

    def _update_text_field(self, field, val_song, val_id3):
        txt_db = self.texts_db[field]
        txt_id3 = self.texts_id3[field]
        
        # Determine if field is optional using registry
        field_def = field_registry.get(field)
        is_required = field_def.required if field_def else True
        
        # Special handling for artist field (database has limited length)
        is_artist = field == "artist"
            
        val1, val2, color = process_string_comparison(val_song, val_id3, required=is_required, is_artist=is_artist)
        
        txt_db.delete(0, END)
        txt_db.insert(0, val1)
        txt_db.config(bg=color)
        
        txt_id3.delete(0, END)
        txt_id3.insert(0, val2)
        txt_id3.config(bg=color)

    def _update_status_indicators(self):
        # Genre Validation
        test_genre = Song.check_genre(self.song.genres_all, self.id3.genres_all)
        bg_genre = theme.BG_LIGHTER if test_genre else theme.STATUS_ERROR_BG
        self.texts_db["genre"].config(bg=bg_genre)
        self.texts_id3["genre"].config(bg=bg_genre)
        
        if test_genre:
             self.lbl_stat_genre.config(text="✔ Genres Match", fg=theme.STATUS_SUCCESS)
        else:
             self.lbl_stat_genre.config(text="⚠️ Genre Mismatch", fg=theme.STATUS_WARNING)
            
        # ISRC Validation
        isrc_match = str(self.song.isrc) == str(self.id3.isrc)
        
        # Override BG for empty ISRC to be normal (not error)
        if not self.song.isrc and not self.id3.isrc:
            self.texts_db["isrc"].config(bg=theme.BG_LIGHTER)
            self.texts_id3["isrc"].config(bg=theme.BG_LIGHTER)
            
        if isrc_match:
             self.lbl_stat_isrc.config(text="✔ ISRC Match", fg=theme.STATUS_SUCCESS)
        else:
             self.lbl_stat_isrc.config(text="⚠️ ISRC Mismatch", fg=theme.STATUS_WARNING)
            
        # Count & File Status
        self.label_counter.config(text=f"{self.position + 1}/{len(self.song_query)}")
        
        err = self.id3.error
        if err == "No error":
            self.lbl_stat_file.config(text="✔ File OK", fg=theme.STATUS_SUCCESS)
        else:
            self.lbl_stat_file.config(text=f"❌ {err}", fg=theme.STATUS_DANGER)
            
        self.text_jump.delete(0, END)
        self.text_jump.insert(0, str(self.position + 1))
        
        # File Validation
        clean_loc = (self.song.location_local + "    <--->    " + self.song.location_correct).replace("z:\\songs\\", "")
        self.label_filename.config(text=clean_loc)
        
        bg_file = theme.STATUS_SUCCESS if self.song.location_local.lower() == self.song.location_correct.lower() else theme.STATUS_DANGER
        self.label_filename.config(bg=bg_file)

    def song_rename(self):
        # 0. Prepare paths
        location_db = self.song.location_correct.replace("z:", "b:")
        old_location_db = self.song.location_local.replace("z:", "b:")
        
        try:
            # 1. Update Database First
            # If this fails, file stays where it is. Safe.
            self.db.update_song_filename(self.song.id, location_db)
            
            # 2. Prepare destination directory
            if not path.exists(self.song.location_correct):
                makedirs(path.dirname(self.song.location_correct), exist_ok=True)
            
            # 3. Move File
            shutil.move(self.song.location_local, self.song.location_correct)
            
            # 4. Update in-memory state
            self.song.location_local = self.song.location_correct
            
            # Update cache tuple (handling immutability)
            try:
                 self.song_query[self.position][20] = self.song.location_correct
            except TypeError:
                 temp_list = list(self.song_query[self.position])
                 temp_list[20] = self.song.location_correct
                 self.song_query[self.position] = tuple(temp_list)

            # 5. Success Notification
            self.update_fields()
            ErrorHandler.log_info(f"Renamed song {self.song.id}")
            ErrorHandler.show_info("File renamed successfully!")

        except (OSError, PermissionError, shutil.Error) as e:
            # File Move Failed!
            # ROLLBACK Database
            try:
                self.db.update_song_filename(self.song.id, old_location_db)
                ErrorHandler.log_info("Database rolled back after failed file move.")
            except Exception as rollback_error:
                # Fatal! Database thinks file is moved, but it isn't.
                ErrorHandler.show_critical(
                    "CRITICAL ERROR: Data Corruption!",
                    f"File move failed AND rollback failed!\n\nFile is at: {self.song.location_local}\nDB thinks it is at: {self.song.location_correct}\n\nError: {rollback_error}"
                )
                return

            ErrorHandler.show_error(
                "File Rename Failed",
                f"Could not move file.\nDatabase change reverted.\n\nError: {e}"
            )
            
        except Exception as e:
            # Generic error (DB failure or other)
            ErrorHandler.show_error("Rename Error", f"An unexpected error occurred:\n{e}")


    def _gather_data_from_ui(self):
        """Extracts data from UI widgets and updates self.song/self.id3 objects."""
        # Gather editable fields from registry
        for field_def in field_registry.editable():
            if field_def.name == "artist":
                continue  # Artist handled separately below
            if field_def.name == "year":
                continue  # Year handled separately below
            
            val = self.texts_db[field_def.name].get().strip()
            setattr(self.song, field_def.song_attr, val)
            
            val_id3 = self.texts_id3[field_def.name].get().strip()
            setattr(self.id3, field_def.song_attr, val_id3)
            
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

        # Normalization
        self.song.normalize_genres(self.genre_map[0])
        # Update UI to reflect normalized genres
        self.texts_db["genre"].delete(0, END)
        self.texts_db["genre"].insert(0, self.song.genres_all)
        
        # Update internal IDs based on genres (needed for path validation and DB update)
        self.song.update_genre_ids(self.reverse_genre_map, self.genre_map[0])

        # Validation
        validation_result = self.validator.validate(self.song, self.id3)
        
        if not validation_result.is_valid:
            if validation_result.issues:
                # Show the blocking error (first one found)
                ErrorHandler.show_warning(validation_result.issues[0].message)
            return

        if True: # Validation Passed
            # Build update dict from registry - prevents typos in column names
            update_fields_dict = {
                "fldTitle": self.song.title,
                "fldAlbum": self.song.album,
                "fldYear": self.song.year,
                "fldComposer": self.song.composer,
                "fldLabel": self.song.publisher,
                "fldCDKey": self.song.isrc,
                "fldDuration": self.song.duration,
                # Genre fields require special handling
                "fldCat1a": Song.get_genre_id(self.song.genre_01_name, self.reverse_genre_map),
                "fldCat1b": Song.get_genre_id(self.song.genre_02_name, self.reverse_genre_map),
                "fldCat1c": Song.get_genre_id(self.song.genre_03_name, self.reverse_genre_map),
                "fldCat2": self.song.genre_04_id,
            }

            if rename:
                 self.song_rename()

            # Config Rules / Folder Validation - Handled by SongValidator


            try:
                 self.db.update_song_fields(self.song.id, update_fields_dict)
            except Exception as e:
                ErrorHandler.show_error(f"Could not save changes to database:\n{e}")
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
                ErrorHandler.log_silent(e, "Refreshing song list")

        self.update_fields()

    def get_song(self, delta):
        if self.is_loading:
            return

        if delta is None:
            delta = 0
            test = self.text_jump.get().strip()

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
            ErrorHandler.log_silent(e, "Loading song data thread")
            self.after(0, self.toggle_controls, True)

    def _finish_load_song(self, data):
        """Update UI with loaded data on main thread."""
        try:
            self.song, self.id3 = data
            self.update_fields()
        except Exception as e:
            ErrorHandler.log_silent(e, "Updating UI with song data")
            # messagebox.showerror("UI Error", str(e)) # Optional
        finally:
            self.toggle_controls(True)

    def query_db(self):
        window_query = Toplevel(self)
        window_query.title("Database query")
        window_query.config(bg=theme.BG_DARK)
        
        # Get queryable fields from registry
        queryable_fields = [f.name for f in field_registry.queryable()]
        dropdown_field = Combobox(window_query, values=queryable_fields)
        dropdown_field.grid(row=0, column=0, padx=5, pady=10)
        dropdown_field.set("artist")
        
        dropdown_match = Combobox(window_query, values=["contains", "equals"])
        dropdown_match.grid(row=0, column=1, padx=5, pady=10)
        dropdown_match.set("contains")
        
        text_query = Entry(window_query, width=50, bg=theme.BG_LIGHTER, fg=theme.FG_WHITE, insertbackground=theme.FG_WHITE)
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
            ErrorHandler.show_info("No results found.")
            window_sent.destroy()
            self.deiconify()
            self.toggle_controls(True)
            return

        # Check if result was capped (limit is 2000 in database.py)
        if len(self.song_query) >= 2000:
             ErrorHandler.show_info("Query Result Capped\n\nShowing first 2000 records to save memory.\nPlease refine your search criteria if you need specific records.")
            
        self.position = 0
        self.toggle_controls(True) 
        self.get_song(0) 
        self.deiconify()
    
    def update_error_badge(self, count, color):
        """Update error badge when errors occur."""
        if count == 0:
            self.error_badge.config(
                text="0 Errors",
                bg=theme.BG_DARK,
                fg=theme.FG_MEDIUM_GRAY
            )
        else:
            badge_bg = theme.STATUS_DANGER if color == "red" else theme.STATUS_WARNING
            self.error_badge.config(
                text=f"⚠ {count} Error{'s' if count != 1 else ''}",
                bg=badge_bg,
                fg=theme.FG_WHITE
            )
    
    def show_error_log(self):
        """Show error log viewer dialog."""
        try:
            from src.ui.dialogs.error_log_viewer import ErrorLogViewer
            ErrorLogViewer(self).show()
            ErrorHandler.clear_error_count()
        except Exception as e:
            ErrorHandler.show_error(f"Failed to open error log:\n{e}")
            # print(f"Error log launch failed: {e}")


def copy_text(text_1, text_2, end):
    text_2.delete(0, end)
    text_2.insert(0, text_1.get())
    text_1.config(bg=theme.BG_LIGHTER)
    text_2.config(bg=theme.BG_LIGHTER)


def process_string_comparison(val1: Any, val2: Any, required: bool = True, is_artist: bool = False) -> Tuple[str, str, str]:
    """
    Cleans up two values and determines if they match.
    For artist field, checks if ID3 tag (val2) starts with database value (val1).
    Returns: (clean_val1, clean_val2, bg_color_name)
    """
    if val1 == "-" or val1 is None:
        val1 = ""
    if val2 == "-" or val2 is None:
        val2 = ""
    
    val1 = str(val1)
    val2 = str(val2)
    
    bg_color = theme.BG_LIGHTER # Dark Input BG
    
    # Special handling for artist field - check if ID3 starts with DB value
    if is_artist:
        if val1 and not val2.startswith(val1):
            bg_color = theme.STATUS_ERROR_BG # Mismatch
        elif required and val1 == "":
            bg_color = theme.STATUS_ERROR_BG # Required but empty
    else:
        # Standard exact match comparison
        if val1 != val2:
            bg_color = theme.STATUS_ERROR_BG # Mismatch
        elif required and val1 == "":
            bg_color = theme.STATUS_ERROR_BG # Required but empty
        
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
