# TODO - Jazler Database Editor

**Last Updated:** 2025-12-17  
**Tests Passing:** 99/99 ✅

---

## 🚧 In Progress

**Next:**
- [ ] Refactor `save_song` validation logic (High Priority)

---

## 🔴 High Priority

### 1. Extract Validation Logic from `save_song()`
**Status:** ⚠️ Needs Refinement
- ✅ `src/validators/song_validator.py` created
- ✅ `src/validators/validation_result.py` created
- ✅ Tests added (`tests/test_song_validator.py`)
- ⚠️ Validation logic currently inline in `save_song()` (restored for stability)
- [ ] Need to fully migrate to Validator class

---

## 🟡 Medium Priority

### 2. Enhanced Error Log Viewer
**Current:** Basic (shows last 5 errors)  
**Target:** Full-featured table with filters

**Features:**
- Sortable columns (Time, Level, Message)
- Filters (by level, by time)
- Stack trace viewer
- Export to file
- Clear log button

**Files:**
- `src/ui/dialogs/error_log_viewer.py` (~200 lines)
- `tests/test_error_log_viewer.py` (~100 lines)

---

### 3. Field Registry Pattern
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

### 4. Extract Dialogs
**Time:** 4 hours total

**Create:**
- `src/ui/dialogs/database_selector.py` (2h)
- `src/ui/dialogs/query_dialog.py` (2h)

**Benefits:**
- Separation of concerns
- Reusable components
- Easier testing

---

### 5. Magic Numbers - SongColumns Enum
**Current:** 24 separate index constants in Song.py  
**Time:** 2 hours

**Create:**
```python
# src/models/db_schema.py
from enum import IntEnum

class SongColumns(IntEnum):
    ID = 0
    ARTIST_ID = 1
    TITLE = 2
    GENRE_1_ID = 3
    # ... etc
```

**Benefits:**
- Better maintainability
- Type safety
- Self-documenting code

---

### 6. Thread Management - AsyncExecutor
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

### 7. Config Class Enhancement
**Current:** Config mixes file I/O with property access  
**Time:** 3 hours

**Create:**
- `src/core/config_loader.py` - File I/O only
- `src/core/config_validator.py` - Validation logic

**Benefits:**
- Separation of concerns
- Easier testing
- Better validation

---

### 8. Test Organization
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
- Clearer test types
- Easier to run specific test suites

---

## 🟢 Low Priority (Future)

### 9. Break Up DatabaseEditor Class
**Current:** 847 lines, 26 methods  
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

### 10. Specific Documentation Needs
**Time:** 3 hours  
**Target:** Complex methods with business logic

**Priority Methods:**
- `save_song()` - Explain validation flow
- `check_genre()` - Document special rules (e.g., "za obradu" optional)
- `get_expected_path()` - Explain path generation logic
- `process_string_comparison()` - Clarify artist vs standard matching

**General:** Add docstrings to all public methods

---

### 11. Specific Testing Gaps
**Time:** 4 hours  
**Target:** Edge cases and complex logic

**Add Tests For:**
- [ ] Individual validation functions (once extracted)
- [ ] Path validation for different genre rules
- [ ] Artist "startswith" matching logic
- [ ] Genre deduplication and limiting to 3
- [ ] Year = 0 handling
- [ ] File rename operations with rollback
- [ ] Error recovery scenarios

---

### 12. Performance Optimization
**Only if needed:**
- Profile slow operations
- Optimize database queries
- Cache frequently accessed data

---

### 13. Known Issues / Tech Debt

**Track these for future reference:**
1. **God Class:** DatabaseEditor is 887 lines - needs breaking up
2. **Magic Numbers:** 24 database column index constants
3. **Threading:** Thread creation scattered across methods
4. **Config I/O:** Mixed with property access in Config class

---

### 14. Modern Code Practices & Cleanups
**Time:** 4 hours
**Target:** Codebase modernization

**Tasks:**
1. **Layout Constants:** Extract fonts (`("Segoe UI", 9)`) and metrics (`padx=20`) to `Theme` class
2.  **Audio Magic Strings:** Replace `"TPE1"`, `"TIT2"` in `audio.py` with Enum/Constants
3.  **Strict Typing:** Add type hints to UI methods (events) and enable strict mypy mode
4.  **Lambda Refactoring:** Replace complex UI lambdas with named methods for better debugging

---

### 15. UX Polish & Usability
**Time:** 4 hours
**Target:** User Experience Improvement

**Tasks:**
1.  **Tooltips:** Add hover tooltips to copy buttons (`->`, `<-`) and status indicators
2.  **Loading State:** Add `cursor="wait"` and visual indicator during async operations (Query/Load)
3.  **Button Sizing:** Increase hit area for small action buttons (min-width 30px)
4.  **Visual Hierarchy:** Add subtle background distinction between Database (left) and ID3 (right) columns
5.  **Tab Order:** Verify and explicit set logical tab navigation order

**Note:** Items 1-4 are addressed in other TODO sections above

---

## ✅ Completed

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
