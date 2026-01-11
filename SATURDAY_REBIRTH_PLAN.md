# ☕ The "Saturday Rebirth" Plan: Jazler Engine 2.0

Good morning! Here is your blueprint for tearing down the prototype and building the modular fortress that will power Gosling2 v0.2. This isn't just a refactor; it's a structural rebirth.

---

## 🏗️ 1. The Architectural Blueprint (Modular/Onion)

We are moving from a single "app" to a layered system. Each layer only knows about the one below it.

### Layer 1: The Domain (The "What")
*   **Directory**: `src/domain/`
*   **Task**: Create pure Python classes that represent your station's world.
*   **The Master Registry**: Instead of just indices, we create a `FieldDefinition` system that knows if a field is a `Path`, `String`, `Integer`, or `Boolean`. This allows for "Auto-Magic" UI generation later.

### Layer 2: Infrastructure (The "How")
*   **Directory**: `src/infrastructure/`
*   **The Repository Pattern**: We build a `SongRepository` that handles the "dirty" work of `pyodbc`. It translates raw MS Access rows into our clean Domain objects.
*   **The Media Handler**: A dedicated service for the `Z:` drive, FFmpeg previews, and ID3 tag logic.

### Layer 3: Application Services (The "Logic")
*   **Directory**: `src/application/`
*   **Task**: This is where you write your "Investigator" logic. 
*   **Example**: `LibraryAuditService.find_ghosts()` – it takes the Repository and the Media Handler and runs the audit we did yesterday, but in a clean, reusable way.

### Layer 4: The Network Interface (The "Bridge")
*   **Directory**: `src/interfaces/api/`
*   **The FastAPI Layer**: We expose all of Layer 3 via a REST API. This is what makes "Snow Day Mode" possible.

---

## 📅 Tomorrow's Execution Checklist

### Phase 1: The New Foundation (09:00 - 11:00)
- [ ] Initialize the new folder structure.
- [ ] Port the **Field Registry** into a data-driven model.
- [ ] Build the first "True" Repository: `SongRepository.get_by_id(auid)`.

### Phase 2: The Headless Heart (11:00 - 14:00)
- [ ] Strip the `AudioMetadata` and `SongValidator` of all global state.
- [ ] Implement the **"Jazler-Context"**: A system that handles the genre/decade/tempo maps once and shares them everywhere.

### Phase 3: The API & The Face (14:00 - 18:00)
- [ ] Launch the **FastAPI dev server**.
- [ ] Create a `GET /songs/{id}` endpoint that returns a beautiful JSON object of everything Jazler knows about that track.
- [ ] **Next.js Hookup**: Initialize the frontend project. We want a simple "Search & Preview" page that talks to the API.

---

## 🚀 Why this works for you:
*   **Zero Feature Creep**: Because the Core is decoupled, you can add an "Auto-Mender" or a "Deep Schema Prober" just by adding a new Application Service. 
*   **Home-Friendly**: You can develop the UI and the API logic at home using your test DB, and then just drop the "Access Infrastructure" layer into the station terminal on Monday. It just works.

---

## 🕷️ Your Secretary's Note
I've attached the photographic proof of Peter Parker reviewing this very plan. Coffee is included. 

**Ready to start the "Great Severing" when you finish that cup?**
