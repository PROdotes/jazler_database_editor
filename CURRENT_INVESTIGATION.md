# Investigation Log: Song Save & Persistence

**Date**: 2026-01-12
**Status**: Paused (User context switching)

## Current Issue
User reported potential inconsistency with Database Persistence during the Duration debugging session. 
- "we need to see why db changes are not being saved"

## State of Components
1. **Schema Aliases**: Fixed (`subcat1` -> `fldCat1b`). Verified working.
2. **Duration Display**: Fixed rounding issue. UI now shows raw float (`215.5704...`).
3. **ID3 Logic**: 
   - Write: Cleared input = `TLEN: 0`.
   - Read: `TLEN: 0` is now ignored, fallback to physical length.
4. **Save Route**: 
   - Indentation bug fixed (Step 1320).
   - Type coercion (FLOAT/DOUBLE) fixed.
   - `fields_to_update` logic seems correct but needs final verification.

## Next Query
When resuming, we must verify:
1. Does changing a DB field (e.g., Title or Duration) persist after reload?
2. Did the user's report of "not saving" stem from the "Ghost Value" confusion, or is there a genuine write failure in `AccessBackend`?

## Debug Scripts
- `debug_song.py` is configured to inspect physical file tags and resolved paths.
