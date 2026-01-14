# Phase 9: Safe Import & Synchronization Plan

## 🎯 Objective
Implement the "Import from Orphan" feature to allow bringing untracked MP3 files into the Jazler database.
**CRITICAL:** This process is high-risk. It must be **non-destructive** and **heavily tested** to prevent database corruption or duplication.

## ⚠️ Risks
1.  **Duplicate Records:** Re-importing a song that already exists (but maybe has a slightly different filename or metadata).
2.  **Data Loss:** Relying solely on ID3 tags might lose database-specific info (Date Added, Play Counts, Categories not in tags).
3.  **Bad Parsing:** Incorrectly guessing Artist/Title from filenames like `01-Track.mp3`.
4.  **Performance:** Scanning 20,000 files can hang the UI.

---

## 🛡️ Testing Strategy (Test-Driven)

We will not write implementation code until tests exist.

### 1. Unit Tests (`test_import_parser.py`)
**Goal:** Verify that we can correctly extract Artist/Title from filenames and ID3 tags without any DB connection.

**Test Cases (Bob must implement these exactly):**
| Input Filename | ID3 Artist | ID3 Title | Expected Artist | Expected Title |
| :--- | :--- | :--- | :--- | :--- |
| `Madonna - Vogue.mp3` | None | None | `Madonna` | `Vogue` |
| `01 - Beatles - Help.mp3` | None | None | `Beatles` | `Help` |
| `AC-DC - TNT.mp3` | None | None | `AC-DC` | `TNT` |
| `Track01.mp3` | `Prince` | `1999` | `Prince` | `1999` |
| `Unknown.mp3` | None | None | `Unknown` | `Unknown` |

**Parsing Rules to Implement:**
1.  Split by ` - ` (space hyphen space).
2.  If 2 parts: `Part1` = Artist, `Part2` = Title.
3.  If 3 parts (e.g. `01 - Artist - Title`): Ignore `01`, `Part2`=Artist, `Part3`=Title.
4.  **Priority:** ID3 Tags > Filename > "Unknown".

### 2. Integration Tests (`test_import_db.py`)
**Goal:** Verify DB constraints and Artist Linking. Use an in-memory SQLite DB for speed.

**Scenarios:**
1.  **Duplicate Check:**
    *   Insert Song A (`Artist="Cher", Title="Believe"`).
    *   Try to Import Song B (`Artist="Cher", Title="Believe"`).
    *   **Result:** Should detect conflict/duplicate. Do NOT insert.
2.  **Artist Linking:**
    *   `snArtists` table has `ID=10, Name="Queen"`.
    *   Import song with Artist `Queen`.
    *   **Result:** Song should be linked to `ID=10`. New artist should NOT be created.
3.  **New Artist:**
    *   Import song with Artist `NewBand`.
    *   **Result:** New record in `snArtists` created. Song linked to new ID.

### 3. "Golden Master" Verification (Real Data)
**Goal:** Prove safety on real user data.

**Procedure:**
1.  **Select:** Pick 5 existing songs in the real production DB.
2.  **Snapshot:** Run `SELECT * FROM snDatabase WHERE ID IN (...)` and save to `golden_master.json`.
3.  **Delete:** Delete these 5 rows from the DB.
4.  **Run Import:** Point the tool at the folder containing those 5 MP3s.
5.  **Compare:**
    *   Extract new rows: `SELECT * FROM snDatabase WHERE Title IN (...)`.
    *   Compare `fldDuration`, `fldArtistName`, `fldTitle` against JSON.
    *   **Pass:** if values match exactly (tolerance 0.1s for duration).

---

## 🛠️ Implementation Specs (for Bob)

### Class: `ImportParser`
Located in: `src/services/import_parser.py`

```python
class ImportParser:
    def parse(self, filepath: str, id3_tags: dict = None) -> ImportCandidate:
        """
        Pure logic. No DB access.
        
        Args:
            filepath: Full path or filename.
            id3_tags: Dict from media_service.read_tags().
            
        Returns:
            ImportCandidate object (dataclass) with:
            - artist: str
            - title: str
            - confidence: float (0.0 to 1.0)
            - source: str ('filename' or 'id3')
        """
        pass
```

### Class: `ImportService`
Located in: `src/services/import_service.py`

```python
class ImportService:
    def preview_import(self, file_paths: List[str]) -> List[ImportResult]:
        """
        Dry-run. Checks DB for duplicates.
        Returns list of results with status: 'NEW', 'DUPLICATE', 'CONFLICT'.
        """
        pass

    def execute_import(self, candidates: List[ImportCandidate]) -> ImportSummary:
        """
        The dangerous one. Writes to DB.
        Must use transactions if possible.
        """
        pass
```

---

## 📝 User Stories / Checklist

- [ ] **As a user**, I want to see a list of files that are on disk but not in the DB.
- [ ] **As a user**, I want to see how the system interprets `Filename.mp3` before I click Import.
- [ ] **As a user**, I want to bulk-import 100 files safely.
- [ ] **As a developer**, I want to ensure `AC/DC` doesn't become `AC_DC` or `Ac Dc`.

---

## 📅 Next Session Goal
1.  Initialize `test_import_parser.py`.
2.  Implement `ImportParser` class.
3.  Verify filename parsing logic with 20+ weird examples.
4.  **NO DATABASE WRITES YET.**



## 🔤 Normalization Rules

### For Duplicate Detection (comparing parsed values to DB)
- Case-insensitive: `CHER` == `Cher` == `cher`
- Trim whitespace: `" Cher "` → `Cher`
- (Optional) Collapse multiple spaces: `"Cher  -  Believe"` → `"Cher - Believe"`

### Characters NOT normalized (preserve as-is)
- Hyphens in artist names: `AC-DC` stays `AC-DC`
- Punctuation: `P!nk` stays `P!nk`
- "The" prefix: `The Beatles` stays `The Beatles` (don't strip)