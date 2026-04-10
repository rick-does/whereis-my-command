# Stage 1: Build corpus
FROM python:3.12-slim AS corpus-build

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY ingest/ ingest/
RUN pip install --no-cache-dir -r ingest/requirements.txt
RUN python ingest/ingest.py

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

COPY backend/ backend/
RUN python -m venv backend/.venv \
    && backend/.venv/bin/pip install --no-cache-dir -r backend/requirements.txt

COPY frontend/ frontend/

COPY --from=corpus-build /build/data/chroma/ data/chroma/
COPY --from=corpus-build /root/.cache/ /root/.cache/

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
