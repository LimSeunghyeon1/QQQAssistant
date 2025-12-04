FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/ .

RUN pip install --upgrade pip && \
    pip wheel --no-deps --wheel-dir /tmp/wheels .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

COPY backend /app/backend
COPY --from=builder /tmp/wheels /tmp/wheels

RUN pip install --upgrade pip && \
    pip install --no-cache-dir /tmp/wheels/*.whl

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
