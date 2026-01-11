# 🎯 Gosling2 Phase v0.2: The "Jazler Bridge" Migration & Cleanup Plan

This plan outlines the steps to transform the current `ms_database_sync_app` from a desktop utility into a robust, decoupled data engine that powers the **Gosling2 v0.2** migration and the **Remote Terminal**.

---

## 🛠️ Milestone 1: Technical Decoupling ("The Engine")
*Goal: Turn the codebase into a stateless library that can be used by scripts or services.*

### 1.1 Extract `JazlerEngine` Core
- [ ] **Finalize `src/core/engine.py`**: Ensure it handles all DB and File logic without UI dependencies.
- [ ] **Config Independence**: Allow the engine to take a dictionary or custom path, removing the dependency on a global `config.json`.
- [ ] **Dependency Injection**: Pass connection objects to methods instead of hardcoding `pyodbc.connect` inside classes.

### 1.2 "Jazler-Domain" Package
- [ ] Move `src/models/`, `src/validators/`, and `src/core/` into a structure that can be easily imported into the Gosling2 backend.

---

## 🧹 Milestone 2: The Great Library Cleanup
*Goal: Use our new tools to sanitize the 50k+ song library before migration.*

### 2.1 Finalize the "Investigation" Suite
- [ ] **`tools/audit_offline.py`**: Refine the "Lost & Found" logic to handle the `B:` vs `Z:` drive mapping perfectly.
- [ ] **`tools/schema_prober.py`**: Fully document the purpose of every column in `snDatabase` to ensure no metadata (like "Intro Pos" or "Mix Pos") is lost during migration.

### 2.2 Execution of the "Ghost-Busting"
- [ ] **Identify**: Generate the final list of the ~851 "Ghosted" songs.
- [ ] **Flagging**: Create a script to bulk-update a "Status" field in MS Access (or disable them via `fldEnabled = 0`) to prevent Gosling2 from trying to import broken links.
- [ ] **Path Repair**: Create an "Auto-Mender" script that updates `fldFilename` in Access for the 53k "Moved" songs we found in the logs.

---

## 🚀 Milestone 3: The Microservices Migration
*Goal: Host the "Brain" so Gosling2 can talk to it.*

### 3.1 The "Station-Side Agent" (DB & Media Services)
- [ ] **DB Service**: A FastAPI wrapper running on the ONAIR terminal. It manages the sequential queue for MS Access writes.
- [ ] **Media Service**: Handles ID3 tagging and generates audio previews (128kbps) for remote editing.

### 3.2 The Web Gateway (Snow Day Mode)
- [ ] Create a central orchestrator that Gosling2 uses to "reach back" into the Jazler library.
- [ ] Implement **JWT Security** to ensure only you can trigger library-wide changes remotely.

---

## 📅 Weekend Tasks (Home Edition)
*Since you're at home with the test DB and file logs:*

1.  **Schema Safari**: Use `python tools/probe_schema.py --test` to find where Jazler stores "Last Played" or "Flags" so we can add them to our audit logic.
2.  **Mismatch Resolution**: Look at the `library_investigation_report.txt` and see if the "Moved" songs are actually moved, or if we just need to refine our Path Normalization logic.
3.  **Engine Polish**: I'll help you finish the `JazlerEngine` so it's 100% ready for the v0.2 merge.

---

## 🏆 The End Goal (Gosling2 Integration)
When this project is done, Gosling2 won't need to "know" about MS Access. It will simply call:
`GET StationAgent/songs/migrate?status=cleaned`
And it will receive a perfect, sanitized JSON stream ready for the modern SQL world.
