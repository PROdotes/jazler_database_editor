# Project Structure

## src/core/config.py
**class Config**
- `__init__(self)`: Initializes configuration, loading from `config.json` in project root.
- `save_last_query(self, field, match, value)`: Saves the most recent search query parameters to config.
- `load_last_query(self) -> Optional[Dict]`: Retrieves the last saved search query parameters.
- `set_db_mode(self, use_live: bool) -> str`: Returns the active database path based on the mode.
- *Properties*: `db_path_live`, `db_path_test`, `drive_map`, `genre_rules`.

## src/core/database.py
**class Database**
- `__init__(self, db_path, table_name)`: Initializes the database connection settings.
- `_get_connection(self)`: Establishes and returns a connection to the Microsoft Access database.
- `_fetch(self, query, params=None)`: Executes a SELECT query and returns all results.
- `_execute(self, query, params=None)`: Executes an UPDATE or DELETE query and commits changes.
- `generate_genre_map(self)`: Creates a dictionary mapping genre IDs to genre names.
- `generate_decade_map(self)`: Creates a dictionary mapping decade IDs to decade names.
- `generate_tempo_map(self)`: Creates a dictionary mapping tempo IDs to tempo names.
- `update_song_filename(self, song_id, new_filename)`: Updates the file path for a specific song in the database.
- `update_song_fields(self, song_id, fields)`: Updates multiple fields (metadata) for a specific song.
- `delete_song(self, song_id)`: Removes a song entry from the database.
- `fetch_songs(self, field, value, exact_match)`: Searches for songs matching specific criteria.
- `fetch_all_songs(self)`: Retrieves all song entries from the database.

## src/utils/audio.py
**class AudioMetadata**
- `song_length(path: str) -> Optional[float]`: (Static) Calculates duration of an MP3 file in seconds.
- `get_tag(path: str) -> MP3`: (Static) Reads ID3 tags from an MP3 file.
- `tag_write(id3_data: 'SongID3', location: str) -> None`: (Static) Writes updated metadata to MP3 ID3 tags.

## src/models/song.py
**class Song**
- `__init__(self, input_data, genres, decades, tempos)`: Parses raw database tuple into a structured Song object.
- `from_db_record(cls, database_entry, genre_map, decade_map, tempo_map) -> Tuple`: (Class Method) Factory to create populated Song and SongID3 objects.
- `get_expected_path(self) -> str`: Generates the expected file path based on song metadata and rules.
- `list_to_string(genre0: str, strings: List[str]) -> str`: (Static) Converts a list of genre strings into a comma-separated string.
- `calc_decade(year: Any) -> str`: (Static) Calculates the decade string (e.g., "1990's") from a year.
- `get_genre_id(genre: str, reverse_genre_map: Dict[str, int]) -> int`: (Static) Looks up the ID for a given genre name.
- `check_genre(database_genre: str, id3_genre: str) -> bool`: (Static) Verifies if database genres match those in ID3 tags.

**class SongID3**
- `__init__(self, artist, title, composer, album, year, genres, publisher, isrc, duration, error)`: Storage class for ID3 tag data.

## src/ui/app.py
**class JazlerEditor(Tk)**
- `__init__(self)`: Initializes the main application, database connection, and UI.
- `ask_database_mode(self)`: Prompts user to select between Live or Test database.
- `connect_database(self)`: Connects to the selected database backend.
- `setup_ui(self)`: Builds the graphical user interface components.
- `toggle_controls(self, state="normal")`: Enables/disables UI buttons to prevent race conditions during operations.
- `query_execute(self, field_in, match, query)`: Performs a database search and maps UI field names to DB columns.
- `get_initial_query(self)`: Loads the last used query or fetches all songs on startup.
- `update_fields(self)`: Populates UI inputs with data from the current Song and ID3 objects.
- `_update_text_field(self, field, val_song, val_id3)`: Helper to update a single pair of DB/ID3 input fields with color coding.
- `_update_status_indicators(self)`: Updates status labels (genre match, file exists, etc.) based on current data.
- `song_rename(self)`: Moves the physical file and updates the filename in the database.
- `_gather_data_from_ui(self)`: Scrapes current values from input fields into the Song/ID3 objects.
- `save_song(self, rename)`: Orchestrates validating, saving to DB, writing ID3 tags, and optionally renaming.
- `get_song(self, delta)`: Navigates to the next/prev song or jumps to a specific index.
- `_load_song_thread_job(self, pos)`: Background thread worker to load song data.
- `_finish_load_song(self, data)`: Main thread callback to update UI after loading song key data.
- `query_db(self)`: Opens the search/query popup window.
- `query_button_click(self, drop_field, drop_match, text_query, window_sent)`: Handles search submission from the query window.
- `_query_thread_job(self, drop_field, drop_match, text_query, window_sent)`: Background thread worker for executing search queries.
- `_finish_query(self, results, window_sent)`: Main thread callback to handle search results and refresh UI.

**class WebSearch**
- `_clean_lookup_string(song)`: (Static) Formats artist/title for web search URLs.
- `discogs_lookup(song)`: (Static) Opens browser search for the song on Discogs.
- `google_lookup(song)`: (Static) Opens browser search for the song on DuckDuckGo.

**Functions**
- `copy_text(text_1, text_2, end)`: Copies text from one entry widget to another (arrow button action).
- `process_string_comparison(val1, val2) -> Tuple`: Compares two strings and determines background color.

## run.py
- Refactored entry point: Imports `JazlerEditor` and starts `mainloop`.
