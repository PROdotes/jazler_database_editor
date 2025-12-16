# TODO Next

## Immediate Priorities

### 1. Refactor `save_song` Method
**Current State:** 148-line monolithic method with nested validation logic  
**Target:** Break into smaller, testable components

**Proposed Structure:**
```python
# src/validators/song_validator.py
class SongValidator:
    def validate_required_fields(song, id3) -> ValidationResult
    def validate_artist_match(song, id3) -> ValidationResult
    def validate_genres(song, id3, genre_map) -> ValidationResult
    def validate_file_path(song, config) -> ValidationResult
    def validate_all(...) -> ValidationResult
```

**Benefits:**
- Each validation can be tested independently
- Clearer separation of concerns
- Easier to add new validations
- Better error messages

**Files to Create:**
- `src/validators/__init__.py`
- `src/validators/song_validator.py`
- `src/validators/validation_result.py`
- `tests/test_song_validator.py`

---

### 2. Extract Theme Constants
**Current State:** Hard-coded colors scattered throughout `app.py`

**Create:** `src/ui/theme.py`
```python
@dataclass
class Theme:
    BG_DARK = "#2b2b2b"
    BG_LIGHTER = "#3c3f41"
    BG_INPUT = "#3c3f41"
    STATUS_ERROR = "#662222"
    STATUS_SUCCESS = "#28a745"
    STATUS_WARNING = "#fd7e14"
    STATUS_DANGER = "#dc3545"
    FG_WHITE = "#ffffff"
    FG_GRAY = "#6c757d"
    FG_LIGHT_GRAY = "#cccccc"
```

**Impact:** ~20 hard-coded color references in `app.py`

---

### 3. Field Registry Pattern
**Current State:** Field mappings duplicated in multiple places

**Create:** `src/models/field_definition.py`
```python
@dataclass
class FieldDefinition:
    name: str
    db_column: str
    display_name: str
    required: bool = True
    editable: bool = True
    widget_type: str = "entry"

class FieldRegistry:
    FIELDS = [...]
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional[FieldDefinition]
```

**Impact:** Eliminates duplication in `query_execute()`, `update_fields()`, widget creation

---

## Secondary Improvements

### 4. Error Handling Consistency
- Create `src/utils/error_handler.py`
- Replace print statements with proper logging
- Centralize messagebox error displays
- Add error logging to file

### 5. Dependency Injection
**Current:**
```python
self.db = Database(self.file, self.table_name)
```

**Target:**
```python
class DatabaseEditor:
    def __init__(self, database: Database, config: Config):
        self.db = database
        self.config = config
```

**Benefits:** Easier testing with mock dependencies

---

## Testing Gaps

### Add Tests For:
- [ ] Individual validation functions (once extracted)
- [ ] Path validation logic for different genre rules
- [ ] Artist "startswith" matching logic
- [ ] Genre deduplication and limiting to 3
- [ ] Year = 0 handling
- [ ] File rename operations
- [ ] Error recovery scenarios

---

## Documentation Needs

### Add Docstrings To:
- [ ] `save_song()` - explain the validation flow
- [ ] `check_genre()` - document the special rules
- [ ] `get_expected_path()` - explain path generation logic
- [ ] `process_string_comparison()` - clarify artist vs standard matching

---

## Known Issues / Tech Debt

1. **God Class**: `DatabaseEditor` is 847 lines - needs breaking up
2. **Magic Numbers**: Database column indices (24 constants in `Song.py`)
3. **Threading**: Thread creation scattered in `get_song`, `query_button_click`
4. **Config I/O**: Mixed with property access in `Config` class

---

## Completed Today ✅

- [x] Rebranded from "Jazler Database Editor" to "MS Database Sync App"
- [x] Renamed class `JazlerEditor` → `DatabaseEditor`
- [x] Updated all documentation
- [x] Renamed GitHub repository to `ms_database_sync_app`
- [x] All 67 tests passing
- [x] Analyzed `save_song` method complexity

---

## Next Session Goals

**Priority 1:** Extract validation logic from `save_song`  
**Priority 2:** Create theme constants  
**Priority 3:** Add tests for validation logic

**Estimated Time:** 2-3 hours for Priority 1
