## Fluxlink Visual Diff

Fluxlink Visual Diff is a tool for comparing two KiCad PCB layouts. It parses `.kicad_pcb` files, computes a semantic diff (components, nets, routing), generates visual overlays, and optionally opens a browser-based viewer to explore the differences.

### Features

- **Semantic diff**: Detects changes in components, nets, and routing between two PCB revisions.
- **Visual overlays**:
  - `before.png` / `after.png`: Rendered boards.
  - `diff_overlay.png`: Pixel-based visual diff between boards.
  - `component_diff.png`: Highlights added, removed, and moved components.
- **HTML viewer**: Lightweight Flask viewer to inspect all generated images side by side.

## Requirements

- **Python**: 3.10+ (a recent 3.x is recommended)
- **OS**: macOS / Linux (Windows likely works but is not actively tested)
- **Dependencies**: Installed via `pip` from `fluxdiff/requirements.txt`:
  - `opencv-python`
  - `numpy`
  - `pillow`
  - `click`
  - `flask`

You also need KiCad PCB files in the modern `.kicad_pcb` S‑expression format (KiCad 5 or 6+).

## Installation

From the repository root:

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r fluxdiff/requirements.txt
```

Make sure the repository root is on `PYTHONPATH` (running from the root and using `-m` takes care of this).

## Usage

From the repository root, run:

```bash
python -m fluxdiff.cli.main path/to/before.kicad_pcb path/to/after.kicad_pcb
```

To also launch the browser viewer after generating the diff:

```bash
python -m fluxdiff.cli.main path/to/before.kicad_pcb path/to/after.kicad_pcb --viewer
```

### Command-line arguments

- **`before_file`**: Path to the “before” KiCad `.kicad_pcb` file.
- **`after_file`**: Path to the “after” KiCad `.kicad_pcb` file.
- **`--viewer`**: Optional flag. If set, starts a local Flask server and opens the PCB diff viewer in your browser.

Example:

```bash
python -m fluxdiff.cli.main examples/before.kicad_pcb examples/after.kicad_pcb --viewer
```

## Outputs

After running the CLI, an `output/` directory is created (or reused) in the repo root with:

- **`before.png`**: Render of the “before” board.
- **`after.png`**: Render of the “after” board.
- **`diff_overlay.png`**: Visual diff overlay between before/after.
- **`component_diff.png`**: Highlights added (green), removed (red), and moved (yellow) components.
- **`diff_report.txt`**: Text summary including:
  - `=== COMPONENT CHANGES ===`
  - `=== NET CHANGES ===`
  - `=== ROUTING CHANGES ===`
  - A simple summary (counts per category).

## Viewer

If you pass `--viewer`, the CLI starts a local Flask app that:

- Serves the generated images from `output/`.
- Opens `http://localhost:5000` in your browser.
- Shows a layout with:
  - Before PCB
  - After PCB
  - Visual Diff
  - Component Diff

You can also run the viewer directly (after generating images):

```bash
python -m fluxdiff.viewer.server
```

## Project Structure (high level)

- `fluxdiff/cli/main.py` – CLI entrypoint; orchestrates parsing, diffing, image export, and optional viewer.
- `fluxdiff/parser/pcb_parser.py` – Parses KiCad `.kicad_pcb` into internal `PCBData` (components, nets, traces, vias).
- `fluxdiff/visual/component_diff.py` – Generates `component_diff.png`.
- `fluxdiff/viewer/server.py` – Flask server backing the PCB diff viewer.
- `fluxdiff/viewer/static/index.html` – HTML/JS for the richer viewer UI.
- `fluxdiff/requirements.txt` – Python dependency list.

## Limitations / Notes

- Intended for KiCad S‑expression PCB files; other EDA formats are not supported.
- Rendering to PNG relies on external KiCad export logic (`kicad_export`) and may require KiCad CLI/tools to be installed and available.
- This is an early-stage tool; expect rough edges and incomplete coverage of all KiCad features.

