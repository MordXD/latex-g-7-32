# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a ГОСТ 7-32 LaTeX Template and Course Work repository - a Russian academic document generation system that provides both LaTeX templates compliant with GOST 7-32-2017 standards and a web-based editor interface for real-time LaTeX editing.

## Development Commands

### LaTeX Document Compilation
```bash
cd latex/
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Web Application Development
```bash
cd web-app/
pip install -r requirements.txt
python app.py
# Access at http://localhost:5000
```

### Graph Generation
```bash
cd latex/scripts/
python generate_graphs.py
python all_plots.py
python phase_plot.py
```

## Architecture

### LaTeX Document System (`latex/`)
- **Main Entry**: `main.tex` - Primary LaTeX document for electrical engineering coursework
- **Core Class**: `styles/gost-7-32.cls` - Main document class that orchestrates 15 specialized style modules
- **Modular Design**: Each aspect of GOST 7-32-2017 formatting is handled by separate `.sty` files (headings, tables, bibliography, code highlighting, etc.)

### Web Application (`web-app/`)
- **Main Entry**: `app.py` - Flask application with real-time LaTeX compilation
- **Real-time Features**: File monitoring with `watchdog`, WebSocket communication via Flask-SocketIO
- **Compilation Pipeline**: Background `pdflatex` execution with timeout handling and error reporting

### Scientific Computing (`latex/scripts/`)
- Python scripts for generating technical diagrams using matplotlib
- Specialized for electrical engineering coursework (RL circuit analysis, phase diagrams)

## Key Implementation Details

### GOST 7-32 Compliance
The LaTeX system implements Russian GOST 7-32-2017 standards through a modular approach:
- T2A encoding for proper Cyrillic typesetting
- Specialized counters for Russian academic formatting
- Compliant bibliography, table, and figure styling

### Real-time Compilation Architecture
The web app uses:
- `watchdog` to monitor `main.tex` for changes
- Asynchronous LaTeX compilation with timeout protection
- WebSocket updates for compilation status and error reporting
- PDF preview and download functionality

### Entry Points for Common Tasks
- Extend document templates: Modify `latex/styles/gost-7-32.cls`
- Add web features: Enhance `web-app/app.py`
- Create new scientific plots: Extend `latex/scripts/generate_graphs.py`
- Update formatting rules: Edit specific `.sty` files in `latex/styles/`

## Documentation
Comprehensive documentation available in `docs/`:
- `DOCS.md` - Complete GOST 7-32 style guide (420 lines)
- `README.md` - Web application setup and usage
- `README_WEBUI.md` - Web interface instructions