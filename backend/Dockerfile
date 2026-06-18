FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the whole package first so the editable install can discover `app`.
COPY . .
RUN pip install --upgrade pip && pip install -e ".[dev]"

EXPOSE 8000
# Compose overrides this to run migrations first; this is the plain default.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
