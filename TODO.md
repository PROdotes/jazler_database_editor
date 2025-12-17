# TODO - Jazler Database Editor

**Last Updated:** 2025-12-17  
**Tests Passing:** 100/100 ✅

---

## 🚧 In Progress

**Next:**
(No active tasks)

---

## 🔴 High Priority

(No high priority tasks currently)

---

## 🟡 Medium Priority

### 1. Field Registry Pattern
**Current:** Field mappings duplicated in 3+ places  
**Time:** 4 hours

**Create:**
```python
# src/models/field_definition.py
@dataclass
class FieldDefinition:
    name: str
    db_column: str
    display_name: str
    required: bool = True
    editable: bool = True
```

**Benefits:**
- Single source of truth
- Eliminates duplication
- Easier to add fields

---

### 2. Extract Dialogs
**Time:** 4 hours total

**Create:**
- `src/ui/dialogs/database_selector.py` (2h)
- `src/ui/dialogs/query_dialog.py` (2h)

**Benefits:**
- Separation of concerns
- Reusable components
- Easier testing

---

### 3. Thread Management - AsyncExecutor
**Current:** Threading logic scattered in get_song, query_button_click  
**Time:** 3 hours

**Create:**
```python
# src/utils/async_executor.py
class AsyncExecutor:
    def execute_async(background_task, on_complete, on_error)
```

**Benefits:**
- Centralized threading
- Better error handling
- Separation from UI logic

---

## 🟢 Low Priority (Future)

### 4. Config Class Enhancement
**Current:** Config mixes file I/O with property access (139 lines, manageable)  
**Time:** 3 hours

**Create:**
- `src/core/config_loader.py` - File I/O only
- `src/core/config_validator.py` - Validation logic

**Benefits:**
- Separation of concerns
- Easier testing

---

### 5. Test Organization
**Current:** All tests in root tests/ folder  
**Time:** 2 hours

**Create:**
```
tests/
├── unit/           # Current tests
├── integration/    # End-to-end workflows
├── performance/    # Load and stress tests
└── fixtures/       # Shared test data
```

**Benefits:**
- Better organization
- Easier to run specific test suites

---

### 6. Break Up DatabaseEditor Class
**Current:** 870 lines, 26 methods  
**Time:** 2-3 days  
**Risk:** High - touches entire UI

**Only do if:**
- Planning major new features
- Have time for comprehensive testing

**Approach:** Extract one component at a time
1. Navigation → `NavigationController`
2. Field editing → `FieldEditor`
3. Status indicators → `StatusBar`

---

### 7. Specific Documentation Needs
**Time:** 3 hours  
**Target:** Complex methods with business logic

**Priority Methods:**
- `save_song()` - Explain validation flow
- `check_genre()` - Document special rules (e.g., "za obradu" optional)
- `get_expected_path()` - Explain path generation logic
- `process_string_comparison()` - Clarify artist vs standard matching

**General:** Add docstrings to all public methods

---

### 8. Specific Testing Gaps
**Time:** 3 hours  
**Target:** Edge cases and complex logic

**Add Tests For:**
- [x] Path validation for different genre rules ✅
- [ ] Artist "startswith" matching logic
- [ ] Genre deduplication and limiting to 3
- [ ] Year = 0 handling
- [ ] File rename operations with rollback
- [ ] Error recovery scenarios

---

### 9. Performance Optimization
**Only if needed:**
- Profile slow operations
- Optimize database queries
- Cache frequently accessed data

---

### 10. Known Issues / Tech Debt

**Track these for future reference:**
1. **God Class:** DatabaseEditor is 870 lines - needs breaking up
2. **Magic Numbers:** ✅ Addressed with `SongColumns` IntEnum and `ID3Tags` constants
3. **Threading:** Thread creation scattered across methods
4. **Config I/O:** Mixed with property access in Config class

---

### 11. Modern Code Practices & Cleanups
**Time:** 3 hours
**Target:** Codebase modernization

**Tasks:**
1. **Layout Constants:** Extract fonts (`("Segoe UI", 9)`) and metrics (`padx=20`) to `Theme` class
2. ~~**Audio Magic Strings:** Replace `"TPE1"`, `"TIT2"` in `audio.py` with `ID3Tags` constants~~ ✅ Done
3. **Strict Typing:** Add type hints to UI methods (events) and enable strict mypy mode
4. **Lambda Refactoring:** Replace complex UI lambdas with named methods for better debugging
5. **SongID3 Dataclass:** Refactor `SongID3.__init__` (11 params) to use `@dataclass` or builder pattern

---

### 12. UX Polish & Usability
**Time:** 4 hours
**Target:** User Experience Improvement

**Tasks:**
1. **Tooltips:** Add hover tooltips to copy buttons (`->`, `<-`) and status indicators
2. **Loading State:** Add `cursor="wait"` and visual indicator during async operations
3. **Button Sizing:** Increase hit area for small action buttons (min-width 30px)
4. **Visual Hierarchy:** Add subtle background distinction between Database (left) and ID3 (right) columns
5. **Tab Order:** Verify and explicitly set logical tab navigation order

---

## ⏳ Maybe Add Later

### Enhanced Error Log Viewer
**Current:** Basic version exists (shows last 5 errors)  
**Target:** Full-featured table with filters

**Features:**
- Sortable columns (Time, Level, Message)
- Filters (by level, by time)
- Stack trace viewer
- Export to file
- Clear log button

**Files:**
- `src/ui/dialogs/error_log_viewer.py` (exists, ~200 lines)
- `tests/test_error_log_viewer.py` (not started)

---

## ✅ Completed

### Extract Validation Logic (Dec 17, 2025)
- ✅ Created `src/validators/song_validator.py`
- ✅ Implemented `SongValidator` class with distinct validation rules
- ✅ Added `ValidationResult` for structured error reporting
- ✅ Updated `save_song` to use `SongValidator` exclusively
- ✅ Fixed case-sensitivity bug in Path Validation
- ✅ Removed legacy inline validation from `app.py`
- ✅ Added comprehensive tests (`tests/test_song_validator.py`)

### Theme System (Dec 17, 2025)
- ✅ Created `theme.json` with 13 color categories
- ✅ Created `src/ui/theme.py` Theme class
- ✅ Replaced ~40 hardcoded colors in `app.py`
- ✅ Added 10 comprehensive tests
- ✅ Colors now customizable via JSON

### Config Fallback System
- ✅ Gracefully handles missing config keys
- ✅ Uses defaults for missing values
- ✅ Added comprehensive tests

### Error Handler Foundation
- ✅ Created ErrorHandler class with severity levels
- ✅ JSON Lines logging with rotation
- ✅ Error badge in UI with hover effects
- ✅ 10 new tests, all passing

### Error Handling System (Dec 17, 2025)
- ✅ Implemented centralized ErrorHandler
- ✅ Created Error Log Viewer UI
- ✅ Replaced all legacy Messageboxes and Prints
- ✅ Secured song_rename() against data corruption
- ✅ 100% Test Pass Rate

### Clean Code Quick Wins (Dec 17, 2025)
- ✅ Added `base_songs_path` to config (removed hardcoded `z:\songs\`)
- ✅ Created `src/utils/id3_tags.py` with `ID3Tags` constants
- ✅ Updated `audio.py` and `song.py` to use ID3Tags constants
- ✅ Created `src/models/db_schema.py` with `SongColumns` IntEnum (all 52 columns!)
- ✅ Mapped all database fields from `snDatabase` table
- ✅ All 100 tests passing

