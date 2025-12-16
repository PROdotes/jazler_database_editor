# Project Structure

## config.py
**class Config**
- `__init__(self)`: Initializes configuration, loading from file or creating default.
- `save_last_query(self, field, match, value)`: Saves the most recent search query parameters to config.
- `load_last_query(self) -> Optional[Dict]`: Retrieves the last saved search query parameters.
- `set_db_mode(self, use_live: bool) -> str`: Returns the active database path based on the mode.
- *Properties*: `db_path_live`, `db_path_test`, `drive_map`, `genre_rules`.

## database.py
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

## hook-mutagen.py
*(No functions or classes)*: PyInstaller hook to include mutagen and pyodbc dependencies.

## mp3_stuff.py
**class AudioMetadata**
- `song_length(path: str) -> Optional[float]`: (Static) Calculates duration of an MP3 file in seconds.
- `get_tag(path: str) -> MP3`: (Static) Reads ID3 tags from an MP3 file.
- `tag_write(id3_data: 'SongID3', location: str) -> None`: (Static) Writes updated metadata to MP3 ID3 tags.

## Song.py
**class Song**
- `__init__(self, input_data, genres, decades, tempos)`: Parses raw database tuple into a structured Song object.
- `from_db_record(cls, database_entry, genre_map, decade_map, tempo_map) -> Tuple`: (Class Method) Factory to create populated Song and SongID3 objects.
- `get_expected_path(self) -> str`: Generates the expected file path based on song metadata and rules.
- `list_to_string(genre0: str, strings: List[str]) -> str`: (Static) Converts a list of genre strings into a comma-separated string.
- `calc_decade(year: Any) -> str`: (Static) Calculates the decade string (e.g., "1990's") from a year.
- `get_genre_id(genre: str, reverse_genre_map: Dict[str, int]) -> int`: (Static) Looks up the ID for a given genre name.
- `check_genre(database_genre: str, id3_genre: str) -> bool`: (Static) Verifies if database genres match those in ID3 tags.

**class SongID3**
- `__init__(self, artist, title, composer, album, year, genres, publisher, isrc, duration, error)`: storage class for ID3 tag data.

## main.py
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
    - `is_valid_attribute(value)`: Checks if a value is non-empty.
    - `check_all()`: Validates that critical fields are set and match between DB and ID3.
- `get_song(self, delta)`: Navigates to the next/prev song or jumps to a specific index.
- `_load_song_thread_job(self, pos)`: Background thread worker to load song data (IO bound).
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

<br>
<br>

# Proposed Refactoring Structure

This structure aims to separate concerns (UI, Data Models, Business Logic, Utilities) and adhere to Python packaging standards.

## Directory Layout

```text
jazler_database_editor/
│
├── src/                          # Source code package
│   ├── __init__.py
│   │
│   ├── core/                     # Core business logic and settings
│   │   ├── __init__.py
│   │   ├── config.py             # Formerly config.py
│   │   └── database.py           # Formerly database.py
│   │
│   ├── models/                   # Data transfer objects
│   │   ├── __init__.py
│   │   └── song.py               # Formerly Song.py (Classes: Song, SongID3)
│   │
│   ├── utils/                    # Helper functions and external IO
│   │   ├── __init__.py
│   │   └── audio.py              # Formerly mp3_stuff.py
│   │
│   └── ui/                       # User Interface
│       ├── __init__.py
│       └── app.py                # Formerly main.py (Class: JazlerEditor)
│
├── resources/                    # Hooks and static assets
│   └── hooks/
│       └── hook-mutagen.py
│
├── run.py                        # Entry point script
├── requirements.txt              # Dependency list
└── config.json                   # Configuration file
```

## Migration Map

| Current File       | Proposed Location           | Description                                      |
|:-------------------|:----------------------------|:-------------------------------------------------|
| `main.py`          | `src/ui/app.py`             | Contains the `JazlerEditor` class and UI logic.  |
| *(new)*            | `run.py`                    | New entry point that imports and runs local app. |
| `database.py`      | `src/core/database.py`      | Database connectivity and handling.              |
| `config.py`        | `src/core/config.py`        | Configuration loading and saving.                |
| `Song.py`          | `src/models/song.py`        | Data models for Song and ID3 tags.               |
| `mp3_stuff.py`     | `src/utils/audio.py`        | Audio file manipulation utilities.               |
| `hook-mutagen.py`  | `resources/hooks/hook-...`  | PyInstaller build hooks.                         |
