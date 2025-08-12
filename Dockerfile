# --- Basis ---
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# --- Builder ---
FROM base AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Runtime (non-root) ---
FROM base AS runtime
ENV PATH="/opt/venv/bin:$PATH"
# Nutzer mit UID 1000 anlegen (passt oft zum Host-User, vermeidet Mount-Rechteprobleme)
RUN useradd -u 1000 -m appuser
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
USER appuser
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
