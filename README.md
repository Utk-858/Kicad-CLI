# 🏗️ FluxDiff: Semantic & Visual KiCad PCB Review

FluxDiff is a next-generation tool for **semantic and visual comparison** of KiCad PCB files (`.kicad_pcb`). It bridges the gap between raw S-expression noise and meaningful hardware review by providing structured reports, pixel-perfect overlays, and LLM-powered insights.

---

## 🚀 Key Features

### 1. Semantic Diff Engine
- **Component Matching**: Matches components via UUID first (stable across re-annotations) and falls back to Ref.
- **Attribute Detection**: Highlights movements (within 0.05mm), rotations, value changes, and footprint swaps.
- **Net & Connectivity**: Analyzes pad-to-net mapping and detects broken connections or unintended shorts.
- **Routing Analysis**: Detailed set-diff for traces and vias, including snapping logic to nearest pads.

### 2. Visual Diff Suite
- **Pixel Overlay**: Generates a composite image highlighting even the smallest layout shifts using OpenCV.
- **Component Highlighting**: Annotated overlays showing added (green), removed (red), and moved (yellow) components.
- **SVG to PNG Pipeline**: Uses `kicad-cli` and `cairosvg` for high-fidelity board renders.

### 3. Fabrication & Supply Chain
- **BOM Generator**: Automatically groups components by value and footprint. Cleans footprint metadata for fabrication readiness.
- **ERP Simulation**: Integrated supply chain checker that simulates stock availability (OK, WARNING, CRITICAL) for your BOM.

### 4. FluxDiff RAG (AI Chat)
- **Repo-Aware Chat**: Leveraging FAISS and OpenAI to provide a chat interface that understands your board's commit history.
- **Interactive Insights**: Ask the AI things like *"What changed in the power section between the last two commits?"* or *"Why was R105 moved?"*

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Click (CLI), Flask (Viewer), FastAPI (RAG API).
- **Computer Vision**: OpenCV, NumPy.
- **Hardware Parsing**: Custom S-expression AST parser.
- **AI/RAG**: OpenAI (GPT-4o-mini), FAISS, LlamaIndex-inspired orchestration.
- **External Tools**: `kicad-cli` (v6+), `cairosvg`.

---

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fluxdiff/fluxdiff.git
   cd fluxdiff
   ```

2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install KiCad**: Ensure `kicad-cli` is in your PATH.

---

## 🖥️ Usage

### 1. Basic Semantic + Visual Diff
```bash
python -m fluxdiff.cli.main before.kicad_pcb after.kicad_pcb
```

### 2. Launch Interactive Viewer
```bash
python -m fluxdiff.cli.main before.kicad_pcb after.kicad_pcb --viewer
```

### 3. Run RAG Chat Backend
```bash
export PYTHONPATH=$PYTHONPATH:.
uvicorn fluxdiff.rag.api.server:app --reload --port 8000
```

---

## 📂 File Structure

```
fluxdiff/
├── cli/              # Orchestration entrypoint
├── parser/           # S-expression & PCB domain parsers
├── models/           # PCB Data Models
├── diff/             # Pure semantic diff logic
├── analysis/         # Connectivity graph, ERC, & BOM generator
├── supply_chain/     # ERP simulation & supply checker
├── visual/           # OpenCV image processing & KiCad export
├── viewer/           # Flask-based web viewer
└── rag/              # LLM-powered chat logic
```

---

## 🗺️ Roadmap & Progress

- [x] Semantic Diff Engine (Components, Nets, Traces)
- [x] Visual Overlay Generation
- [x] Interactive Flask Viewer
- [x] Grouped BOM Generator
- [x] Supply Chain / ERP simulation
- [x] RAG Chat System over commit history
- [ ] **In Progress**: Viewer UI Zoom/Pan & Dark Mode
- [ ] **Next**: Board Outline (Edge.Cuts) Diff
- [ ] **Next**: CI-friendly JSON export mode

---

## 📝 License
MIT License. Developed for the next generation of open hardware tooling.

