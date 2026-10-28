FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Aplikacja nie dziala jako root; katalog uploadow musi byc zapisywalny.
RUN useradd --create-home appuser \
    && mkdir -p /srv/uploads \
    && chown -R appuser:appuser /srv/uploads

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
