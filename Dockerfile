FROM python:3.13-slim

LABEL org.opencontainers.image.title="Hybrid Financial Fraud Evaluation Engine" \
      org.opencontainers.image.description="Deterministic rules plus supervised ML fraud evaluation API" \
      org.opencontainers.image.source="https://github.com/sergiofigueras/hybrid-fraud-engine" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY fraud_engine ./fraud_engine
COPY training ./training
COPY artifacts ./artifacts

RUN python -m pip install --no-cache-dir . \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3)" || exit 1

CMD ["sh", "-c", "uvicorn fraud_engine.api:app --host 0.0.0.0 --port ${PORT}"]
