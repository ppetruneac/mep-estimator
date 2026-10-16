# Riser inventory review API
# Build from repo root:
#   docker build -f apps/inventory_webapp/Dockerfile -t riser-inventory-api:local .

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir uv

# Install extractor + webapp deps
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system --no-cache -e .

COPY apps/inventory_webapp/pyproject.toml /webapp/pyproject.toml
COPY apps/inventory_webapp/app /webapp/app
WORKDIR /webapp
RUN uv pip install --system --no-cache fastapi "uvicorn[standard]" pydantic python-multipart

ENV DATA_DIR=/data \
    RISER_DB_PATH=/data/getriser.sqlite \
    HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/webapp

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
