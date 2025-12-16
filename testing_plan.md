# Testing Plan

This document outlines the testing strategy for the Jazler Database Editor, focusing on verifying functionality before and after the directory structure migration.

## 1. Prerequisites

Before running tests, ensure the following environment is set up:
- **Test Database**: Ensure the "Test" database path in `config.json` points to a valid copy of the Access database (`.accdb`) that is safe to modify.
    - Default: `\\ONAIR\Jazler RadioStar 2\Databases - Copy\JZRS2DB-V5.accdb`
- **Test Audio Files**: Have a set of MP3 files available that match entries in the Test Database.
    - Note: The app maps drives (e.g., `b:` to `z:`). Ensure the mapped paths are accessible on the local machine.
- **Backup**: Always backup `config.json` and the `.accdb` file before intensive testing.

## 2. Manual Testing Checklist (GUI)

Perform these steps to verify end-to-end functionality.

### A. Startup & Connection
- [ ] Run the application (`python main.py` or `python run.py`).
- [ ] Verify the "Select Database" prompt appears.
- [ ] Select **NO** (Test Database).
- [ ] Verify the window title shows `[TEST]`.
- [ ] Verify the status bar is Green ("SAFE MODE").

### B. Song Loading & Display
- [ ] Verify the first song loads automatically (or after Query).
- [ ] Check that **Database Value** fields need to match the database content.
- [ ] Check that **MP3 Tag Value** fields are populated from the file.
- [ ] Verify color coding:
    - **Green** background: Fields match.
    - **Red** background: Fields mismatch (or file missing).
- [ ] Verify Status Indicators:
    - "Genre Status": Matches if DB genres are subset of ID3 genres.
    - "File Status": "File OK" if file exists and can be read.

### C. Navigation
- [ ] Click **Next > (F10)**: Should load the next song in the query list.
- [ ] Click **< Prev (F9)**: Should load the previous song.
- [ ] Enter a number in **Jump** field and click Jump: Should go to that specific index.

### D. Editing & Saving
- [ ] Select a song with mismatches (Red fields).
- [ ] Click the **Arrow (->)** button to copy DB value to ID3 value.
- [ ] Manually edit a text field (e.g., Title).
- [ ] Click **Save (F5)**.
    - Verify "Saved" confirmation or visual update.
    - Verify the file's ID3 tags were actually updated (check in Windows Explorer or another player).
    - Verify the Database record was updated (reload the song or check via Access).

### E. Advanced Operations
- [ ] **Rename (F6)**:
    - Change the Artist or Title.
    - Click **Rename**.
    - Verify the physical file is renamed on disk.
    - Verify the `fldFilename` in the database is updated.
- [ ] **Query (F1)**:
    - Press F1. enter a search term (e.g., "Love").
    - Verify the result list is populated and the first result loads.
- [ ] **Web Lookups**:
    - Press **F3** (Google): Should open default browser with search query.
    - Press **F4** (Discogs): Should open Discogs search.

### F. Edge Case Verification
- [ ] **Drive Mapping**:
    - Ensure `config.json` has a mapping (e.g., `"b:": "z:"`).
    - Load a song where the database path starts with `b:`.
    - Verify the app finds the file locally at `z:` (File Status Green).
- [ ] **Session Persistence**:
    - Perform a search query (e.g., Artist "Abba").
    - Close the application.
    - Re-open the application.
    - Verify the list automatically loads the "Abba" results.
- [ ] **Special Genre Rules**:
    - Load a song that matches a "No Year Subfolder" rule (e.g., Rock).
    - Verify the *Expected Path* (displayed in UI) matches the rule logic (i.e., NO year folder in path).
- [ ] **Config Generation**:
    - (Safe to do only if you have a backup) Rename `config.json` to `config_backup.json`.
    - Start the app.
    - Verify it launches with default settings and creates a NEW `config.json` file.

## 3. Automated / Unit Testing Strategy

While the GUI is manually tested, the core logic should be verified with scripts.

### Test Script: `tests/test_core.py` (Proposed)
- **Config**:
    - Verify `Config` singleton loads.
    - Verify `set_db_mode` returns correct paths.
- **AudioMetadata**:
    - Run `AudioMetadata.song_length` on a dummy MP3.
    - Run `AudioMetadata.get_tag` and verify known tags.
- **Song Model**:
    - Instantiate `Song` with mock DB data.
    - Verify `get_expected_path` logic (generation of filenames based on genre/year rules).
    - Verify `check_genre` logic with various string inputs.

## 4. Migration Verification (Run after Phase 2)

After moving files to `src/`, perform these specific checks:

- [ ] **Import Check**: Run `python run.py`. If it crashes immediately with `ModuleNotFoundError`, imports are broken.
- [ ] **Config Resolution**: Check if `config.json` is read correctly from the root directory, not `src/core/`.
- [ ] **Asset Loading**: Ensure the app icon (if any) and hook scripts still work (if rebuilding EXE).
- [ ] **PyInstaller Build**: Run `pyinstaller main.spec` (updated spec needed) to ensure the build system can find the new paths.
