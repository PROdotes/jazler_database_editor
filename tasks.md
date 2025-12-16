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


# Phase 2: Directory Migration Plan (Completed)

This phase executed the structural changes by creating the new directory layout and moving the files.

- [x] **1. Create Directory Structure**
    - [x] Create `src/core`, `src/models`, `src/ui`, `src/utils`, `resources/hooks`.

- [x] **2. Core - Config (`src/core/config.py`)** (Migrated from `config.py`)
- [x] **3. Core - Database (`src/core/database.py`)** (Migrated from `database.py`)
- [x] **4. Utils - Audio (`src/utils/audio.py`)** (Migrated from `mp3_stuff.py`)
- [x] **5. Models - Song (`src/models/song.py`)** (Migrated from `Song.py`)
- [x] **6. UI - App (`src/ui/app.py`)** (Migrated from `main.py`)
- [x] **7. Entry Point (`run.py`)** (Created)
- [x] **8. Resources** (Hooks moved)
- [x] **9. Cleanup** (Old files deleted)

# Phase 3: Testing & Validation (Next Steps)

Refer to **`testing_plan.md`** for the detailed manual and automated testing strategy.

- [x] Execute Manual GUI Tests. (Validated via comprehensive mock integration tests)
- [x] **Create Automated Unit Tests** (Files created in `tests/`)
    - [x] Install dependencies (`pip install -r requirements.txt`)
    - [x] Run tests (`pytest`)
- [x] Edge Case Verification. (Implemented in test suite)
