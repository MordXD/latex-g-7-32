# ГОСТ 7-32 LaTeX Document Generator with FastAPI + OpenWebUI

Modern Docker-based infrastructure for generating PDF documents using LaTeX templates with GOST 7-32 standards. Features FastAPI backend and OpenWebUI frontend for seamless document creation and editing.

## 🏗️ Architecture

### 🚀 Modern Stack
- **Backend**: FastAPI with Poetry + Docker
- **Frontend**: OpenWebUI (Chat-based interface)
- **Compilation**: pdflatex with full TeX Live
- **Storage**: Docker volumes for PDFs and logs
- **Communication**: REST API + WebSocket for real-time updates

### 🐳 Docker Services
- `backend`: FastAPI service for LaTeX compilation
- `openwebui`: Web interface for document generation
- `nginx`: Reverse proxy (production mode)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ available disk space (for TeX Live)

### 1. Start Services
```bash
# Production mode
docker compose up --build

# Development mode (with live reload)
docker compose -f docker-compose.dev.yml up --build
```

### 2. Access Services
- **OpenWebUI**: http://localhost:3000
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Generate Your First Document
1. Open http://localhost:3000
2. Use the LaTeX Compiler Tool in the chat interface
3. Try: **"Show me available LaTeX templates"**
4. Then: **"Compile the main template"**

## 📁 Project Structure

```
├── backend/                   # FastAPI application
│   └── app/
│       ├── main.py           # FastAPI app entry point
│       ├── routers/          # API routes
│       ├── services/         # Business logic
│       └── models/           # Pydantic models
├── latex/                     # LaTeX templates & styles
│   ├── styles/               # ГОСТ 7-32 styling
│   ├── images/               # Document images
│   └── main.tex              # Main template
├── plugins/                   # OpenWebUI custom tools
│   └── latex_compiler.py     # LaTeX compilation tool
├── pdf/                       # Generated PDFs (volume)
├── logs/                      # Application logs (volume)
├── docker-compose.yml         # Production Docker setup
├── docker-compose.dev.yml     # Development setup
├── Dockerfile                 # Backend container
├── pyproject.toml            # Poetry configuration
└── .env                      # Environment variables
```

## 🛠️ API Usage

### REST API Endpoints

#### Compile LaTeX Document
```bash
curl -X POST "http://localhost:8000/api/compile" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "\\documentclass[14pt]{styles/gost-7-32}\n\\begin{document}\nHello World\n\\end{document}"
  }'
```

#### Get Available Templates
```bash
curl "http://localhost:8000/api/templates"
```

#### Download Compiled PDF
```bash
curl "http://localhost:8000/api/download/{compilation_id}/pdf" \
  --output document.pdf
```

### WebSocket Real-time Compilation
```javascript
// Connect to WebSocket for live compilation updates
const ws = new WebSocket('ws://localhost:8000/ws/compile');

// Send compilation request
ws.send(JSON.stringify({
  type: 'compile',
  content: '\\documentclass[14pt]{styles/gost-7-32}...'
}));

// Receive progress updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Compilation progress:', data);
};
```

## 🎯 OpenWebUI Integration

### Available Tools in Chat

#### 1. Compile LaTeX Content
```
User: "Compile this LaTeX document for me:
\documentclass[14pt]{styles/gost-7-32}
\begin{document}
Это тестовый документ ГОСТ 7-32
\end{document}"

Assistant: ✅ Document compiled successfully!
📥 Download: http://localhost:8000/pdf/xyz123.pdf
⏱️ Compilation time: 2.1 seconds
```

#### 2. List Templates
```
User: "Show me available LaTeX templates"

Assistant: 📄 Found 3 LaTeX templates:
• main (main.tex) - Main coursework template
• report (report.tex) - Report template
• thesis (thesis.tex) - Thesis template
```

#### 3. Compile with Customizations
```
User: "Compile the main template, replace 'Студент' with 'Иванов Иван'"

Assistant: ✅ Template compiled with customizations!
📥 Download: http://localhost:8000/pdf/abc456.pdf
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# FastAPI Settings
HOST=0.0.0.0
PORT=8000
DEBUG=true

# LaTeX Settings
LATEX_TIMEOUT=60
LATEX_OUTPUT_DIR=pdf
LATEX_WORK_DIR=latex

# CORS Settings
CORS_ORIGINS=["http://localhost:3000", "http://openwebui:3000"]

# Logging
LOG_LEVEL=INFO
```

### Custom LaTeX Templates
Add new templates to `latex/` directory:
```bash
# Add new template
cp latex/main.tex latex/my_template.tex
# Edit template content
# Template automatically available via API
```

## 📋 GOST 7-32 LaTeX Templates

The project includes comprehensive templates for academic and technical documents:

### Included Templates
- **main.tex** - Electrical engineering coursework with calculations
- **Report templates** - Academic reports following GOST standards
- **Thesis templates** - Diploma and thesis documents

### Electric Engineering Coursework Content
The included coursework covers:

#### Task 1: DC Circuit Analysis
- Kirchhoff's laws method
- Mesh current analysis
- Nodal analysis
- Two-node method
- Superposition principle
- Thevenin/Norton equivalent
- Power balance calculations

#### Task 2: AC Circuit Analysis
- Complex Kirchhoff's laws
- AC mesh analysis
- AC nodal analysis
- Complex superposition
- Frequency response analysis
- Vector diagrams
- Power calculations

### 🛠 GOST 7-32 Features
- Full compliance with ГОСТ 7-32-2017 standards
- Modular styling system
- Cyrillic text support
- Automatic numbering for sections, formulas, figures
- Proper bibliography formatting
- Technical symbol and formula support

## 📊 Graph Generation

Python scripts in `latex/scripts/` for technical diagrams:
- `generate_graphs.py` - Primary graph generation
- `all_plots.py` - Additional plots
- `phase_plot.py` - Phase diagrams

## 🐳 Advanced Docker Operations

### Production Deployment
```bash
# Minimize image size using multi-stage builds
docker compose -f docker-compose.yml --profile production up --build

# Scale services
docker compose up --scale backend=3 --scale openwebui=2

# healthcheck status
docker compose ps
```

### Debugging
```bash
# View backend logs
docker compose logs -f backend

# Access container shell
docker compose exec backend bash

# Test LaTeX compilation
docker compose exec backend pdflatex --version
```

### Environment Customization
```bash
# Custom ports
PORT=8080 docker compose up

# Custom LaTeX packages
LATEX_PACKAGES="tikz,pgfplots" docker compose up
```

## 🔧 Development Workflow

### Local Development Setup
```bash
# Install dependencies locally
pip install poetry
poetry install

# Run with hot reload
poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest
```

### Code Quality
```bash
# Format code
poetry run black backend/
poetry run isort backend/

# Type checking
poetry run mypy backend/
```

## 🧪 Testing

### API Testing
```bash
# Test compilation endpoint
curl -X POST "http://localhost:8000/api/compile" \
  -H "Content-Type: application/json" \
  -d '{"content": "\\documentclass[14pt]{styles/gost-7-32}\\begin{document}Test\\end{document}"}'

# Test WebSocket compilation
wscat -c ws://localhost:8000/ws/compile
```

### Integration Tests
```bash
# Run full integration test
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 Monitoring & Logging

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Application logs
tail -f logs/app.log
```

### Health Checks
- Backend: http://localhost:8000/health
- OpenWebUI: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 🔐 Security Considerations

- LaTeX compilation runs in isolated containers
- File uploads validated and sanitized
- Compilation timeouts prevent resource exhaustion
- CORS configured for production domains
- Volume permissions restricted

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a Pull Request

### Contribution Areas
- LaTeX template improvements
- Additional OpenWebUI tools
- Docker optimizations
- Documentation enhancements
- New compilation features

## 📞 Support

For questions or issues:

- **Documentation**: Check `/docs` directory
- **Issues**: Create GitHub Issue
- **Chat**: Join our Discord community
- **Support**: `support@project.com`

---

**Built with ❤️ for the Russian academic community** 