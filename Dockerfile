# Use texlive base image with full LaTeX installation
FROM texlive/texlive:latest

# Set working directory
WORKDIR /app

# Install Python 3.11 and required packages
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    python3.11-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python command
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Install Poetry
RUN pip install poetry

# Configure Poetry
RUN poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN poetry install --no-dev

# Copy application code
COPY backend/ ./backend/
COPY latex/ ./latex/
COPY .env ./

# Create necessary directories
RUN mkdir -p pdf logs

# Set permissions
RUN chmod +x backend/app/main.py

# Install additional LaTeX packages that might be needed
RUN tlmgr install \
    babel-russian \
    fontspec \
    unicode-math \
    microtype \
    geometry \
    fancyhdr \
    setspace \
    hyperref \
    circuitikz \
    listings \
    xcolor \
    biblatex \
    biber \
    amsmath \
    amsfonts \
    amssymb \
    siunitx \
    booktabs \
    multirow \
    array \
    enumitem \
    indentfirst

# Update font database
RUN updmap-sys

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "backend.app.main"]