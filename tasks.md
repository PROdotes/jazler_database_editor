# Refactoring Tasks - Preparation for Migration

This task list outlines the steps to refactor the internal code structure to meet modern standards while keeping the existing file layout. This prepares the codebase for a seamless move to the new directory structure later.

- [x] **1. Refactor `Song.py` (Model Encapsulation)**
    - [x] **Convert Factory to Class Method**
        - [x] Rename `get_data(...)` to `Song.from_db_record(...)`.
        - [x] Make it a `@classmethod` of the `Song` class.
        - [x] Update `main.py` to call `Song.from_db_record` instead of `get_data`.
    - [x] **Encapsulate Path Logic**
        - [x] Move `get_location(...)` logic inside `Song` class as `get_expected_path(self)`.
        - [x] Update usages in `Song.__init__` to use `self.get_expected_path()`.
    - [x] **Standardize Debugging**
        - [x] Remove `basic_data()` and `id3_data()` print methods.
        - [x] Implement standard `__repr__(self)` and `__str__(self)` methods for `Song` and `SongID3` classes to return string representations instead of printing.
    - [x] **Static Utilities**
        - [x] Move `list_to_string`, `calc_decade`, `check_genre` inside `Song` class as `@staticmethod` (or strictly related class methods) to reduce global namespace pollution.
        - [x] Move `get_genre_id` inside `Song` class (or utility) to remove it from global scope.

- [x] **2. Refactor `config.py` (Configuration Singleton)**
    - [x] **Create Config Class**
        - [x] Define a `Config` class to hold `db_path_live`, `db_path_test`, `drive_map`, etc.
        - [x] Implement a Singleton pattern or a simple generic instantiation so `config = Config()` loads the data.
        - [x] Implement `set_db_mode` and `load` logic within the class.
        - [x] Replace global variable access in `main.py` (e.g., `DB_PATH_LIVE`) with `config.db_path_live`.

- [x] **3. Refactor `main.py` (UI & Logic Separation)**
    - [x] **Inline Helpers**
        - [x] Inline `_clean_lookup_string` into `discogs_lookup` and `google_lookup` or create a small helper class `WebSearch`.
    - [x] **Refactor Database Setup**
        - [x] Separate `setup_database_config` into UI code (asking user) and logic code (calling `config.set_db_mode`).
    - [x] **Update References**
        - [x] Ensure `JazlerEditor` uses the new `Song` class methods and `Config` object.

- [x] **4. Refactor `mp3_stuff.py` (Utility grouping)**
    - [x] **Create AudioUtils Class**
        - [x] Wrap `song_length`, `get_tag`, and `tag_write` into an `AudioMetadata` class as static methods.
        - [x] Update imports in `Song.py` and `main.py`.

- [x] **5. Verification**
    - [x] Run the application after each major refactor step to ensure no regression in functionality.
    - [x] Verify that all "Global functions" that are actually business logic are now attached to their relevant classes.


# Phase 2: Directory Migration Plan

This phase executes the structural changes by creating the new directory layout and moving the files.

- [ ] **1. Create Directory Structure**
    - [ ] Create `src/core`, `src/models`, `src/ui`, `src/utils`, `resources/hooks`.

- [ ] **2. Core - Config (`src/core/config.py`)**
    - [ ] **Action**: Copy `config.py` to `src/core/config.py`.
    - [ ] **Method: `Config.__init__`**: Update `CONFIG_FILE` to use absolute path handling (e.g., `os.path.join(PROJECT_ROOT, "config.json")`) to ensure the config file is always found in the project root.
    - [ ] **Method: `Config._load_from_file`**: Ensure no relative path issues.
    - [ ] **Other**: No removal required.

- [ ] **3. Core - Database (`src/core/database.py`)**
    - [ ] **Action**: Copy `database.py` to `src/core/database.py`.
    - [ ] **Class: `Database`**: No code changes required. Methods `_get_connection`, `fetch_songs`, etc., are self-contained.

- [ ] **4. Utils - Audio (`src/utils/audio.py`)**
    - [ ] **Action**: Copy `mp3_stuff.py` to `src/utils/audio.py`.
    - [ ] **Imports**: Update `from Song import SongID3` to `from src.models.song import SongID3` (inside TYPE_CHECKING block).
    - [ ] **Class: `AudioMetadata`**: No logic changes required.

- [ ] **5. Models - Song (`src/models/song.py`)**
    - [ ] **Action**: Copy `Song.py` to `src/models/song.py`.
    - [ ] **Imports**: 
        - Update `from config import app_config` to `from src.core.config import app_config`.
        - Update `from mp3_stuff import AudioMetadata` to `from src.utils.audio import AudioMetadata`.
    - [ ] **Class: `Song`**: No logic changes required.
    - [ ] **Class: `SongID3`**: No logic changes required.

- [ ] **6. UI - App (`src/ui/app.py`)**
    - [ ] **Action**: Copy `main.py` to `src/ui/app.py`.
    - [ ] **Imports**: Update all localized imports (`Song`, `database`, `config`, `mp3_stuff`) to absolute imports from `src...`.
    - [ ] **Method: `if __name__ == "__main__":`**: **REMOVE** this block. This logic moves to `run.py`.
    - [ ] **Class: `JazlerEditor`**: No logic changes required.

- [ ] **7. Entry Point (`run.py`)**
    - [ ] **Action**: Create new file `run.py` at project root.
    - [ ] **Content**: Import `JazlerEditor` from `src.ui.app` and execute the main loop. Includes path setup if necessary.

- [ ] **8. Resources**
    - [ ] **Action**: Move `hook-mutagen.py` to `resources/hooks/hook-mutagen.py`.

- [ ] **9. Cleanup**
    - [ ] Delete original files (`config.py`, `database.py`, `mp3_stuff.py`, `Song.py`, `main.py`, `hook-mutagen.py`) after verification.
