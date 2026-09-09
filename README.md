# SIH26162 Thermal Event Intelligence Platform

A modular, event-driven pipeline for near-real-time thermal anomaly detection, geospatial fusion, and intelligence generation.

**Current Stage:** Stage 1A - FIRMS Ingestion with Demo Mode  
**Local Dev Mode:** Native PostgreSQL + PostGIS on Windows (no Docker required)  
**Status:** 🚀 Ready for local development

---

## Quick Start (Windows)

### Prerequisites
- PostgreSQL 13+ with PostGIS 3.0+
- Python 3.11+
- Git

### Installation (5 minutes)

**Step 1: Install PostgreSQL + PostGIS**
```powershell
# Download from https://www.postgresql.org/download/windows/
# During installation, remember your postgres password
# Use StackBuilder to install PostGIS
```

**Step 2: Create Database**
```powershell
psql -U postgres -h localhost

# In psql:
CREATE DATABASE sih26162;
\c sih26162
CREATE EXTENSION IF NOT EXISTS postgis;
\q
```

**Step 3: Clone and Setup Backend**
```powershell
git clone https://github.com/your-org/SIH26162.git
cd SIH26162

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

**Step 4: Configure Environment**
```powershell
Copy-Item .env.example .env
notepad .env

# Edit DATABASE_URL with your PostgreSQL password:
# DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/sih26162
```

**Step 5: Start Backend**
```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 6: Load Demo Data**
```powershell
# In another PowerShell terminal:
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/admin/ingest-demo-data" -Method Post
```

**Backend is running at:** http://localhost:8000

---

## Configuration

### Environment Variables (.env)

```bash
# Database connection (PostgreSQL + PostGIS)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/sih26162

# FIRMS API (optional, set for real thermal data)
FIRMS_MAP_KEY=your_32_char_key_from_firms.modaps.eosdis.nasa.gov
DEMO_MODE=true  # Use false if you have a FIRMS key

# Backend
BACKEND_PORT=8000
BACKEND_ENV=development
LOG_LEVEL=INFO

# Geospatial
PILOT_BBOX=17.35,73.50,19.00,75.50  # Pune pilot region
FIRMS_BBOX=17.35,73.50,19.00,75.50

# Optional: Google Earth Engine (Stage 1B)
EARTH_ENGINE_PROJECT_ID=your-gee-project-id
```

### Getting Your FIRMS API Key

1. Visit https://firms.modaps.eosdis.nasa.gov/api/
2. Sign up / Login
3. Request a map key
4. Add to `.env`: `FIRMS_MAP_KEY=your_key`
5. Set `DEMO_MODE=false`
6. Restart backend

---

## API Endpoints (Stage 1A)

### Health Checks

```bash
# System health (includes PostGIS verification)
curl http://localhost:8000/api/v1/health

# Detailed status
curl http://localhost:8000/api/v1/status

# Source health
curl http://localhost:8000/api/v1/sources/health
```

### Events

```bash
# List recent events
curl http://localhost:8000/api/v1/events?limit=100

# Get event detail
curl http://localhost:8000/api/v1/events/{event_id}

# Get event evidence (Stage 1B - stub)
curl http://localhost:8000/api/v1/events/{event_id}/evidence

# Filter by region
curl "http://localhost:8000/api/v1/events?min_lat=17.35&max_lat=19.0&min_lon=73.5&max_lon=75.5"

# Filter by confidence
curl "http://localhost:8000/api/v1/events?min_confidence=80"

# Recent events (quick endpoint)
curl http://localhost:8000/api/v1/events/recent?limit=50&hours=24
```

### Ingestion Management

```bash
# Get FIRMS polling history
curl http://localhost:8000/api/v1/sources/runs?source=FIRMS&limit=10

# Get specific run
curl http://localhost:8000/api/v1/sources/runs/{run_id}

# Get events from a run
curl http://localhost:8000/api/v1/sources/runs/{run_id}/events

# Trigger FIRMS poll now (admin)
curl -X POST http://localhost:8000/api/v1/admin/poll-firms-now

# Start background polling (admin)
curl -X POST http://localhost:8000/api/v1/admin/start-polling

# Load demo data (admin)
curl -X POST http://localhost:8000/api/v1/admin/ingest-demo-data
```

---

## Database Schema (Stage 1A)

### Key Tables

**thermal_events** — Normalized thermal detections from FIRMS
- Deterministic deduplication by (latitude, longitude, acquisition_time, satellite)
- PostGIS geometry point (WGS84)
- Raw payload tracking (URI, SHA-256)
- Status: active, duplicate, archived

**ingestion_runs** — FIRMS polling history
- Success/failure metrics, record counts, timing
- Next scheduled run timestamp

**raw_payloads** — Immutable store of raw API responses
- Content hash, retention policy
- Supports replay and reproducibility

**source_health** — Data source availability tracking
- Status: healthy, degraded, unavailable, unknown
- Last check, last success timestamps

**contextual_features** — GIS layers (populated Stage 1B)
- OSM industrial/infrastructure features
- Manual GIS imports (GeoJSON, CSV, WFS)

**event_spatial_enrichment** — Spatial matching results (Stage 1B)
- Inside industrial zone, nearest feature, distance, count within 1km
- Land-cover classification, water proximity
- Coverage state: match_found, no_match, unavailable, coverage_unknown

---

## Project Structure

```
SIH26162/
├── .env                          # Local config (DO NOT COMMIT)
├── .env.example                  # Configuration template
├── README.md                     # This file
├── DEVELOPMENT.md                # Detailed setup guide (Windows PostgreSQL)
├── docker-compose.yml            # Docker setup (preserved for deployment)
│
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration (reads DATABASE_URL)
│   ├── database.py               # PostgreSQL async interface
│   ├── firms_collector.py        # FIRMS API polling & ingestion
│   ├── demo_data.py              # Mock event generator
│   ├── requirements.txt          # Python dependencies
│   ├── data/storage/             # Local file storage
│   ├── gis/                      # GIS providers (Stage 1B)
│   │   ├── osm_provider.py       # OpenStreetMap/Overpass
│   │   └── dynamic_world_provider.py  # Google Dynamic World
│   ├── api/
│   │   ├── health.py             # Health check endpoints
│   │   ├── events.py             # Events read API
│   │   └── sources.py            # Source health & run history
│   └── tests/                    # Unit tests (Stage 1B)
│
├── frontend/
│   ├── package.json              # Node dependencies
│   └── src/
│       └── App.tsx               # React app shell
│
├── infra/
│   ├── migrations/
│   │   ├── 00_init_schema.sql    # PostgreSQL schema
│   │   └── 01_spatial_indexes.sql# PostGIS performance tuning
│   ├── docker/
│   │   └── Dockerfile.backend    # Backend image (for Docker)
│   └── sample-data/              # Demo fixtures
│
└── docs/
    └── (API documentation - coming)
```

---

## Troubleshooting

### "PostGIS extension not available"

```powershell
# Install via StackBuilder or enable in database:
psql -U postgres -h localhost -d sih26162 -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Verify:
psql -U postgres -h localhost -d sih26162 -c "SELECT PostGIS_version();"
```

### "Connection refused"

```powershell
# PostgreSQL not running. Start it:
Start-Service postgresql-x64-15
# Or restart:
Restart-Service postgresql-x64-15
```

### "Password authentication failed"

```powershell
# Wrong password in DATABASE_URL
# Update .env with correct password:
notepad .env

# Or reset PostgreSQL password:
psql -U postgres -h localhost -c "ALTER USER postgres WITH PASSWORD 'NewPassword';"
```

### Backend won't start

```powershell
# 1. Check DATABASE_URL is set in .env
# 2. Verify PostgreSQL is running
# 3. Check database exists:
psql -U postgres -h localhost -d sih26162 -c "\dt"

# 4. Check PostGIS is installed:
psql -U postgres -h localhost -d sih26162 -c "SELECT PostGIS_version();"
```

### Port 8000 already in use

```powershell
# Use different port:
python -m uvicorn backend.main:app --reload --port 8001
```

---

## Development Workflow

### Adding a New API Endpoint

1. Create new route in `backend/api/` (e.g., `backend/api/enrichment.py`)
2. Define request/response models with Pydantic
3. Include router in `backend/main.py`
4. Test: `curl http://localhost:8000/api/v1/...`

### Modifying Database Schema

1. Edit `infra/migrations/` SQL files
2. For versioned migrations, use Alembic
3. Restart backend to apply migrations

### Running Tests

```powershell
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

---

## Next: Stage 1B (GIS Enrichment)

After Stage 1A is working locally:

1. **OpenStreetMap Adapter**
   - Query Overpass API for industrial features (factories, parks, zones)
   - Restrict live queries to Pune pilot region only
   - Cache results by geographic tile
   - Add timeouts, retries, User-Agent, manual GeoJSON fallback

2. **Spatial Enrichment**
   - For each event: query contextual_features within 1 km
   - Calculate: inside_zone, nearest_distance, feature_count
   - Use PostGIS ST_DWithin, ST_Distance, ST_Intersects

3. **Google Dynamic World Land-Cover**
   - Query GOOGLE/DYNAMICWORLD/V1 via Earth Engine
   - Store land-cover labels, probabilities, dates
   - Graceful fallback if credentials unavailable
   - Demo fixtures for development

4. **Manual GIS Import**
   - Support: GeoJSON, CSV, WFS, ArcGIS FeatureServer
   - Endpoints: POST `/api/v1/admin/import-geojson`, POST `/api/v1/admin/import-csv`
   - Future: Bhuvan/ISRO, government layers

5. **Evidence Storage**
   - Link events to GIS sources
   - Track coverage state: match_found, no_match, unavailable, coverage_unknown
   - No overwriting of raw event data

---

## Docker Deployment (Future)

PostgreSQL local development mode is **for local work only**. For production/Docker:

```bash
# Use docker-compose with PostgreSQL container
docker-compose up -d

# Backend will initialize PostgreSQL schema automatically
```

---

## Performance Optimization

### PostGIS Indexes

```sql
-- Spatial index on thermal_events geometry
CREATE INDEX CONCURRENTLY idx_thermal_events_geom ON thermal_events USING GIST(point);

-- Index on contextual_features
CREATE INDEX CONCURRENTLY idx_contextual_features_geom ON contextual_features USING GIST(ST_Point(longitude, latitude)::geography);

-- Time-based indexes
CREATE INDEX idx_thermal_events_acq_time ON thermal_events(acquisition_time DESC);
CREATE INDEX idx_contextual_features_source ON contextual_features(source_name);
```

### Query Optimization

```sql
-- Use ST_DWithin for distance queries (indexed)
SELECT * FROM contextual_features
WHERE ST_DWithin(
  ST_Point(longitude, latitude)::geography,
  ST_Point(event_lon, event_lat)::geography,
  1000  -- 1 km buffer in meters
);

-- Use ST_Intersects for polygon containment
SELECT * FROM contextual_features
WHERE ST_Intersects(
  geometry_polygon,
  ST_Point(event_lon, event_lat)
);
```

---

## Roadmap

| Stage | Focus | Status |
|-------|-------|--------|
| **1A** | FIRMS ingestion, demo mode, basic APIs | ✅ **Now** |
| **1B** | OSM enrichment, spatial matching, evidence | 📅 Next |
| **1C** | Historical data import, manual GIS layers | 📅 After 1B |
| **2** | ML model training, persistence features | 📅 Later |
| **3** | Dashboard, alerting, review UI | 📅 Final |

---

## Key Design Decisions

### Immutable Raw Data
- Raw FIRMS payloads stored with SHA-256 hash
- Allows re-running enrichment without re-fetching
- Provenance tracked: pipeline_version, processed_at

### Deterministic Deduplication
- Dedup key: `(latitude, longitude, acquisition_time, satellite)` rounded to 4 decimals
- No fuzzy matching; eliminates duplicates at ingestion
- Allows safe replay of missed polling windows

### Local-First Spatial Queries
- GIS layers cached in PostgreSQL
- Event enrichment happens via local PostGIS queries
- Faster, cheaper, more reliable than remote calls

### Pune Pilot Region Restriction
- OSM live queries restricted to Pune bounding box (17.35,73.50,19.00,75.50)
- Prevents nationwide Overpass spam
- Cache by tile for efficiency

### Environment-Based Configuration
- No hardcoded credentials in source code
- DATABASE_URL read from .env only
- No password in .env.example or logs

---

## Support & Debugging

### Enable Verbose Logging

```bash
LOG_LEVEL=DEBUG

# Or in PowerShell:
$env:LOG_LEVEL = "DEBUG"
```

### Inspect Database Directly

```powershell
psql -U postgres -h localhost -d sih26162

-- Useful queries:
SELECT COUNT(*) FROM thermal_events;
SELECT id, latitude, longitude, acquisition_time FROM thermal_events LIMIT 5;
SELECT source, COUNT(*) FROM ingestion_runs GROUP BY source;
SELECT version();      -- PostgreSQL version
SELECT PostGIS_version();  -- PostGIS version
\q
```

---

## Contributors

Built for **SIH 2026 | Thermal Event Intelligence Platform**

---

**Last Updated:** 2026-08-25  
**Edition:** Windows PostgreSQL + PostGIS (Native, No Docker)
