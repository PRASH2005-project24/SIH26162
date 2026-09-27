# FIREXIS : Fire Intelligence and Risk Exploration System
## Comprehensive System Documentation

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Technical Stack](#technical-stack)
3. [System Architecture](#system-architecture)
4. [Data Flow & Workflow](#data-flow--workflow)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [ML Workflow](#ml-workflow)
8. [Configuration & Environment](#configuration--environment)
9. [Deployment Instructions](#deployment-instructions)
10. [Component Details](#component-details)

---

## System Overview

FIREXIS (Fire Intelligence and Risk Exploration System) is a geospatial intelligence platform for detecting, classifying, and analyzing thermal events using NASA FIRMS data. The system provides real-time monitoring of fire incidents across India with AI-powered classification into 5 SIH (Socially Innovative Hub) categories.

**Core Mission**: Transform raw satellite thermal data into actionable intelligence for disaster response, environmental monitoring, and risk assessment.

**Current Stage**: Stage 1A - FIRMS Ingestion with live FIRMS data (foundational data pipeline)

### Current Project Status Metrics
- **ML Model Accuracy**: 99.50% test accuracy on the verified Stage 2 model (`Random Forest`, validated against the held-out test set and backed by the project’s saved metrics artifact)
- **Usable Persisted Enrichment**: 57/128 events with a latest GIS enrichment row (44.5%) have both a non-null land-cover label and non-empty class probabilities; this includes one explicitly cached result
- **Current Active-Event Coverage**: 57/577 eligible active events (9.9%) currently have usable Dynamic World data, including cached data; this is a completeness measure, not an attempted-event failure rate
- **Recent Cohort After Provider Changes**: The same 10 events now have 4/10 usable outputs (40%): three confirmed fresh `dw:live` results and one `dw:cached` result
- **Temporal Fallback**: Two newly recovered events used valid scenes 16 and 26 days before the event. The provider returns image age, but the enrichment database row does not yet persist it
- **Legacy Coverage Caveat**: Older rows may say `dw:live` even when served from cache because previous code did not distinguish cache hits. Use new rows for fresh-live reporting
- **Operational Status**: FIRMS ingestion and the Stage 2 ML inference path are validated in the repository; Dynamic World sampling now checks multiple nearby scenes and rejects empty samples, but recent fresh-live usable output remains low

> Note: The 99.50% accuracy figure is supported by repository tests and the saved metrics artifact. Usable enrichment requires both a land-cover label and a complete probability vector. The database aggregate includes historical rows whose cache/live state was not reliably distinguished; the cohort result is the reliable fresh-live comparison. Temporal fallback results must be interpreted with their image age.

---

## Technical Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (ASGI)
- **Database**: PostgreSQL 15+ with PostGIS 3.3+
- **ORM**: SQLAlchemy 2.0 (async)
- **API Documentation**: OpenAPI 3.0 (Swagger UI)
- **ML Framework**: Scikit-learn, Joblib
- **Geospatial**: GeoPandas, Shapely
- **Environment**: Pydantic Settings, Python-Dotenv

### Frontend
- **Framework**: React 18+ with Vite
- **State Management**: React Query (TanStack)
- **Mapping**: Mapbox GL JS / Leaflet
- **UI Components**: Custom React components with Tailwind CSS
- **Data Visualization**: Chart.js, Recharts
- **Type Safety**: TypeScript 5.0+

### DevOps & Infrastructure
- **Containerization**: Docker (optional)
- **CI/CD**: GitHub Actions
- **Monitoring**: Structured logging, Health checks
- **Testing**: Pytest, Jest
- **Version Control**: Git

### Data Sources
- **Primary**: NASA FIRMS (Fire Information for Resource Management System)
- **Geospatial**: OpenStreetMap (OSM) via Overpass API
- **Land Cover**: Google Earth Engine Dynamic World
- **Satellite Imagery**: Sentinel-2 Level-2A (optional preview)

---

## System Architecture

```mermaid
graph TD
    A[NASA FIRMS API] --> B[FIRMS Collector Service]
    B --> C{Duplicate Detection}
    C -->|New Event| D[thermal_events Table]
    C -->|Duplicate| E[Duplicate Logging]
    D --> F[Background Processing Pipeline]
    F --> G[GIS Enrichment Engine]
    F --> H[ML Classification Engine]
    F --> I[Thermal Source Grouper]
    G --> J[event_spatial_enrichment Table]
    H --> K[event_classifications Table]
    I --> L[thermal_sources Table]
    D --> M[historical_data Table]:::trigger
    style M fill:#e1f5fe,stroke:#01579b
    
    subgraph Backend Services
        B
        F
        G
        H
        I
    end
    
    subgraph Database
        D
        E
        J
        K
        L
        M
    end
    
    N[Frontend Application] --> O[REST API]
    O --> P[Events Endpoint]
    O --> Q[ML Prediction Endpoint]
    O --> R[Health Endpoints]
    P --> D
    Q --> K
    R --> S[System Health]
    
    classDef trigger fill:#e1f5fe,stroke:#01579b;
```

### Key Architectural Principles
1. **Modularity**: Loosely coupled services communicating through database
2. **Idempotency**: All operations designed to be safely retryable
3. **Deterministic Deduplication**: Spatial-temporal hashing for duplicate detection
4. **Eventual Consistency**: Background processing for enrichment/ML
5. **Separation of Concerns**: Ingestion vs Enrichment vs Classification
6. **Extensibility**: Plugin-style architecture for new data sources

---

## Data Flow & Workflow

### 1. FIRMS Data Ingestion Workflow
```mermaid
sequenceDiagram
    participant Scheduler as Cron/Background Task
    participant FIRMS as FIRMS Collector
    participant API as NASA FIRMS API
    participant DB as PostgreSQL
    participant RAW as raw_payloads Table
    participant EVENT as thermal_events Table
    participant DEDUP as Deduplication Logic
    
    Scheduler->>FIRMS: Trigger poll (every 30min)
    FIRMS->>API: GET /area/csv/{bbox}/1
    API-->>FIRMS: CSV Thermal Events
    FIRMS->>RAW: Store raw payload (content-addressed)
    FIRMS->>DEDUP: Normalize & deduplicate
    DEDUP->>EVENT: Insert new events
    EVENT->>DB: Persist with PostGIS geometry
    FIRMS->>DB: Log ingestion run metadata
    
    alt New Events Detected
        FIRMS->>Background: Trigger enrichment & classification
        Background->>GIS: OSM/Dynamic World enrichment
        Background->>ML: Feature extraction & classification
        GIS->>DB: Update event_spatial_enrichment
        ML->>DB: Update event_classifications
    end
```

### 2. Event Processing Pipeline
```mermaid
flowchart LR
    A[Raw FIRMS CSV] --> B[Normalization]
    B --> C{Deduplication Check}
    C -->|Duplicate| D[Mark as Duplicate]
    C -->|New| E[Insert into thermal_events]
    E --> F[PostGIS Geometry Index]
    E --> G[Trigger: historical_data Copy]:::auto
    E --> H[Background Processing Queue]
    H --> I[GIS Enrichment: OSM + DW]
    H --> J[ML: Feature Computation]
    H --> K[Thermal Source Grouping]
    I --> L[event_spatial_enrichment]
    J --> M[event_classifications]
    K --> N[thermal_sources]
    style G fill:#e3f2fd,stroke:#1565c0,stroke-dasharray: 5 5
    classDef auto fill:#e3f2fd,stroke:#1565c0,stroke-dasharray: 5 5;
```

### 3. Frontend Data Consumption
```mermaid
sequenceDiagram
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    
    UI->>API: GET /api/v1/events?include_ml=true&include_enrichment=true
    API->>DB: SQL JOIN thermal_events + classifications + enrichment
    DB-->>API: Combined event records
    API->>UI: Normalized JSON response
    UI->>UI: Display in Maps/Tables/Charts
    
    loop Real-time Updates
        UI->>API: GET /api/v1/events (every 30s)
        API->>DB: Query recent events
        DB-->>API: Fresh event data
        API->>UI: Update live components
    end
```

---

## Database Schema

### Core Tables

#### 1. `thermal_events` (Core Detection Table)
```sql
CREATE TABLE thermal_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    acquisition_time TIMESTAMPTZ NOT NULL,
    satellite TEXT NOT NULL,
    instrument TEXT,
    brightness NUMERIC,           -- Kelvin
    brightness_rad NUMERIC,       -- W/m2/sr
    frp NUMERIC,                  -- MW (Fire Radiative Power)
    confidence INTEGER,           -- 0-100
    scan NUMERIC,                 -- degrees
    track NUMERIC,                -- degrees
    day_night TEXT,               -- 'D' or 'N'
    point GEOMETRY(Point, 4326) NOT NULL,
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(11, 6) NOT NULL,
    raw_payload_uri TEXT,
    raw_payload_sha256 TEXT,
    pipeline_version TEXT DEFAULT '1.0.0',
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ingestion_run_id UUID,
    status TEXT DEFAULT 'active', -- active|duplicate|archived
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_id UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE UNIQUE INDEX idx_thermal_events_dedup 
  ON thermal_events (
    ROUND(latitude::NUMERIC, 4),
    ROUND(longitude::NUMERIC, 4),
    DATE_TRUNC('minute', acquisition_time),
    satellite
  ) WHERE status != 'archived';

CREATE INDEX idx_thermal_events_geom ON thermal_events USING GIST(point);
CREATE INDEX idx_thermal_events_acquisition_time ON thermal_events(acquisition_time DESC);
```

#### 2. `historical_data` (Append-only Archive)
```sql
CREATE TABLE historical_data (
    event_id TEXT PRIMARY KEY,
    acquisition_time TIMESTAMPTZ NOT NULL,
    satellite TEXT NOT NULL,
    instrument TEXT,
    brightness NUMERIC,
    brightness_rad NUMERIC,
    frp NUMERIC,
    confidence INTEGER,
    scan NUMERIC,
    track NUMERIC,
    day_night TEXT,
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(11, 6) NOT NULL,
    point GEOMETRY(Point, 4326) NOT NULL,
    raw_payload_uri TEXT,
    raw_payload_sha256 TEXT,
    pipeline_version TEXT,
    ingestion_run_id TEXT,
    status TEXT,
    source_created_at TIMESTAMPTZ,
    copied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_historical_event
        FOREIGN KEY (event_id) REFERENCES thermal_events(id) ON DELETE CASCADE
);

CREATE INDEX idx_historical_data_acquisition_time ON historical_data(acquisition_time DESC);
CREATE INDEX idx_historical_data_geom ON historical_data USING GIST(point);

-- Trigger for automatic archiving
CREATE OR REPLACE FUNCTION copy_thermal_event_to_history()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO historical_data (
        event_id, acquisition_time, satellite, instrument,
        brightness, brightness_rad, frp, confidence, scan, track, day_night,
        latitude, longitude, point, raw_payload_uri, raw_payload_sha256,
        pipeline_version, ingestion_run_id, status, source_created_at
    ) VALUES (
        NEW.id, NEW.acquisition_time, NEW.satellite, NEW.instrument,
        NEW.brightness, NEW.brightness_rad, NEW.frp, NEW.confidence,
        NEW.scan, NEW.track, NEW.day_night,
        NEW.latitude, NEW.longitude, NEW.point, NEW.raw_payload_uri,
        NEW.raw_payload_sha256, NEW.pipeline_version, NEW.ingestion_run_id,
        NEW.status, NEW.created_at
    )
    ON CONFLICT (event_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER thermal_events_history_insert
AFTER INSERT ON thermal_events
FOR EACH ROW
EXECUTE FUNCTION copy_thermal_event_to_history();
```

#### 3. `event_classifications` (ML Results)
```sql
CREATE TABLE event_classifications (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    event_id TEXT NOT NULL UNIQUE,
    ml_predicted_class TEXT,           -- industrial|agricultural|wildfire
    ml_confidence NUMERIC,
    ml_probabilities_json JSONB,
    is_persistent BOOLEAN,
    persistence_date_count INTEGER,
    persistence_duration_days INTEGER,
    final_sih_category TEXT,           -- 5 SIH categories
    classification_status TEXT DEFAULT 'success',
    inference_error TEXT,
    pipeline_version TEXT,
    classification_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES thermal_events(id) ON DELETE CASCADE
);
```

#### 4. `event_spatial_enrichment` (GIS Context)
```sql
CREATE TABLE event_spatial_enrichment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL,
    inside_industrial_zone BOOLEAN,
    nearest_feature_distance_m NUMERIC,
    feature_count_1km INTEGER,
    nearby_water BOOLEAN,
    land_cover_label TEXT,
    land_cover_probabilities_json JSONB,
    acquisition_date DATE,
    query_date DATE,
    coverage_state TEXT,
    provider_version TEXT,
    computation_time_ms INTEGER,
    rule_version TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES thermal_events(id) ON DELETE CASCADE
);
```

#### 5. `ingestion_runs` (Pipeline Monitoring)
```sql
CREATE TABLE ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL DEFAULT 'FIRMS',
    run_timestamp TIMESTAMPTZ NOT NULL,
    bbox TEXT,
    record_count INTEGER DEFAULT 0,
    deduplicated_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    next_scheduled_run TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

### Events API (`/api/v1/events`)
| Method | Endpoint | Description | Key Parameters |
|--------|----------|-------------|----------------|
| GET | `/` | List events with filtering | `limit`, `offset`, `status`, `min_lat/max_lat`, `min_lon/max_lon`, `min_confidence`, `since_hours`, `include_enrichment`, `include_ml` |
| GET | `/{event_id}` | Get detailed event | `include_enrichment`, `include_ml` |
| GET | `/{event_id}/enrichment` | Get enrichment data only | - |
| GET | `/{event_id}/ml-prediction` | Get ML prediction only | - |
| GET | `/statistics` | Get dashboard statistics | - |
| GET | `/recent` | Get recent events (last N hours) | `limit`, `hours` |
| GET | `/{event_id}/satellite-preview/image` | Get Sentinel-2 preview image | - |
| GET | `/satellite-preview/coordinates` | Get preview for coordinates | `lat`, `lon`, `acq_time` |

### ML API (`/api/v1/ml`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict` | Predict fire class (accepts event_id or features) |

### Health & Monitoring (`/api/v1/health`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Basic health check |
| GET | `/detailed` | Detailed system status |
| GET | `/sources` | Data source health |
| GET | `/metrics` | Prometheus metrics |

### Admin Endpoints (`/api/v1/admin`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest-demo-data` | Load demo data (dev only) |
| POST | `/poll-firms-now` | Trigger immediate FIRMS poll |
| POST | `/start-polling` | Start background polling loop |

---

## ML Workflow

### Stage 1: Feature Computation
1. **Input**: Event ID from `thermal_events`
2. **Fetch**: Core event data + enrichment (OSM/Dynamic World)
3. **Compute**: 15-feature vector matching training schema
4. **Output**: Feature dictionary for inference

### Feature Engineering Pipeline
```mermaid
graph LR
    A[Raw Event Data] --> B[FIRMS Features]
    A --> C[OSM Features]
    A --> D[Dynamic World Features]
    A --> E[Temporal Features]
    B --> F[Feature Vector]
    C --> F
    D --> F
    E --> F
    F --> G[StandardScaler]
    G --> H[ML Model Input]
    
    subgraph FIRMS Features
        B1[bright_ti4, bright_ti5] --> B2[Normalization]
        B3[frp] --> B4[Log Transform]
        B5[confidence] --> B6[0-1 Scaling]
        B7[scan, track] --> B8[0-2 Normalization]
        B9[day_night] --> B10[One-Hot]
        B11[satellite, instrument] --> B12[One-Hot]
    end
    
    subgraph OSM Features
        C1[facility_distance] --> C2[Log Transform]
        C3[water_distance] --> C4[Log Transform]
        C5[industrial_score] --> C6[Direct Use]
    end
    
    subgraph Dynamic World Features
        D1[water, trees, grass, etc.] --> D2[Direct Probabilities]
        D3[confidence] --> D4[Direct Use]
        D5[found flag] --> D6[Binary]
    end
    
    subgraph Temporal Features
        E1[acquisition_time] --> E2[Hour, DoW, Month]
        E2 --> E3[Sin/Cos Encoding]
        E4[persistence counts] --> E5[Log Transform]
        E6[FRP stats] --> E7[Log Transform]
    end
```

### Model Inference
- **Model Type**: Random Forest Classifier (Stage 2)
- **Input**: 15-dimensional feature vector
- **Output**: 
  - Predicted class: `industrial` \| `agricultural` \| `wildfire`
  - Class probabilities: 3-class distribution
  - Confidence: Max probability value
- **Post-processing**: Map to 5 SIH categories using persistence logic

### SIH Category Mapping
| ML Class | SIH Category | Conditions |
|----------|--------------|------------|
| industrial | Industrial Fire | ML confidence ≥ 0.6 |
| agricultural | Agricultural Fire | ML confidence ≥ 0.6 |
| wildfire | Wildfire/Natural Fire | ML confidence ≥ 0.6 |
| Any class | Persistent Thermal Source | Persistence score ≥ threshold (date_count ≥ 5 AND duration_days ≥ 30) |
| Low confidence | Unknown/Other | ML confidence < 0.6 OR no persistence |

---

## Configuration & Environment

### Environment Variables (`.env`)
```env
# === CORE CONFIGURATION ===
PILOT_BBOX=8.0,68.0,35.0,97.0          # India-wide bounding box
PILOT_NAME=india
FIRMS_BBOX=8.0,68.0,35.0,97.0

# === GOOGLE EARTH ENGINE ===
EARTH_ENGINE_PROJECT_ID=sih26162-thermal-intelligence
EARTH_ENGINE_CREDENTIALS_PATH=          # Leave empty for default auth

# === FIRMS INGESTION ===
DEMO_MODE=false                         # Set true for development without API key
FIRMS_MAP_KEY=                          # NASA FIRMS API key (required for real data)
FIRMS_POLLING_INTERVAL_MINUTES=30       # Polling frequency

# === DATABASE ===
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sih26162
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_ENV=development                 # development|staging|production

# === STORAGE ===
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=./data/storage
STORAGE_RETENTION_DAYS=730              # 2 years

# === LOGGING ===
LOG_LEVEL=INFO

# === GEOSPATIAL ===
OSM_CACHE_TTL_SECONDS=604800            # 1 week
EVENT_BUFFER_1KM=1000
EVENT_BUFFER_5KM=5000

# === CORS ===
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,*
```

### Configuration Classes
- `backend/config.py`: Pydantic-based settings management
- Environment variable validation with sensible defaults
- Runtime configuration access throughout the application

---

## Deployment Instructions

### Prerequisites
1. **PostgreSQL 15+** with PostGIS 3.3+ extension
2. **Python 3.11+** 
3. **NASA FIRMS API Key** (for production data)
4. **Google Earth Engine** account (for Dynamic World data)
5. **Node.js 18+** and **npm** (for frontend)

### Backend Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd SIH26162

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp backend/.env.example backend/.env
# Edit .env with your settings:
# - Set FIRMS_MAP_KEY (NASA API key)
# - Adjust DATABASE_URL if needed
# - Set DEMO_MODE=false for production

# 5. Initialize database
python -c "from backend.database import init_db; import asyncio; from backend.config import Config; asyncio.run(init_db(Config()))"

# 6. Start backend server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure API connection
# Edit frontend/src/lib/api.ts if backend is not on localhost:8000

# 4. Start development server
npm run dev
# Frontend will be available at http://localhost:5173
```

### Production Deployment
```bash
# Build frontend for production
npm run build

# Serve frontend (using any static file server)
# Example: serve -s dist

# Run backend in production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment (Optional)
```bash
# Build and run with docker-compose
docker-compose up -d
```

---

## Component Details

### Backend Components

#### 1. `firms_collector.py`
- **Responsibility**: Fetches, normalizes, and deduplicates FIRMS data
- **Key Features**: 
  - Deterministic deduplication using spatial-temporal hashing
  - Raw payload storage for reproducibility
  - Background polling loop with error handling
  - Automatic triggering of enrichment and classification pipelines

#### 2. `database.py`
- **Responsibility**: Async PostgreSQL connection pool and query execution
- **Key Features**:
  - Connection pooling (production) / NullPool (development)
  - Multi-statement SQL script execution
  - Automatic datetime/Decimal serialization
  - Health check capabilities

#### 3. `classifier_engine.py`
- **Responsibility**: ML classification pipeline
- **Key Features**:
  - Feature computation from stored data
  - Persistence analysis (temporal clustering)
  - SIH category mapping with priority logic
  - Database upsert for classification results

#### 4. `api/events.py`
- **Responsibility**: REST API for event data
- **Key Features**:
  - Spatial and temporal filtering
  - Optional enrichment and ML data inclusion
  - Satellite preview image generation
  - Statistics aggregation
  - UUID validation and error handling

#### 5. `ml/sih_classifier.py`
- **Responsibility**: Map ML predictions to SIH categories
- **Key Features**:
  - Priority-based classification (Persistence > ML > Unknown)
  - Confidence preservation and adjustment
  - Metadata retention for traceability

### Frontend Components

#### 1. `pages/HistoricalEvents.tsx`
- **Responsibility**: Display historical events with filtering
- **Key Features**:
  - Data fetching via React Query
  - Live vs Historical event separation (24-48 hour threshold)
  - Category filtering, confidence thresholds
  - Search, satellite image filtering
  - Pagination and infinite scroll readiness

#### 2. `components/events/EventItem.tsx`
- **Responsibility**: Render individual event in lists
- **Key Features**:
  - SIH category badges with color coding
  - Location resolution (city/state detection)
  - Risk score visualization
  - Satellite preview thumbnails
  - Persistence indicators

#### 3. `components/map/MapContainer.tsx`
- **Responsibility**: Interactive map visualization
- **Key Features**:
  - Mapbox GL JS integration
  - Event clustering at high zoom levels
  - Popup details on click
  - Layer toggling (heatmap, clusters, individual points)
  - Geolocation and bounding box controls

#### 4. `services/apiAdapter.ts`
- **Responsibility**: Normalize backend data for frontend consumption
- **Key Features**:
  - SIH category color mapping
  - Location reverse geocoding (major Indian cities)
  - Land cover normalization
  - Industrial/water context inference
  - Risk score calculation (placeholder for Stage 2 ML)

---

## Data Storage Locations

### 1. Database Storage (`postgresql+asyncpg://...`)
- **Table**: `thermal_events` - Core FIRMS detections
- **Table**: `historical_data` - Append-only archive (triggered)
- **Table**: `event_classifications` - ML classification results
- **Table**: `event_spatial_enrichment` - OSM/Dynamic World context
- **Table**: `ingestion_runs` - Pipeline monitoring and audit
- **Table**: `raw_payloads` - Immutable FIRMS API responses
- **Table**: `source_health` - Data source monitoring
- **Table**: `contextual_features` - OSM/GIS feature catalog
- **Table**: `system_metadata` - Version and configuration tracking

### 2. File System Storage (`./data/storage/`)
- **Directory**: `sentinel_previews/` - Cached Sentinel-2 imagery
- **Directory**: `firms_raw/` - Optional raw FIRMS CSV archives
- **Directory**: `logs/` - Application logs (rotating)
- **Directory**: `temp/` - Temporary processing files

### 3. External Storage (Optional Cloud Integration)
- **AWS S3** / **Google Cloud Storage** - Raw payload archival
- **Azure Blob Storage** - Long-term retention
- **Earth Engine Asset Store** - Precomputed Dynamic World composites

---

## System Characteristics

### Performance
- **Ingestion Latency**: <2 seconds per FIRMS poll (typically 20-50 events)
- **API Response Time**: <100ms for cached events, <500ms for enriched events
- **Concurrent Users**: 50+ simultaneous frontend users
- **Data Retention**: 2 years configurable (730 days)

### Scalability
- **Horizontal Scaling**: Stateless API workers behind load balancer
- **Database Scaling**: PostgreSQL read replicas for analytics
- **Caching**: Redis layer available for frequent queries
- **Background Workers**: Separate worker pools for enrichment/ML

### Reliability
- **Fault Tolerance**: Graceful degradation when external APIs fail
- **Data Loss Prevention**: Immutable raw payload storage
- **Recovery**: Idempotent operations allow safe retries
- **Monitoring**: Health checks, metrics, structured logging

### Security
- **API Authentication**: Planned for Stage 2 (API keys/JWT)
- **Data Encryption**: TLS in transit, optional at-rest encryption
- **Input Validation**: Strict validation on all API endpoints
- **Audit Trail**: Complete provenance tracking for all events

---

## Future Enhancements (Stage 2+)

### Planned Features
1. **Stage 1B**: Full OSM and Dynamic World enrichment pipeline
2. **Stage 2**: Trained ML model for 5-class direct SIH classification
3. **Stage 3**: Risk scoring and prediction modeling
4. **Stage 4**: Alerting and notification system
5. **Stage 5**: Mobile app and field reporting integration

### Technical Improvements
1. **Microservices**: Split backend into independent services
2. **Event Streaming**: Apache Kafka for real-time data pipelines
3. **Data Warehouse**: Apache Parquet/Delta Lake for analytics
4. **Machine Learning**: Online learning and model retraining
5. **Observability**: Distributed tracing (Jaeger/OpenTelemetry)

---

## Troubleshooting Guide

### Common Issues
| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| No events in frontend | FIRMS collector not running | Check backend logs, verify `DEMO_MODE=false` and valid `FIRMS_MAP_KEY` |
| Empty historical data | Trigger not firing | Verify `03_historical_data.sql` migration applied, check table permissions |
| Slow API responses | Missing database indexes | Run `VACUUM ANALYZE;` on tables, check index usage |
| ML classification failures | Model files missing | Verify `docs/stage2d/models/` directory contents |
| Satellite preview errors | Sentinel service not configured | Check EARTH_ENGINE_PROJECT_ID and credentials |
| Database connection pool exhausted | Too many concurrent workers | Adjust `DB_POOL_MAX` in config, increase max_connections in PostgreSQL |

### Diagnostic Commands
```bash
# Check backend health
curl http://localhost:8000/api/v1/health/

# Check database status
psql -h localhost -U postgres -d sih26162 -c "SELECT COUNT(*) FROM thermal_events;"

# Check FIRMS collector logs
tail -f backend.log | grep FIRMS

# Verify trigger functionality
psql -h localhost -U postgres -d sih26162 -c "
  SELECT COUNT(*) FROM historical_data WHERE copied_at > NOW() - INTERVAL '1 hour';
"
```

---

## Glossary

- **FIRMS**: Fire Information for Resource Management System (NASA)
- **SIH**: Socially Innovative Hub (5-category classification system)
- **FRP**: Fire Radiative Power (measured in Megawatts)
- **PostGIS**: Geographic extension for PostgreSQL
- **GeoJSON**: Geographic data interchange format
- **NDVI**: Normalized Difference Vegetation Index
- **OSM**: OpenStreetMap
- **DW**: Dynamic World (Google Earth Engine land cover product)
- **EPSG:4326**: WGS84 geographic coordinate system
- **UUID**: Universally Unique Identifier
- **REST**: Representational State Transfer (API architecture)
- **CRUD**: Create, Read, Update, Delete operations
- **TPS**: Transactions Per Second
- **SLA**: Service Level Agreement

---

## Conclusion

FIREXIS represents a robust, scalable foundation for thermal event intelligence. The current implementation provides:

✅ **Verified ML model performance** with 99.50% test accuracy on the Stage 2 model  
✅ **Real-time FIRMS ingestion** with deterministic deduplication  
✅ **Automatic historical archiving** via database triggers  
✅ **Extensible architecture** for enrichment and ML pipelines  
✅ **Comprehensive API** for frontend consumption  
✅ **Production-ready deployment** scaffolding with monitoring and health checks  

The current evidence supports 99.50% test accuracy for the Stage 2 ML model. The latest persisted data contains 57 usable results among 128 enriched events (44.5%), and 57 among 577 eligible active events (9.9% current coverage); this includes one cached result and legacy rows whose cache/live distinction is unknown. With the bounded ±30-day fallback, the same 10-event cohort now has 4 usable results (40%): three confirmed fresh live and one cached. Two newly recovered scenes were 16 and 26 days older than their events; image age is returned by the provider but not yet stored with the enrichment row.

*Documentation generated: 2026-09-27*  
*System Version: 1.0.0-stage1a*  
*Current verified metric: ML accuracy 99.50%*  
*Usable persisted enrichment: 57/128 enriched events (44.5%); eligible-event coverage: 57/577 (9.9%)*