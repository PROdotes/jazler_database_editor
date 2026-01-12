# Investigation Log: Song Save & Persistence

**Date**: 2026-01-12
**Status**: Completed

## Final Resolution
The reported "data not saving" issue was confirmed to be an **Environment Mismatch**:
- The editor was connected to `jazler_test` (Test DB).
- Use was likely verifying against `jazler_live` (Live DB) in the RadioStar software.

## Verification Steps
1. **Peristence Test**: Programmatic updates (`repro_persistence.py`) confirmed data persists in Access DB.
2. **Live Test**: Successfully wrote changes to the Live DB via the Offline/Sync workflow.
3. **Safety Nets Implemented**:
   - **Config Driven**: App now respects `active_database` from `connections.json` (was hardcoded to test).
   - **Undo Drafts**: Syncing changes now auto-creates a "Reverse Draft" to allow quick undo.
   - **Type Safety**: Patched boolean string handling (`'on'` -> `True`) in sync logic.

## Next Actions
- Resume normal development.
- Ensure `connections.json` is set to user's desired environment (reverted to `jazler_test`).
