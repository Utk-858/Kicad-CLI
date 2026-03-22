# FluxDiff – Full Project Context

## Project Overview

FluxDiff is a tool for **semantic and visual comparison of KiCad PCB files (`.kicad_pcb`)**.

The goal is to detect **layout, connectivity, and routing differences** between two PCB revisions and present them in both **machine-readable and visual form**.

FluxDiff combines:

- PCB semantic diff engine
- Visual diff generation (OpenCV)
- Interactive viewer
- CLI tool
- GitHub Pull Request automation

The architecture resembles professional PCB review tools used in EDA environments.

---

# Core Features Implemented

## 1. PCB Parsing

PCB files are parsed using a **custom S-expression parser**.

KiCad PCB files are structured as nested S-expressions such as:

```
(footprint
  (at 10 10)
  (fp_text reference "R1")
)
```

The parser converts this structure into Python objects.

### Parsed Data Model

```
PCBData
 ├ components
 ├ nets
 ├ traces
 └ vias
```

### Models

Defined in:

```
fluxdiff/models/pcb_models.py
```

Data classes:

```
Component
Pad
Net
Trace
Via
PCBData
DiffResult
```

---

# 2. Semantic Diff Engine

Located in:

```
fluxdiff/diff/diff_engine.py
```

Compares two `PCBData` objects.

### Detects

Component changes:

- added components
- removed components
- moved components
- rotation changes
- footprint changes
- layer changes
- value changes

Net connectivity:

- pad net changes
- pad disconnections

Routing:

- trace additions
- trace removals
- via additions
- via removals

### Thresholds

```
MOVE_THRESHOLD = 0.05 mm
ROT_THRESHOLD = 1 degree
TRACE_ROUND = 5 decimal precision
```

### Output Structure

```
DiffResult
 ├ component_changes
 ├ net_changes
 └ routing_changes
```

---

# 3. Visual Diff Generation

Located in:

```
fluxdiff/visual/
```

## PCB Export

Uses KiCad CLI to export board images.

```
kicad-cli pcb export svg
```

Images generated:

```
before.png
after.png
```

## Visual Difference

OpenCV computes differences between images.

Generated file:

```
diff_overlay.png
```

This highlights layout changes.

---

# 4. Component Visual Diff

Module:

```
fluxdiff/visual/component_diff.py
```

Purpose:

Draw bounding boxes around moved components.

Expected output:

```
component_diff.png
```

Current status:

Component parsing is incomplete, so component list is empty.

```
Before components: 0
After components: 0
```

Therefore `component_diff.png` is not currently generated.

---

# 5. Web Viewer

Located in:

```
fluxdiff/viewer/server.py
```

Flask-based UI.

Viewer displays:

```
Before board
After board
Diff overlay
```

Recently upgraded to include:

### Interactive Before/After Slider

Users can drag to compare PCB revisions visually.

Runs at:

```
http://localhost:5000
```

---

# 6. CLI Tool

Entry point:

```
fluxdiff/cli/main.py
```

Example usage:

```
python -m fluxdiff.cli.main before.kicad_pcb after.kicad_pcb
```

Launch viewer:

```
python -m fluxdiff.cli.main before.kicad_pcb after.kicad_pcb --viewer
```

---

# 7. Output Files

Generated in:

```
output/
```

Files:

```
before.png
after.png
diff_overlay.png
component_diff.png (not yet working)
diff_report.txt
```

Example report:

```
PCB DIFF REPORT

=== COMPONENT CHANGES ===
Component R1 moved

=== NET CHANGES ===
Pad R2 changed from GND -> VCC

=== ROUTING CHANGES ===
Trace added
Via removed
```

---

# 8. GitHub Integration

Workflow file:

```
.github/workflows/pcb-diff.yml
```

Triggers when a Pull Request modifies:

```
*.kicad_pcb
```

### Workflow Steps

1. checkout repository
2. install Python
3. install dependencies
4. install KiCad CLI
5. run FluxDiff
6. upload artifacts
7. post PR comment

### Artifacts Uploaded

```
pcb-diff
 ├ before.png
 ├ after.png
 ├ diff_overlay.png
 └ diff_report.txt
```

### PR Comment

```
FluxDiff PCB Analysis

PCB layout changes detected.

Download visual diff artifacts from this workflow run.
```

---

# Project Structure

```
fluxdiff/
│
├ cli/
│  └ main.py
│
├ diff/
│  └ diff_engine.py
│
├ models/
│  └ pcb_models.py
│
├ parser/
│  ├ pcb_parser.py
│  └ sexp_parser.py
│
├ visual/
│  ├ image_diff.py
│  ├ component_diff.py
│  └ kicad_export.py
│
├ viewer/
│  └ server.py
│
 test_boards/
 output/
 docs/
 .github/workflows/
```

---

# Environment Setup

Python version:

```
Python 3.10+
```

Install dependencies:

```
pip install opencv-python numpy pillow click flask
```

or

```
pip install -r requirements.txt
```

---

# System Requirements

KiCad CLI must be installed.

Mac example path:

```
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
```

Verify installation:

```
kicad-cli --version
```

---

# Example Run

```
python -m fluxdiff.cli.main test_boards/before.kicad_pcb test_boards/after.kicad_pcb --viewer
```

Console output:

```
Visual diff generated: output/diff_overlay.png
Diff report written to: output/diff_report.txt
```

Viewer:

```
http://localhost:5000
```

---

# Known Limitations

### Component Parsing Issue

Current parser does not correctly extract components from S-expression tree.

Debug output:

```
Before components: 0
After components: 0
```

Needs improvement in:

```
parser/sexp_parser.py
parser/pcb_parser.py
```

This affects:

```
component_diff.png
```

---

# Future Improvements

Parser Improvements

- fix component extraction

Bounding Box Detection

- detect real component footprint area

Net Graph Analysis

- compare electrical connectivity

Multi-layer Routing Diff

- layer specific diffing

GitHub PR Image Preview

- embed diff image in PR comments

Viewer Improvements

- zoom
- pan
- highlight changed areas

---

# Current Development State

The system currently supports:

- PCB semantic diff
- visual OpenCV diff
- CLI execution
- interactive web viewer
- GitHub CI automation

Component-level highlighting is pending parser improvements.

---

# Developer

Utkarsh Bansal

MERN stack developer building Mentox and exploring hardware tooling.

---

# Instructions for Next Chat

Continue development of FluxDiff.

Immediate priorities:

1. Fix component parsing so components list is populated.
2. Enable generation of component_diff.png.
3. Improve viewer visualization if needed.

All other systems are functional.


---

# ARCHITECTURE.md

## High Level Architecture

FluxDiff is organized as a modular pipeline that converts KiCad PCB files into structured data, compares them semantically, and produces visual and textual diff outputs.

```
KiCad PCB (.kicad_pcb)
        │
        ▼
S‑Expression Parser
(parser/sexp_parser.py)
        │
        ▼
PCB Parser
(parser/pcb_parser.py)
        │
        ▼
PCBData Model
(models/pcb_models.py)
        │
        ▼
Diff Engine
(diff/diff_engine.py)
        │
        ▼
Visual Generators
(visual/)
        │
        ├── image_diff.py
        ├── component_diff.py
        └── kicad_export.py
        │
        ▼
Outputs
(before.png, after.png, diff_overlay.png, diff_report.txt)
        │
        ▼
Viewer
(viewer/server.py)
        │
        ▼
GitHub Automation
(.github/workflows/pcb-diff.yml)
```

---

## Module Responsibilities

### parser/
Responsible for converting KiCad S‑expression files into structured Python objects.

Components:

- sexp_parser.py → generic S‑expression tree parser
- pcb_parser.py → extracts components, nets, traces, vias

Output:

```
PCBData
```

---

### models/
Defines all data structures used across the system.

Important classes:

```
Component
Pad
Net
Trace
Via
PCBData
DiffResult
```

These models decouple parsing from diff logic.

---

### diff/
Contains semantic comparison logic.

Main file:

```
diff_engine.py
```

Responsibilities:

- detect component movement
- detect value / footprint changes
- detect routing differences
- detect net connectivity changes

Output:

```
DiffResult
```

---

### visual/
Responsible for generating visual representations.

Modules:

image_diff.py

- compares rendered board images using OpenCV

component_diff.py

- highlights moved components

kicad_export.py

- exports board images using KiCad CLI

---

### viewer/
Contains the Flask web viewer.

Features:

- display before board
- display after board
- show diff overlay
- interactive slider comparison

Server file:

```
viewer/server.py
```

---

### cli/
Entry point for the application.

```
cli/main.py
```

Responsibilities:

- orchestrate full pipeline
- run parser
- run diff engine
- generate images
- optionally launch viewer

---

### GitHub Integration

Workflow file:

```
.github/workflows/pcb-diff.yml
```

Responsibilities:

- detect PCB file changes in PR
- run FluxDiff
- upload artifacts
- comment on pull request

---

# DEV_ROADMAP.md

## Phase 1 – MVP (Completed)

Features implemented:

- S‑expression PCB parser
- semantic diff engine
- visual OpenCV diff
- CLI tool
- Flask viewer
- GitHub PR automation

This phase produces:

```
before.png
after.png
diff_overlay.png
diff_report.txt
```

---

## Phase 2 – Parser Improvements

Goals:

- fix component extraction
- ensure components list is populated
- enable component_diff.png generation

Tasks:

1. inspect S‑expression AST output
2. update pcb_parser extraction rules
3. support KiCad module + footprint formats

Expected result:

```
component_diff.png
```

---

## Phase 3 – Component Visual Highlighting

Enhancements:

- compute component bounding boxes
- draw accurate highlight regions
- label components with reference IDs

Potential improvements:

- footprint size estimation
- orientation-aware boxes

---

## Phase 4 – Connectivity Analysis

Implement electrical connectivity graph.

Steps:

1. build net graph
2. compare connectivity graphs
3. detect logical circuit changes

This enables detection of:

- broken connections
- unintended shorts
- topology changes

---

## Phase 5 – Multi-Layer Routing Diff

Enhancements:

- analyze copper layers independently
- detect layer-specific routing changes

Features:

- per-layer diff views
- layer toggles in viewer

---

## Phase 6 – Viewer Improvements

Planned features:

- zoom and pan
- component click highlighting
- routing path visualization
- layer toggling

UI inspiration:

- GitHub image comparison
- PCB review tools

---

## Phase 7 – Advanced GitHub Integration

Future improvements:

- embed diff images directly in PR comments
- auto-detect old vs new PCB revisions
- multi-file PCB diff support

Example PR comment:

```
FluxDiff PCB Analysis

Components changed: 2
Routing changes: 5
Net changes: 1
```

---

## Phase 8 – Production Hardening

Long-term goals:

- packaging as pip module
- Docker container
- scalable CI usage

Potential CLI install:

```
pip install fluxdiff
fluxdiff before.kicad_pcb after.kicad_pcb
```

---

## Phase 9 – Long-Term Vision

Transform FluxDiff into a full **hardware code review tool**.

Possible capabilities:

- schematic diff
- PCB layout diff
- design rule comparison
- manufacturing change detection

Target users:

- hardware teams
- PCB designers
- open hardware projects

---

## Immediate Next Task

Fix component parsing so the system produces:

```
component_diff.png
```

Once parser works, the entire pipeline becomes fully functional.

