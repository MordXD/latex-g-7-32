# ==========================================
# Stage 1: Builder (Python Dependencies)
# ==========================================
FROM python:3.11-slim as builder

WORKDIR /app

# Установка Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -sSL https://install.python-poetry.org | python3 -

# Копирование файлов зависимостей
COPY pyproject.toml poetry.lock ./

# Установка зависимостей (без dev)
RUN poetry install --without dev --no-root

# ==========================================
# Stage 2: Final Image (Minimal TeX Live)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:/usr/local/texlive/bin/x86_64-linux:$PATH"

# 1. Установка системных зависимостей (минимальных)
# perl и wget нужны для установки TeX Live
RUN apt-get update && apt-get install -y --no-install-recommends \
    perl \
    wget \
    xz-utils \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# 2. Установка TeX Live (scheme-basic)
# Мы скачиваем установщик, ставим базовую версию и удаляем установщик
RUN mkdir /tmp/install-tl-unx && \
    wget -qO- https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz | \
    tar -xz -C /tmp/install-tl-unx --strip-components=1 && \
    printf "%s\n" \
      "selected_scheme scheme-basic" \
      "TEXDIR /usr/local/texlive" \
      "TEXMFLOCAL /usr/local/texlive/texmf-local" \
      "TEXMFSYSCONFIG /usr/local/texlive/texmf-config" \
      "TEXMFSYSVAR /usr/local/texlive/texmf-var" \
      "option_doc 0" \
      "option_src 0" \
      > /tmp/install-tl-unx/texlive.profile && \
    /tmp/install-tl-unx/install-tl -profile /tmp/install-tl-unx/texlive.profile && \
    rm -rf /tmp/install-tl-unx

# 3. Установка ТОЛЬКО необходимых пакетов через tlmgr
# Это и дает 70% оптимизации
RUN tlmgr update --self && \
    tlmgr install \
    collection-latexrecommended \
    collection-fontsrecommended \
    collection-langcyrillic \
    # Пакеты из GOST 7-32 стилей:
    titlesec titling setspace tocloft enumitem caption \
    listings multirow array booktabs colortbl makecell \
    fancyhdr indentfirst geometry \
    # Шрифты и языки:
    tempora babel-russian cm-super \
    # Математика и графики:
    amsmath siunitx circuitikz pgfplots \
    # Утилиты
    latexmk && \
    # Очистка кэша TeX Live
    rm -rf /usr/local/texlive/texmf-var/*

# 4. Копирование Python окружения из Builder stage
COPY --from=builder /app/.venv /app/.venv

# 5. Копирование кода приложения
COPY backend /app/backend
COPY latex /app/latex

# Создание пользователя (security best practice)
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]