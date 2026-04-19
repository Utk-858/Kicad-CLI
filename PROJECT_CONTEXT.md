# 🏗️ Project Context: FluxDiff

## 1. High-Level Mission

- **The Problem:** KiCad PCB designers have no semantic diff tool. `git diff` on `.kicad_pcb` files produces unreadable S-expression noise. Engineers can't quickly tell what actually changed between two board revisions — which components moved, which nets rewired, which traces were added.
- **The Goal (MVP Definition of Done):** Given two `.kicad_pcb` files, FluxDiff produces: (1) a human-readable semantic diff report (components, nets, routing), (2) visual PNG overlays highlighting pixel-level and component-level changes, and (3) an optional local web viewer for browsing results interactively.
- **The User:** Hardware/PCB engineers doing design reviews, running CI on board files, or auditing changes before manufacturing handoff.

---

## 2. The Tech Stack

| Layer | Technology |
| :--- | :--- |
| CLI entrypoint | Python + Click |
| PCB parsing | Custom S-expression parser (`sexp_parser.py`) |
| Diff engine | Pure Python (set/dict comparisons) |
| Visual export | `kicad-cli` (SVG) → `cairosvg` (PNG) |
| Image diffing | OpenCV (`cv2`) + NumPy |
| Connectivity analysis | Custom graph builder |
| Web viewer | Flask + Jinja2 (rendered HTML string) |
| Viewer frontend | Vanilla JS + CSS (no framework) |
| BOM Generator | Pure Python (grouping logic) |
| Supply Chain | Simulated ERP Service |

**External tools required at runtime:** `kicad-cli` (must be on PATH), `cairosvg`, `opencv-python`, `flask`, `click`.

| RAG Layer | Technology |
| :--- | :--- |
| LLM Orchestration | LlamaIndex / Custom ChatEngine |
| Vector Database | FAISS (local index) |
| Embeddings | OpenAI (`text-embedding-3-small`) |
| API Framework | FastAPI |
| Git Integration | GitPython / Subprocess |


---

## 3. Core Architecture & Mental Model

### Data Flow

```
.kicad_pcb file
    → sexp_parser.parse_sexp()          # Raw S-expression → Node AST
    → pcb_parser.parse_pcb()            # AST → PCBData (components, nets, traces, vias)
    → diff_engine.compare_pcbs()        # PCBData × 2 → DiffResult
        ├── component_diff()            # UUID-first matching, then attribute comparison
        ├── net_diff()                  # Pad→net mapping changes
        ├── routing_diff()              # Trace/via set diff
        ├── enrich_traces_with_connectivity()  # Snap trace endpoints to nearest pad
        ├── build_connectivity_graph()  # net → {(ref, pad)} graph
        ├── compare_connectivity()      # Graph delta messages
        └── run_erc_checks()            # Basic ERC on new graph
    → export_pcb_png()                  # kicad-cli SVG → cairosvg PNG
    → generate_visual_diff()            # Pixel-level before/after overlay
    → generate_component_visual_diff()  # Component-annotated overlay
    → diff_report.txt + output PNGs
    → (optional) Flask viewer server

### RAG Data Flow (Knowledge Acquisition)

```
Git Commit History
    → GitLoader.get_commits()           # Fetch commit hashes & metadata
    → DiffGenerator.generate_diff()     # For each pair: git show → temp file → FluxDiff CLI
    → DocumentBuilder.build()           # DiffSummary + CommitInfo → RAGDocument
    → EmbeddingClient.get_embeddings()  # OpenAI API
    → FAISS.add_documents()             # Update local vector index in rag_db/
```

### RAG Query Flow (Conversation)

```
User Query
    → ChatEngine.ask()
        → Retriever.retrieve()          # Similarity search in FAISS
        → ChatMemory.get_context()      # Fetch session history
        → build_rag_prompt()            # Inject context + history into template
        → LLMClient.generate()          # OpenAI (gpt-4o-mini)
    → ChatResponse (Answer + Sources)
```

```

### Key Entities

```python
# All defined in fluxdiff/models/pcb_models.py

PCBData         # Top-level container: components, nets, traces, vias
Component       # ref, value, footprint, x, y, rotation, layer, pads[], uuid
Pad             # number (string), net (string name)
Net             # net_id (int), name (string)
Trace           # layer, start (x,y), end (x,y), net; + enriched: start_ref/pad, end_ref/pad
Via             # x, y, net
DiffResult      # component_changes[], net_changes[], routing_changes[], summary
```

### State Management

- **No persistent state.** Every run is stateless; all data lives in Python objects for the duration of one CLI invocation.
- **Output directory `./output/`** is the only side effect: PNGs and `diff_report.txt` written there.
- **Flask viewer** stores `DiffResult` in `app.config["DIFF_RESULT"]` (thread-safe); it is never written to disk.

### Coordinate System

- KiCad uses **millimetres** for all positions.
- PNG pixels are produced by `kicad-cli` SVG at 96 DPI, then `cairosvg` at `scale=4.0`.
- The exact conversion used in `component_diff.py`: `PIXELS_PER_MM = (96 / 25.4) * 4.0 ≈ 15.118`
- **All geometry comparisons happen in mm.** Never compare raw pixel values to component coordinates.

---

## 4. Code Standards & Patterns

### Module Responsibilities (strict separation)

| Module | Responsibility |
| :--- | :--- |
| `parser/sexp_parser.py` | Tokenise + parse S-expressions into `Node` AST. No PCB logic. |
| `parser/pcb_parser.py` | Walk AST, extract PCB domain objects. No diff logic. |
| `models/pcb_models.py` | Pure dataclasses. No methods, no business logic. |
| `diff/diff_engine.py` | All diffing. No I/O, no image ops. Returns `DiffResult`. |
| `analysis/` | Connectivity graph, ERC checks, trace enrichment, geometry utilities. |
| `visual/` | Image export and overlay generation. No diff logic. |
| `viewer/server.py` | Flask app. Reads `DiffResult` from `app.config`. No diff logic. |
| `analysis/bom_generator.py` | Generates grouped Bill of Materials from PCB components. |
| `cli/main.py` | Orchestration only. Calls all other modules in sequence. |

### Component Identity: UUID First

- KiCad footprints have a `uuid` field. **Always use UUID as the primary identity key** when matching components across before/after boards.
- Ref-based matching is a fallback only (for old boards without UUIDs).
- If one board has UUIDs and the other does not, emit a `[WARNING]` and fall back to ref matching for both.
- Duplicate refs (KiCad annotation errors) are **not dropped** — both are included, disambiguated by UUID suffix in output labels.

### Error Handling

- All image export steps are wrapped in `try/except` in `cli/main.py`. A failed image export logs `[WARNING]` and skips visual diff steps; the semantic diff always runs.
- `kicad_export.py` raises `RuntimeError` immediately on any failure — never silently continues with a corrupt/empty PNG.
- `sexp_parser.py` raises `ValueError` on malformed S-expressions (unclosed parens, unexpected `)`) — never returns partial trees.
- Use `[WARNING]`, `[INFO]`, `[ERROR]` prefixes on all print statements for machine-parseable log levels.

### Naming Conventions

- Diff message strings follow a strict prefix pattern: `"Component added:"`, `"Component removed:"`, `"Component moved:"`, `"CRITICAL:"`, `"WARNING:"`, `"INFO:"`, `"CONNECTIVITY:"`, `"ERC:"`. Do not invent new prefixes.
- Internal helper functions are prefixed with `_` (e.g., `_build_component_map`, `_label`, `_pos_equal`).

### Thresholds (defined at top of `diff_engine.py`)

```python
MOVE_THRESHOLD = 0.05   # mm — minimum displacement to report a component as moved
ROT_THRESHOLD  = 1.0    # degrees — minimum rotation delta to report
TRACE_ROUND    = 5      # decimal places for trace coordinate hashing
```

```python
TOLERANCE = 0.8  # mm (geometry.py) — snap radius for trace endpoint → pad matching
```

---

## 5. File & Folder Map

```
fluxdiff/
├── cli/
│   └── main.py              # Click CLI entrypoint; orchestrates everything
├── models/
│   └── pcb_models.py        # All dataclasses: PCBData, Component, Trace, Via, Net, DiffResult
├── parser/
│   ├── sexp_parser.py       # S-expression tokeniser/parser → Node AST
│   └── pcb_parser.py        # AST → PCBData domain objects
├── diff/
│   └── diff_engine.py       # compare_pcbs() and all sub-diff functions
├── analysis/
│   ├── bom_generator.py       # Grouped BOM (value, footprint) generation
│   ├── connectivity_graph.py  # build_connectivity_graph(), compare_connectivity()
├── supply_chain/
│   ├── erp_service.py         # Simulated ERP stock fetching
│   ├── supply_checker.py      # BOM vs ERP stock analysis
│   ├── erc_checker.py         # run_erc_checks() — basic ERC rules
│   ├── geometry.py            # distance(), build_pad_index(), find_nearest_pad()
│   └── trace_connectivity.py  # enrich_traces_with_connectivity()
├── visual/
│   ├── kicad_export.py        # kicad-cli + cairosvg → PNG
│   ├── image_diff.py          # Pixel-level before/after overlay
│   └── component_diff.py      # Component-annotated visual overlay
└── viewer/
    diff_report.txt
├── fluxdiff/rag/            # LLM-powered insights system
│   ├── api/                 # FastAPI server (server.py)
│   ├── chat/                # Conversation logic (chat_engine.py, memory.py)
│   ├── ingest/              # Repository indexing logic (git_loader.py, diff_generator.py)
│   ├── llm/                 # OpenAI client wrappers
│   ├── retrieval/           # Vector search logic
│   └── schemas.py           # RAG-specific Pydantic/dataclass models
└── rag_db/                  # Local FAISS vector storage (gitignored)
```

---

## 6. Critical Business Logic (The "Gotchas")

- **`REF**` is not a real ref.** Footprints with `ref == "REF**"` have not been annotated in KiCad. They are silently skipped in all component maps, net maps, and visual overlays. If ALL components have `REF**`, the tool warns the user and skips component/net diff (routing diff still runs).

- **UUID matching survives re-annotation.** If R5 is renamed to R6 between revisions but its UUID is unchanged, the diff engine correctly reports `"Component re-annotated: R5 -> R6"` rather than a spurious remove+add pair. This only works when matching by UUID.

- **Trace snapping uses net-filtered geometry.** `find_nearest_pad()` only considers pads on the same net as the trace. Without this filter, traces routed near pads of different nets produce phantom connectivity entries. Do not remove the `net=trace.net` argument.

- **Visual diff pixel coordinates use the exact scale factor.** `PIXELS_PER_MM = (96 / 25.4) * 4.0` in `component_diff.py` must match the `scale=4.0` argument passed to `cairosvg.svg2png()` in `kicad_export.py`. Changing either without the other will misalign all component markers on the visual overlay.

- **Flask `app.config` is the only safe place for diff state.** Never store `DiffResult` in a module-level global in `server.py` — it is not thread-safe. Always use `app.config["DIFF_RESULT"]`.

- **Swap detection is mutual.** Two components are reported as a swap only if A moved to B's old position AND B moved to A's old position (within `MOVE_THRESHOLD`). Swapped components are excluded from per-attribute modified checks to avoid double-reporting.

- **ERC deduplication is set-based.** `run_erc_checks()` returns a list; the diff engine takes the set difference `erc_new - erc_old` so only *newly introduced* ERC issues are reported. Pre-existing ERC issues are ignored.

---

## 7. Internal API Routes

| Route | Method | Purpose | Response |
| :--- | :--- | :--- | :--- |
| `/` | GET | HTML viewer page | Rendered HTML with image list |
| `/api/diff` | GET | Structured diff data | `{ components[], nets[], routing[], summary }` |
| `/api/bom` | GET | Grouped BOM data | `[ { value, footprint, count, refs[] } ]` |
| `/images/<filename>` | GET | Serve output PNGs | PNG file from `./output/` |

### FluxDiff RAG API (Port 8000)

| Route | Method | Purpose | Payload |
| :--- | :--- | :--- | :--- |
| `/chat` | POST | Conversational AI | `{ "query": "..." }` |


---

## 8. Anti-Patterns — Do NOT Do These

- **Do NOT** use `ref` as the primary component identity key when UUIDs are available. Refs change on re-annotation; UUIDs are stable.
- **Do NOT** drop duplicate-ref components. Warn, but include both (keyed by UUID).
- **Do NOT** call `cv2.imwrite` without checking the return value or verifying the file exists and is non-empty afterward.
- **Do NOT** snap trace endpoints to pads on different nets (`find_nearest_pad` must always receive `net=trace.net`).
- **Do NOT** store mutable state at module level in `server.py`. Use `app.config`.
- **Do NOT** continue the visual diff pipeline after a PNG export failure — raise immediately so the caller can catch and warn.
- **Do NOT** add a `"CONNECTIVITY:"` prefix inside `compare_connectivity()` — the caller in `diff_engine.py` adds it via f-string.
- **Do NOT** use `WidthType.PERCENTAGE` in any future docx output (breaks Google Docs).
- **Do NOT** invent new diff message prefixes beyond the established set (`CRITICAL`, `WARNING`, `INFO`, `CONNECTIVITY`, `ERC`).

---

## 9. Current Progress & Roadmap

- ✅ **S-expression parser** — robust tokeniser/parser with malformed-input error handling
- ✅ **PCB parser** — extracts components (with UUID), nets, traces, vias, pads
- ✅ **Semantic diff engine** — component, net, routing, swap detection, re-annotation detection
- ✅ **Connectivity graph + ERC** — net-level graph diff and basic electrical rule checks
- ✅ **Visual diff pipeline** — kicad-cli → cairosvg → OpenCV pixel overlay + component overlay
- ✅ **BOM Generator** — Automatic grouping of components by value/footprint for fabrication
- ✅ **Flask web viewer** — image display + JSON diff API + interactive JS panel
- ✅ **FluxDiff RAG** — Commit-based indexing, FAISS retrieval, and FastAPI chat interface

- 🚧 **In Progress:** Viewer UX polish — zoom/pan JS (`pcb_zoom_pan.js`), panel toggle buttons (HTML template in `server.py`), dark-mode grid layout
- 🚧 **In Progress (RAG):** Automated incremental indexing on new commits; source-tracking UI in frontend

- 📋 **Next Up:**
  - Pad-level position offsets (currently pads are approximated at component origin; KiCad exposes real pad offsets in the S-expression)
  - Board outline / Edge.Cuts diff
  - CI-friendly JSON output mode (`--format json`)
  - Configurable layer selection for `kicad-cli` export