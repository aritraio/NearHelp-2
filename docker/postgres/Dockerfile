# PostgreSQL 16 with PostGIS 3.4 + pgvector — everything NearHelp needs in one
# engine (tech-stack.md ADR-2/ADR-3). Built on the official postgis image; the
# pgvector extension is installed from the PGDG apt repo the base image ships.
FROM postgis/postgis:16-3.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
