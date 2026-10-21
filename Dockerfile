# syntax=docker/dockerfile:1
# Obraz budowany wieloetapowo: zaleznosci instalujemy w etapie "builder",
# a do obrazu finalnego kopiujemy tylko gotowe venv -> mniejsza powierzchnia ataku.
# Ten sam obraz pojdzie pozniej do Azure Container Registry (L4/L5).

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENVIRONMENT=dev

# Aktualizacja pakietow bazowych + usuniecie listy pakietow (mniejszy obraz).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Aplikacja nie dziala jako root (CIS Docker Benchmark 4.1).
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home --shell /usr/sbin/nologin appuser

WORKDIR /srv/app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser scripts ./scripts

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

# proxy-headers: aplikacja stoi za nginx (lokalnie) / Application Gateway (Azure).
# no-server-header: nie zdradzamy uzywanego serwera WWW (rekonesans).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*", "--no-server-header"]
