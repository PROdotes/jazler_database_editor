# 🏗️ Architecture V2: The Universal Database Toolkit

**Project:** `ms_database_sync_app` (GitHub: PROdotes/ms_database_sync_app)  
**Created:** 2026-01-10  
**Status:** 📋 Planning → Implementation

---

## 📌 Vision Statement

Transform this project from a single-purpose Jazler/Access editor into a **modular database toolkit** that can:

1. **Connect to any database** (Access, SQLite, Postgres) via pluggable backends
2. **Auto-discover schemas** with manual override support
3. **Power any UI** (CLI, Web, Qt, or even a 3D visualization)
4. **Audit, export, compare, and sync** databases
5. **Eventually bridge Jazler → Gosling2** with bidirectional sync

---

## 🎯 Core Use Cases

| Use Case | Priority | Description |
|----------|----------|-------------|
| **Browse & Edit** | 🔴 HIGH | Search songs, view fields, edit, save (replaces Tkinter) |
| **Audit Files** | 🔴 HIGH | Find ghosts (missing files), moved files |
| **Explore Schema** | 🟡 MEDIUM | View tables, columns, relationships |
| **Export Data** | 🟡 MEDIUM | Dump to JSON, CSV for analysis |
| **Bulk Updates** | 🟡 MEDIUM | Fix paths, trim whitespace, flag disabled songs |
| **Compare DBs** | 🟢 FUTURE | Diff Access vs SQLite (Gosling2 sync) |
| **Migrate Data** | 🟢 FUTURE | Copy Access → Gosling2 with transformations |

---

## 📁 Folder Structure

```
ms_database_sync_app/
├── src/
│   ├── core/                     # 🧠 THE BRAIN (pure logic, no I/O dependencies)
│   │   ├── __init__.py
│   │   ├── schema/
│   │   │   ├── __init__.py
│   │   │   ├── discovery.py      # Auto-probe tables/columns from any DB
│   │   │   ├── definition.py     # FieldDefinition, TableDefinition dataclasses
│   │   │   ├── overrides.py      # Load user overrides from JSON
│   │   │   └── registry.py       # SchemaRegistry: combines discovered + overrides
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── record.py         # Generic Record (dict-like, schema-aware)
│   │   │   └── diff.py           # RecordDiff for comparisons
│   │   ├── operations/
│   │   │   ├── __init__.py
│   │   │   ├── query.py          # Query builder (SELECT with filters)
│   │   │   ├── mutation.py       # Update/Insert/Delete builders
│   │   │   └── bulk.py           # Bulk operation + preview logic
│   │   └── sync/
│   │       ├── __init__.py
│   │       ├── comparator.py     # Compare two databases/tables
│   │       └── migrator.py       # Copy data between backends
│   │
│   ├── backends/                 # 🔌 PLUGGABLE DATA SOURCES
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract Backend interface
│   │   ├── access.py             # MS Access via pyodbc
│   │   ├── sqlite.py             # SQLite (for Gosling2 or local cache)
│   │   └── memory.py             # In-memory (for testing/diffs)
│   │
│   ├── media/                    # 🎵 FILE & AUDIO HANDLING
│   │   ├── __init__.py
│   │   ├── path_resolver.py      # Drive mapping, path normalization
│   │   ├── file_checker.py       # Check if files exist
│   │   └── id3_handler.py        # Read/write ID3 tags (from existing audio.py)
│   │
│   ├── exporters/                # 📦 OUTPUT FORMATS
│   │   ├── __init__.py
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   └── sql_exporter.py       # Generate INSERT statements
│   │
│   ├── services/                 # 🎯 USE-CASE ORCHESTRATORS
│   │   ├── __init__.py
│   │   ├── song_service.py       # CRUD for songs (replaces old DatabaseEditor logic)
│   │   ├── audit_service.py      # Find ghosts, moved files, orphans
│   │   ├── health_service.py     # Path validation, file existence
│   │   ├── export_service.py     # Coordinate exports
│   │   └── sync_service.py       # Coordinate cross-DB sync (future)
│   │
│   ├── cli/                      # 🖥️ COMMAND-LINE INTERFACE
│   │   ├── __init__.py
│   │   ├── __main__.py           # `python -m src.cli`
│   │   ├── probe.py              # Schema explorer
│   │   ├── audit.py              # Ghost/moved finder
│   │   ├── export.py             # Dump to JSON/CSV
│   │   └── compare.py            # Compare two DBs
│   │
│   ├── web/                      # 🌐 WEB UI (Flask + modular)
│   │   ├── __init__.py
│   │   ├── app.py                # Flask application factory
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── main.py           # Home, navigation
│   │   │   ├── songs.py          # Browse, search, edit songs
│   │   │   ├── schema.py         # Schema explorer
│   │   │   ├── audit.py          # Audit views
│   │   │   └── export.py         # Export configuration
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   └── style.css     # Dark theme, modern aesthetics
│   │   │   └── js/
│   │   │       └── app.js        # Client-side interactivity
│   │   └── templates/
│   │       ├── base.html         # Layout with sidebar navigation
│   │       ├── index.html        # Dashboard / home
│   │       ├── songs/
│   │       │   ├── list.html     # Search results table
│   │       │   └── edit.html     # Single song editor
│   │       ├── schema/
│   │       │   └── explorer.html # Table/column browser
│   │       └── audit/
│   │           └── report.html   # Ghost/moved songs report
│   │
│   ├── utils/                    # 🔧 SHARED UTILITIES (keep existing)
│   │   ├── __init__.py
│   │   ├── error_handler.py      # (existing)
│   │   ├── id3_tags.py           # (existing)
│   │   └── async_executor.py     # (future: thread management)
│   │
│   └── validators/               # ✅ VALIDATION (keep existing)
│       ├── __init__.py
│       └── song_validator.py     # (existing, may extend)
│
├── config/
│   ├── connections.json          # DB connection strings (replaces parts of config.json)
│   └── schema_overrides.json     # Ignored tables, field renames, display names
│
├── legacy/                       # 🏚️ OLD CODE (reference only, will delete)
│   ├── ui/                       # Old Tkinter app (moved here for reference)
│   ├── core/                     # Old database.py, engine.py
│   └── models/                   # Old song.py, field_definition.py
│
├── tools/                        # 🔧 STANDALONE SCRIPTS (keep, may integrate)
│   ├── audit_offline.py
│   ├── find_dead_songs.py
│   └── probe_schema.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── config.json                   # (existing, will migrate to config/)
├── theme.json                    # (existing, will use for web styling)
├── requirements.txt
├── run.py                        # Entry point: `python run.py web` or `python run.py cli`
└── ARCHITECTURE_V2.md            # This file
```

---

## 🧠 Core Architecture: Registry-Driven Design

The application is designed to be **completely modular**. The codebase provides the *functionality* (Search, Sort, Edit, Save), but the **Schema Registry** defines the *domain*.

### Logic Flow
1.  **Registry Config (`schema_overrides.json`)**: The single source of truth. Defines:
    *   Which tables are active.
    *   Which columns are visible/searchable.
    *   User-friendly display names (e.g., `fldCat1a` -> "Genre").
    *   Data types and validation rules.
2.  **Schema Service**: Loads the configuration and merges it with database introspection (auto-discovery).
3.  **UI Generation**:
    *   **Search Bar**: Populated dynamically based on "Searchable" fields in Registry.
    *   **Edit Form**: Renders fields defined in the Registry (input type determined by data type).
    *   **Grids/Tables**: Columns determined by "Visible" flag in Registry.

**Key Requirement:** A user must be able to add a new field to the Search dropdown by simply enabling it in the Schema Viewer, **without writing a single line of Python code**.

---

## 🔌 Backend Interface

All database operations go through a common interface:

```python
# src/backends/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class Backend(ABC):
    """Abstract interface for database backends."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[str]:
        """Return list of table names."""
        pass
    
    @abstractmethod
    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        """Return column metadata for a table."""
        pass
    
    @abstractmethod
    def fetch(self, table: str, filters: Optional[Dict] = None, 
              limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch records from a table."""
        pass
    
    @abstractmethod
    def fetch_one(self, table: str, primary_key: Any) -> Optional[Dict[str, Any]]:
        """Fetch a single record by primary key."""
        pass
    
    @abstractmethod
    def update(self, table: str, primary_key: Any, fields: Dict[str, Any]) -> bool:
        """Update a record."""
        pass
    
    @abstractmethod
    def count(self, table: str, filters: Optional[Dict] = None) -> int:
        """Count records matching filters."""
        pass
```

---

## 📋 Schema System

### Auto-Discovery
```python
# src/core/schema/discovery.py
class SchemaDiscovery:
    def probe(self, backend: Backend) -> Dict[str, TableDefinition]:
        """Auto-discover all tables and columns from a backend."""
        tables = {}
        for table_name in backend.get_tables():
            columns = backend.get_columns(table_name)
            tables[table_name] = TableDefinition(
                name=table_name,
                columns=[FieldDefinition.from_db_column(c) for c in columns]
            )
        return tables
```

### Schema Overrides (config/schema_overrides.json)
```json
{
  "ignored_tables": ["MSysObjects", "MSysACEs", "MSysRelationships"],
  "ignored_columns": {
    "snDatabase": ["fldInternalFlags", "fldReserved1"]
  },
  "display_names": {
    "snDatabase": {
      "fldArtist": "Artist",
      "fldTitle": "Title",
      "fldFilename": "File Path",
      "AUID": "ID"
    }
  },
  "primary_keys": {
    "snDatabase": "AUID"
  }
}
```

---

## 🖥️ Tkinter Functionality to Preserve

**These features from the old Tkinter app MUST be replicated in the web UI:**

### Core Features
- [ ] **Database Selector**: Choose Live vs Test database on startup
- [ ] **Search/Query**: Search by field (artist, title, album, etc.) with contains/equals
- [ ] **Result Navigation**: Previous/Next through search results with position indicator
- [ ] **Field Display**: Show Database values vs ID3 tag values side-by-side
- [ ] **Validation Indicators**: Color-coded status (green=match, red=mismatch, yellow=warning)
- [ ] **Edit Fields**: Modify ID3 fields in the right column
- [ ] **Copy Buttons**: Copy DB→ID3 or ID3→DB per field
- [ ] **Save**: Update database + write ID3 tags to file
- [ ] **Save & Rename**: Save + rename file to match expected path

### Supporting Features
- [ ] **Genre/Decade/Tempo Maps**: Load lookup tables for display
- [ ] **Path Validation**: Check if file exists, highlight if missing
- [ ] **Error Badge**: Show error count with click-to-view log
- [ ] **Web Search**: Google/Discogs lookup for current song

### Keyboard Shortcuts (to implement as web hotkeys)
| Key | Action |
|-----|--------|
| F1 | Open search dialog |
| F3 | Google search |
| F4 | Discogs search |
| F5 | Save |
| F6 | Save & Rename |
| F9 | Previous song |
| F10 | Next song |

---

## 📅 Implementation Roadmap

### 🏁 Phase 0: Foundation (Session 1, ~3-4 hours)
**Goal:** New folder structure + Backend abstraction working

- [ ] Create new folder structure (keep old code in `legacy/`)
- [ ] Implement `Backend` abstract class
- [ ] Implement `AccessBackend` (port from `database.py`)
- [ ] Implement `SchemaDiscovery` (port from `probe_schema.py`)
- [ ] Create `config/connections.json`
- [ ] Verify: Can connect and list tables/columns

**Deliverable:** `python -m src.cli probe --test` shows schema

---

### 🔍 Phase 1: Core + Query (Session 2, ~3-4 hours)
**Goal:** Can search and retrieve records

- [ ] Implement `SchemaRegistry` with override loading
- [ ] Implement `Record` model (generic dict wrapper)
- [ ] Implement `Query` builder with filters
- [ ] Implement `SongService.search()` and `SongService.get_by_id()`
- [ ] Port genre/decade/tempo map loading
- [ ] CLI: `query` command

**Deliverable:** `python -m src.cli query --field artist --value "Beatles"` returns records

---

### 🌐 Phase 2: Web Shell ✅ (Session 3)
**Goal:** Basic web UI with search and browse

- [x] Flask app skeleton with base template
- [x] Dark theme CSS (modern design)
- [x] Home page with database selector
- [x] `/songs` route: Search form + results table
- [x] `/songs/<id>` route: Single song view with resolved lookups
- [ ] Navigation: Previous/Next buttons *(deferred)*
- [ ] Pagination for large result sets *(deferred)*

**Deliverable:** Can search songs and browse through results in browser ✅

**Future Enhancement (Phase 2.5): Multi-Filter Search**
- [ ] Multiple filter conditions (AND logic)
- [ ] "Is empty" / "Is not empty" operators for finding missing data
- [ ] Genre filter by name (resolve to IDs internally)
- [ ] Save/load search presets
- Example: `Genre contains "za obradu" AND Year is empty`

---

### ✏️ Phase 3: Edit & Save (Session 4, ~4-5 hours)
**Goal:** Full Tkinter parity for editing

- [x] Edit form for song fields
- [x] Side-by-side DB vs ID3 display
- [x] File existence indicator
- [x] Quick Tools panel (Parse Album, Trim, Title Case, Normalize feat., Clear Composer)
- [x] Batch navigation (Prev/Next through search results)
- [x] Save & Next for rapid batch editing
- [x] Artist field read-only (linked via `fldArtistCode`)
- [ ] Port `id3_handler.py` (from existing `audio.py`) - *deferred*
- [ ] Copy buttons (DB↔ID3) - *deferred*
- [ ] Save button writes ID3 tags - *deferred*
- [ ] Port `SongValidator` logic - *deferred*
- [ ] **Lookup field editing** (genre/decade/tempo dropdowns) - *deferred*

**Deliverable:** Can edit and save song metadata via web UI ✅

**Data Integrity Notes:**
> **Artist:** Stored as `fldArtistName` (display copy) + `fldArtistCode` (FK to artists table).
> Editing the name without updating the code breaks referential integrity.
> Artist field is intentionally read-only; use Artist Manager to re-link.

> **Lookups:** Genre (`fldCat1`), Decade (`fldCat2`), Tempo (`fldCat3`) store numeric IDs.
> These reference `snCat1`, `snCat2`, `snCat3` tables respectively.
> Edit form will need dropdowns populated from lookup tables.

---

### 🎨 Phase 3.5: Artist Manager (Entity Picker) ✅
**Goal:** Allow users to re-link songs to different or new artists (resolving the "Ghost Artist" issue).

**Core Concept:**
We cannot just type a string for `fldArtistName`. We must select an `AUID` from `snArtists`.

**Implementation:**
*   **Service:** `ArtistService` (Search, Get, Create).
*   **API:**
    *   `GET /artists/search?q=...` -> JSON list of `{id, text}`.
    *   `POST /artists/create` -> `{name} -> {id, text, success}`.
*   **UI Component:** `macros/entity_picker.html`.
    *   Replaces the read-only artist field in Song Editor.
    *   "Search-as-you-type" dropdown (Select2 style but custom lightweight).
    *   **"Create New"**: If artist doesn't exist, offers one-click creation.

**Status:** Completed ✅
*   Resolves the dependency for Phase 9.5 (Import from Orphan).

### ✏️ Phase 3.6: Artist CRUD & Propagation (Partial)
**Goal:** Full management of Artists (Rename, Delete, Merge).

**Challenge:**
`snDatabase` stores `fldArtistName` redundantly.

**Implementation Plan:**
*   [x] **Bulk Reassign**: Bulk Edit now supports changing Artist for multiple songs (propagates ID and Name). ✅
*   [ ] **Rename Artist**: Edit single artist record -> propagates to all songs.
*   [ ] **Merge Tool**: Dedicated UI to merge A into B (easier than bulk reassign for 1000 songs).

**Status:** Partial ✅
*   Bulk Edit Artist implemented and verified.


**Deliverable:** Can change song artist via web UI without breaking links

---

### 📁 Phase 4: File Operations (Session 5, ~2-3 hours)
**Goal:** Save & Rename, path handling

- [x] Implement `PathResolver` (drive mapping via `MediaService`)
- [x] Save & Rename functionality (physical rename on save)
- [x] File existence checks with visual feedback (View/Edit pages)
- [ ] Error handling + error log viewer (Partial - logic done, UI logger pending)

**Deliverable:** Full Tkinter parity achieved 🎉

---

### 🌐 Phase 4.5: Virtual Library & Offline Sync (Session 5.5, ~3-4 hours)
**Goal:** Manage and edit the library without access to physical files.

**1. VFS (Virtual File System) Mirroring:**
- [x] **Log Parser:** High-speed parser for PowerShell `log.txt`.
- [x] **Snapshot Integration:** `MediaService` checks "Virtual Mirror" via `VfsService`.
- [x] **UI Indicators:** 🟢 🔵 🔴 status indicators implemented.

**2. ID3 Tag Snapshots (The "Ghost" Data):**
- [x] **Snapshot Generator:** Export actual ID3 tags to `metadata_snapshot.json` while Live. 
    *   *Turbo Note:* Implemented `SnapshotService` with `ThreadPoolExecutor`.
- [x] **Offline Reading:** Display metadata from the cache when the physical file is unreachable.
- [x] **Data Hierarchy:** Always prefer Real ID3 > Cache > Database values.

**3. Offline Change Queuing:**
- [x] **Pending Buffer:** Store edits in `pending_sync.json` via `SyncService`.
- [x] **Conflict Resolution:** "Last Write Wins" logic implemented for individual song edits.
- [x] **Sync Action:** New `/sync` dashboard for bulk applying changes to the DB.

**Technical Spec:**
> **Log Format:** Assumes `Get-ChildItem -Recurse | Select-Object FullName` format.
> **Persistence:** `src/services/vfs_service.py` to manage the mirror and cache.
> **Consistency:** Checksum or Date-modified comparison (optional) to ensure snapshot isn't too stale.

**Deliverable:** Can work on the library at home/offline and sync later. ✅

---

### 🔎 Phase 5: Audit Tools (Session 6, ~3 hours)
**Goal:** Ghost finder in web UI

- [x] Port `audit_offline.py` logic to `AuditService`
- [x] `/audit` route: Configure and run audit
- [x] Audit report page: List ghosts/moved with color coding
- [x] Export audit results to file (Automated via report page)

**Deliverable:** Can find missing songs via web UI ✅

---

### 🕵️ Phase 5.5: Untracked Files (The "Reverse Audit") ✅
**Goal:** Identify physical files on the disk (or VFS log) that are NOT in the database.

**Core Concept:**
The inverse of the standard Audit. 
- *Standard Audit:* Database Record → File Check (Missing = Ghost)
- *Reverse Audit:* File System → Database Check (Missing = Orphan)

**1. Service Layer (`AuditService.find_untracked_files()`):**
*   **Logic:** `FileSystemPaths - DatabasePaths = Untracked`
*   **Performance:** Uses `limit=200000` to ensure full DB fetch (Access default is 100).
*   **Normalization:**
    *   Paths are lowercased and `.mp3` extension normalized.
    *   *Drive Letter Handling:* New config `audit_ignore_drive_letters: true` in `connections.json`.
    *   If true, strips `B:\` or `Z:\` prefix before comparison to handle mapped drive differences.
*   **Source Independence:**
    *   *Online:* Recursively scans `base_songs_path` via `MediaService.scan_files()`.
    *   *Offline:* Uses `VfsService.files` (loaded from `log.txt`).

**2. UI Implementation:**
*   **Audit Dashboard:** New "Find Untracked Files" card.
*   **Untracked Report:**
    *   Dedicated view `/audit/untracked-report`.
    *   Lists all Orphan paths.
    *   **"Copy Path"** button for manual utility.
    *   Count summary.

**3. Integration:** 
*   Uses `AuditService` which orchestrates `SongService` (for DB paths) and `MediaService`/`VfsService` (for File paths).

**Deliverable:** List of MP3s that exist but are not in the database. ✅

---

### 📥 Phase 9.5: Import from Orphan (Future Complex Task) 🔴
**Goal:** Direct "One-Click" import of songs from the Untracked Files report.

**Why is this complex?**
It is not just an INSERT statement. It requires a chain of dependencies:

1.  **Metadata Extraction:**
    *   Must read ID3 tags (Artist, Title, Album, etc.) from the physical file.
    *   *Offline Challenge:* If VFS is active, we can't read tags unless they are in the `metadata_snapshot.json`. Likely requires Online mode.

2.  **Artist Reconciliation (The Hard Part):**
    *   Jazler uses `ArtistCode` (FK) + `ArtistName`.
    *   We cannot just insert string "The Beatles".
    *   **Logic needed:**
        1.  Parse Artist from MP3.
        2.  Search `snArtists` for match.
        3.  *If Found:* Use existing `ArtistCode`.
        4.  *If Not Found:* Create new Artist record → Get new `ArtistCode`.
    *   **Dependency:** Requires **Phase 3.5: Artist Manager** to be fully robust.

3.  **Category Mapping:**
    *   Must default or guess Genre/Decade/Tempo.
    *   Cannot insert NULLs where Jazler expects IDs.

4.  **UI Workflow:**
    *   "Import" button on Orphan row.
    *   Opens a "New Song" modal pre-filled with ID3 data.
    *   User confirms Artist/Title/Category.
    *   Save → Insert into `snDatabase`.

**Prerequisites:** Phase 3.5 (Artist Manager), Phase 4 (ID3 Reading).


---

### 📊 Phase 6: Schema Manager & Modular Grid (Session 7, ~2 hours)
**Goal:** Configure the application via the UI and enable dynamic data views.

**Core Concept: Registry-Driven UI**
The Search Grid must not be hardcoded. It must ask the Registry "What columns do I show?".

**1. Registry Configuration (`grid_views` & `form_layouts`):**
Define named views in `schema_overrides.json`:
```json
"grid_views": {
    "default": ["fldArtistName", "fldTitle", "fldAlbum", "fldYear"],
    "publishing": ["fldArtistName", "fldTitle", "fldComposer", "fldPublisher", "fldCDKey"]
},
"form_layouts": {
    "default": ["*"], 
    "tagging": ["fldArtistName", "fldTitle", "fldCat1a", "fldCat2", "fldCat3"],
    "technical": ["fldFilename", "fldDuration", "fldCDKey", "fldEnabled"]
}
```

**2. Service Layer:**
*   `SongService.get_grid_columns(view_name)`: Returns list of column objects (name, label, type).
*   `SongService.get_form_fields(layout_name)`: Returns list of fields to render in the editor.
*   `SongService.get_searchable_fields()`: Returns available search dropdown options (Completed).

**3. UI Implementation:**
*   **View Switcher:** Dropdown in toolbar to select active Grid View or Form Layout.
*   **Dynamic Table:** Jinja2 loop iterates over `columns` to render `<th>` and `<td>`.
*   **Dynamic Form:** `edit.html` iterates over `fields` to render inputs (Text, Select, Toggle) based on type.
*   **Column Toggles:** UI to show/hide columns ad-hoc (updates session state).

**Tasks:**
- [ ] Implement `grid_views` and `form_layouts` in `schema_overrides.json`
- [ ] Implement `get_grid_columns` and `get_form_fields` in SongService
- [ ] Refactor `list.html` to use dynamic loops
- [ ] Refactor `edit.html` to use dynamic field rendering
- [ ] Create View Switcher UI
- [ ] **Config UI:** Allow users to create/edit Views (Advanced)

---

### 📦 Phase 7: Export & Reporting (Session 8, ~3 hours)
**Goal:** Full data portability with consistent templating.

**Core Concept: Export Templates**
Exports should not be random column dumps. They should use the same "View" logic as the Grid and Editor.

**1. Registry Configuration (`export_templates`):**
```json
"export_templates": {
    "broadcaster_report": ["fldArtistName", "fldTitle", "fldComposer", "fldISRC"],
    "simple_list": ["fldArtistName", "fldTitle", "fldYear"]
}
```

**2. UI Implementation:**
*   **Export Modal:** User selects a Template (e.g., "Simple List") or "Current Grid View".
*   **Format Selection:** JSON, CSV, SQL.
*   **Preview:** Show snippet of what will be exported.

**Tasks:**
- [x] JSON/CSV generic backends
- [x] `/export` route (Basic)
- [ ] Refactor UI to use `export_templates` from Registry
- [ ] Option to export "Current Grid Selection"
- [x] Export with resolved lookups
- [x] Specialized exports for Audit results (Ghosts list)

**Import:**
- [ ] CSV import with preview
- [ ] Field mapping UI (map CSV columns to DB fields)
- [ ] Validation before apply
- [ ] Dry-run mode (show what would change)

---

### ⚡ Phase 8: Bulk Operations (Session 9, ~2 hours)
**Goal:** Fix many records at once

**Selection & Preview:**
- [x] Multi-select checkboxes on search results
- [x] "Select All" / "Select Visible" buttons
- [x] Floating Bulk Action Bar with selection counter
- [x] Bulk edit form with field-level toggles

**Text Field Operations:**
- [x] Path fixer (Path Swap tool for drive letters/folders)
- [x] Whitespace trimmer (Added to Bulk Edit)
- [ ] Find & Replace across general fields (Coming soon)

**Lookup/Category Operations:**
- [x] Add genre to selected songs
- [x] Set decade for selected songs
- [x] Set tempo/year/publisher for selected songs

**Status Operations:**
- [x] Bulk disable songs (Safety deactivation)
- [x] Bulk export selected items

---

### 📚 Phase 8.5: Dictionary & Lookup Management
**Goal:** Unified management of all reference data (Genres, Categories, Artists) with a dedicated strategy for complex entities.

**Concept: "The Dictionary System"**
Jazler relies on auxiliary tables to store reference data. To manage these effectively within the `ms_database_sync_app` architecture, we distinguish between two types of dictionaries:

#### 1. Simple Dictionaries (e.g., `snCat1` Genre, `snCat2` Decade)
*   **Characteristics:** Simple Key-Value pairs (ID -> Label).
*   **Usage:** Populates dropdowns in the Song Editor.
*   **Management Strategy:** Generic CRUD.
    *   **Dashboard:** `/lookups/` (List of all dictionaries)
    *   **Controller:** Generic `LookupController` handles any table defined in `schema_overrides.json` with `is_lookup=True`.

#### 2. Complex Dictionaries (e.g., `snArtists`)
*   **Characteristics:** Entities with metadata (Surname, Type) and heavy usage.
*   **The Propagation Challenge:**
    *   Jazler denormalizes artist names into `snDatabase` (`fldArtistName`).
    *   **Renaming Risk:** Changing a name in `snArtists` *without* updating `snDatabase` creates "Ghost Data" (songs linked to an ID but showing the old name).
*   **Management Strategy:** Specialized Service.
    *   **Dashboard:** `/dictionaries/artists`
    *   **Service:** `ArtistService` (extends Lookup capabilities)
    *   **Tools:**
        *   **Orphan Detection:** Identify artists with 0 linked songs.
        *   **Merge Tool:** Consolidate duplicates (e.g., "Beatles" -> "The Beatles") and update all linked songs.

---

### ✅ Implementation Status (Phase 8.5)
**1. Generic Infrastructure (Completed)**
*   **Registry:** Updated `schema_overrides.json` with `lookup_config` for Cat1/2/3.
*   **Service:** `LookupService` implemented.
*   **UI:** Created generic `/lookups` routes for Index and Grid views.

**2. Artist Extensions (In Progress)**
*   **Structure:** Defined "Dictionaries" as a core menu concept.
*   **Next Steps:**
    *   [ ] Implement `ArtistService.get_usage_counts()` for Orphan detection.
    *   [ ] Create Artist Manager UI with "Songs Count" column.
    *   [ ] Implement "Merge Artist" workflow.


**2. Registry API Contract (`SchemaRegistry`):**
*   `get_lookup_tables() -> List[TableDefinition]`: Returns all table definitions where `is_lookup` is True.
*   **TableDefinition Object:** Must expose `lookup_config` dictionary and `columns` metadata.

**3. Service Layer (`LookupService`):**
*   `get_all(table_name) -> List[Record]`: Fetches all rows, sorting by `lookup_config.sort_column`.
*   `create(table_name, data: Dict)`: Inserts record. Validates that `display_column` is not empty.
*   `delete(table_name, pk_value)`: Checks for foreign key usage (orphans) before deletion.

**4. Generic UI Implementation:**
*   **Index Page (`/lookups/`)**:
    *   Iterates `registry.get_lookup_tables()`.
    *   Renders a card for each (Title = `display_name`, details = Row Count).
*   **Generic Grid (`/lookups/<table_name>`):**
    *   Header: Iterates `lookup_config.grid_columns`.
    *   Rows: Iterates records.
    *   Actions: Edit/Delete buttons.
*   **Generic Form (`/lookups/<table_name>/<action>`):**
    *   Iterates table columns.
    *   Renders input fields based on column type (Text, Number, Boolean).

**Tasks:**
- [x] Update `schema_overrides.json` with `lookup_config` for Cat1/2/3.
- [x] Implement `get_lookup_tables` in Registry.
- [x] Create `lookups_bp` Routes (Generic Index, Grid).
- [ ] Implement Entry Editor (Add/Edit form).
- [ ] Create `lookup_service` logic (Create/Update/Delete).


---

### 🔄 Phase 9: Gosling2 Sync (Future)
**Goal:** Bridge to new system with bidirectional synchronization.

- [ ] `SqliteBackend` implementation
- [ ] `Comparator` (diff two databases)
- [ ] `Migrator` (copy with field mapping)
- [ ] **Missing Song Sync**: Load songs into both databases if 1 has them missing (Bi-directional INSERT).
- [ ] Bidirectional sync detection

---

## 🎨 Web UI Design Notes

### Theme
- Dark background (#1a1a2e or similar)
- Accent color from `theme.json`
- Monospace font for data fields
- Clear visual hierarchy

### Layout
```
┌────────────────────────────────────────────────────────┐
│  🎵 MS Database Sync                    [Test DB] 🟢   │
├──────────┬─────────────────────────────────────────────┤
│          │                                             │
│ 📋 Songs │   [Search Bar]                    [🔍]     │
│ 📊 Schema│   ─────────────────────────────────────     │
│ 🔍 Audit │   │ Artist    │ Title     │ Album    │     │
│ 📦 Export│   ├───────────┼───────────┼──────────┤     │
│          │   │ Beatles   │ Help!     │ Help!    │     │
│          │   │ Queen     │ Bohemian  │ Night... │     │
│          │   └───────────┴───────────┴──────────┘     │
│          │                                             │
│          │   [◀ Prev]  Record 5 of 234  [Next ▶]      │
└──────────┴─────────────────────────────────────────────┘
```

### Song Edit View
```
┌─────────────────────────────────────────────────────────┐
│  ◀ Back to Search          Song #12345                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │   DATABASE      │    │   ID3 TAGS      │            │
│  ├─────────────────┤    ├─────────────────┤            │
│  │ Artist:         │ →  │ Artist:         │  🟢        │
│  │ The Beatles     │ ←  │ The Beatles     │            │
│  ├─────────────────┤    ├─────────────────┤            │
│  │ Title:          │ →  │ Title:          │  🔴        │
│  │ Help            │ ←  │ Help!           │            │
│  └─────────────────┘    └─────────────────┘            │
│                                                         │
│  File: Z:\Songs\Pop\Beatles - Help.mp3     [✓ Exists]  │
│                                                         │
│  [💾 Save]  [💾 Save & Rename]  [🔍 Google]  [🔍 Discogs]│
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Strategy

| Layer | Test Type | Coverage Goal |
|-------|-----------|---------------|
| Backends | Unit + Integration | Connection, CRUD operations |
| Schema | Unit | Discovery, override merging |
| Services | Unit | Business logic, validation |
| Web Routes | Integration | Request/response, templates |
| CLI | Integration | Command parsing, output |

---

## 📚 Dependencies

### Existing (keep)
- `pyodbc` - MS Access connectivity
- `mutagen` - ID3 tag handling

### New
- `flask` - Web framework
- `jinja2` - Templating (comes with Flask)

### Optional Future
- `sqlalchemy` - If we want ORM-style operations later
- `sqlite3` - For Gosling2 backend (stdlib)

---

## ⚠️ Migration Notes

### What Gets Moved to `legacy/`
- `src/ui/app.py` (Tkinter app)
- `src/core/database.py` (replaced by backends)
- `src/core/engine.py` (replaced by services)
- `src/models/song.py` (replaced by generic Record)
- `src/models/field_definition.py` (replaced by schema system)

### What Gets Preserved
- `src/utils/error_handler.py` ✓
- `src/utils/audio.py` → becomes `src/media/id3_handler.py`
- `src/validators/song_validator.py` ✓
- `src/models/db_schema.py` (SongColumns enum) → reference for overrides
- `tools/*` → keep as standalone, may integrate later
- `config.json` → migrate to `config/connections.json`
- `theme.json` → use for web CSS generation

---

## 🚀 Getting Started (Next Session)

1. **Create branch**: `git checkout -b v2-architecture`
2. **Create folders**: Follow structure above
3. **Move old code**: `src/ui` → `legacy/ui`, etc.
4. **Implement Backend ABC**: `src/backends/base.py`
5. **Port AccessBackend**: From `database.py`
6. **Test connection**: Verify pyodbc still works

---

## 📝 Session Log

| Date | Phase | Completed | Notes |
|------|-------|-----------|-------|
| 2026-01-10 | Planning | ✅ | Architecture document created |
| 2026-01-10 | Phase 0 | ✅ | Backend abstraction, schema discovery, CLI probe |
| 2026-01-10 | Phase 1 | ✅ | Record model, SongService, CLI query, lookup maps |
| 2026-01-10 | Phase 2 | ✅ | Flask web UI, dark theme, search, view |
| 2026-01-10 | Phase 3 | ✅ | Edit form, Quick Tools, batch navigation, Save & Next |
| 2026-01-11 | Phase 4 | ✅ | File Ops: Save & Rename, Path Resolver |
| 2026-01-11 | Phase 4.5 | ✅ | Virtual Library, Offline Mirror, Sync Buffer |
| 2026-01-11 | Phase 5 | ✅ | Audit Service, Ghost Report, Export |
| 2026-01-11 | Phase 6 | ✅ | Schema Manager & Modular Grid (View Switcher, Dynamic Search) |
| 2026-01-11 | Phase 8 | ✅ | Bulk Operations: Multi-select, Bulk Edit, Path Swap |
| 2026-01-11 | Phase 8.5 | ✅ | Lookup Registry, Generic Grid, Generic Edit Form |
| 2026-01-11 | Phase 3.5 | ✅ | Artist Manager (Entity Picker, Search, Create) |
| 2026-01-11 | Phase 3.6 | 🚧 | Partial: Bulk Artist Assign implemented |
| 2026-01-11 | Phase 9 | 📝 | Planning: Bi-directional sync requirements logged |

---

*Document Version: 1.2*  
*Author: Antigravity*  
*Last Updated: 2026-01-11*
