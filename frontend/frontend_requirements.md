Optimized tool selectionI’m narrowing this to the exact fields the UI reads so you can map your backend attributes one-to-one and merge only the ones the frontend actually needs.

## Required frontend data model

To make this dashboard work correctly, your backend data should map to these exact frontend fields. The app reads them from the adapter/service layer in `apiAdapter.js`, `eventsService.js`, `predictionService.js`, `satelliteService.js`, and `statisticsService.js`.

The frontend does not need all raw database fields. It needs only these selected attributes.

---

## 1) Event data required for map + detail panel

This is the most important object.

### Required event shape

```json
{
  "event_id": "string",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "location": {
    "city": "Pune",
    "state": "Maharashtra",
    "country": "India"
  },
  "classification": "Industrial Fire",
  "risk_score": 87,
  "risk_level": "critical",
  "confidence": 0.91,
  "frp": 74.2,
  "persistence": "Repeated anomaly over 5 days",
  "industrial_context": {
    "nearby_facilities": "MIDC Industrial Hub (120m)",
    "osm_proximity": "Within industrial zone"
  },
  "water_context": {
    "proximity": "Mutex Canal (920m)"
  },
  "land_cover": {
    "Built": 87,
    "Trees": 4,
    "Grass": 3,
    "Crops": 3,
    "Bare": 2,
    "Water": 1,
    "Snow & ice": 0,
    "Flooded vegetation": 0,
    "Shrub & scrub": 0
  },
  "satellite": {
    "available": true,
    "url": "https://example.com/image.jpg",
    "acquisition_date": "2026-08-24",
    "cloud_cover": 20
  },
  "color": "#ef4444"
}
```

### Field mapping guidance

| Frontend field | Backend alias the app accepts | Why it is needed |
|---|---|---|
| `event_id` | `id`, `event_id` | unique event identifier |
| `latitude` | `latitude`, `lat` | map plotting |
| `longitude` | `longitude`, `lng` | map plotting |
| `location.city` | `location.city` | display in selected panel |
| `location.state` | `location.state` | display location |
| `location.country` | `location.country` | display location |
| `classification` | `classification`, `class` | filter and fire type display |
| `risk_score` | `risk_score` | risk badge and score card |
| `risk_level` | `risk_level` | coloring and label |
| `confidence` | `confidence` | prediction confidence display |
| `frp` | `frp` | factor display, heat intensity |
| `persistence` | `persistence` | factor display |
| `industrial_context` | `industrial_context` | contextual details |
| `water_context` | `water_context` | contextual details |
| `land_cover` | `land_cover` | donut chart |
| `satellite` | `satellite` | preview image and metadata |

### Important backend merge rule

If your backend has different names, merge like this:

- `event_id = event.id ?? event.event_id`
- `latitude = event.latitude ?? event.lat`
- `longitude = event.longitude ?? event.lng`
- `classification = event.classification ?? event.class`

This is exactly how the app normalizes data in `apiAdapter.js`.

---

## 2) Prediction data required for ML panel

This is used in the selected detection prediction section.

### Required prediction object

```json
{
  "event_id": "evt_001",
  "predicted_class": "Industrial Fire",
  "confidence": 0.91,
  "risk_score": 87,
  "risk_level": "critical",
  "model_version": "v2.1.4-production",
  "key_factors": [
    {
      "factor": "High Thermal Intensity (FRP)",
      "value": "High (74.2)"
    }
  ]
}
```

### Required fields

- `predicted_class`
- `confidence`
- `risk_score`
- `risk_level`
- `model_version`
- `key_factors`

### `key_factors` shape the UI expects

```json
[
  { "name": "High Thermal Intensity (FRP)", "value": "High" },
  { "factor": "Industrial Facility Nearby", "value": "Yes" }
]
```

The app reads either:
- `factor.name` or `factor.factor`
- then `value`

This flexibility matters for backend compatibility.

---

## 3) Satellite data required for preview card

### Required shape

```json
{
  "event_id": "evt_001",
  "available": true,
  "url": "https://example.com/sentinel-image.jpg",
  "acquisition_date": "2026-08-24",
  "cloud_cover": 20
}
```

### Required fields

- `available`
- `url`
- `acquisition_date`
- `cloud_cover`

Frontend behavior:
- if `available` is true and URL is valid, show image
- otherwise show placeholder state
- date and cloud cover shown in footer if present

---

## 4) Dashboard statistics required

### Required stats object

```json
{
  "totalDetections": 32,
  "industrialCount": 14,
  "highRiskCount": 8,
  "lowRiskCount": 15,
  "averageRiskScore": 62,
  "demoMode": false
}
```

The app accepts snake_case or camelCase:
- `total_detections` or `totalDetections`
- `industrial_count` or `industrialCount`
- `high_risk_count` or `highRiskCount`
- `low_risk_count` or `lowRiskCount`
- `average_risk_score` or `averageRiskScore`

These values power the quick summary cards.

---

## 5) Land cover data required

This data drives the Dynamic World donut chart.

### Required shape

```json
{
  "Built": 87,
  "Trees": 4,
  "Grass": 3,
  "Crops": 3,
  "Bare": 2,
  "Water": 1,
  "Snow & ice": 0,
  "Flooded vegetation": 0,
  "Shrub & scrub": 0
}
```

### Valid keys the app supports

- `Water`
- `Trees`
- `Grass`
- `Flooded vegetation`
- `Crops`
- `Shrub & scrub`
- `Built`
- `Bare`
- `Snow & ice`

If your backend gives a different nested structure, flatten it before sending to the frontend.

---

## 6) Config values the frontend reads

From `config.js`:

```json
{
  "isDemoMode": true,
  "apiBaseUrl": "http://localhost:8000/api",
  "mlServiceUrl": "http://localhost:5000/predict",
  "mapDefaultCenter": [22.9734, 78.6569],
  "mapDefaultZoom": 5,
  "theme": "light"
}
```

These are optional for basic UI but required for settings and live backend switching.

---

## 7) Minimum fields needed for a fully working dashboard

If you want the absolute minimum working dataset, include these:

### For events
- `event_id`
- `latitude`
- `longitude`
- `location.city`
- `location.state`
- `location.country`
- `classification`
- `risk_score`
- `risk_level`
- `confidence`

### For prediction
- `predicted_class`
- `confidence`
- `risk_score`
- `risk_level`
- `key_factors`

### For satellite
- `available`
- `url`
- `acquisition_date`
- `cloud_cover`

### For statistics
- `totalDetections`
- `industrialCount`
- `highRiskCount`
- `lowRiskCount`

---

## 8) Best way to map your backend attributes

Use this conversion pattern:

1. Keep your backend schema as-is
2. Build a frontend-normalization layer
3. Convert each field into frontend names before rendering

Example:

```js
const normalizedEvent = {
  event_id: raw.id || raw.event_id,
  latitude: raw.latitude ?? raw.lat,
  longitude: raw.longitude ?? raw.lng,
  location: raw.location || {
    city: raw.city,
    state: raw.state,
    country: raw.country
  },
  classification: raw.classification || raw.class,
  risk_score: raw.risk_score ?? raw.riskScore,
  risk_level: raw.risk_level || raw.riskLevel,
  confidence: raw.confidence ?? raw.conf,
  frp: raw.frp,
  persistence: raw.persistence,
  industrial_context: raw.industrial_context || {},
  water_context: raw.water_context || {},
  land_cover: raw.land_cover || {},
  satellite: raw.satellite || {}
};
```

This is the safest approach because the UI already expects a normalized contract.

---

## 9) My recommendation

Use this exact frontend contract as your target API schema:

- Event list: `events[]`
- Single event: `event`
- Prediction: `prediction`
- Satellite: `satellite`
- Stats: `statistics`
- Land cover: `land_cover`

Then create a mapping adapter from your backend fields to this contract.

> This is the cleanest approach because the UI is already built around normalized names, and you can adapt different backend tables without rewriting the frontend.

If you want, I can next give you a “backend-to-frontend field mapping template” in JSON and JavaScript form for your exact API schema.