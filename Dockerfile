# ─────────────────────────────────────────────
# QoL Cardiac — MedFlow AI Research
# Image de production — Streamlit sur port 8501
# ─────────────────────────────────────────────

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Dr. Mamadou Lamine TALL <contact@medflowai.fr>"
LABEL version="1.0"
LABEL description="QoL Cardiac — Évaluation de la qualité de vie patient cardiaque"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_THEME_BASE="dark" \
    STREAMLIT_THEME_PRIMARY_COLOR="#3b82f6"

# Répertoire de travail
WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY app.py .

# Créer le dossier de configuration Streamlit
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml /app/.streamlit/config.toml 2>/dev/null || true

# Port exposé
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Lancement
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
