# STAGE 3 — CLAUDE CODE IMPLEMENTATION PROMPT

You are implementing **Stage 3 of SIH26162 — Thermal Event Intelligence Platform**.

Your job is to build the final dashboard/application layer based on the supplied Stage 3 specification and the reference dashboard screenshot.

## IMPORTANT: READ THIS FIRST

Before writing code:

1. Inspect the entire existing repository.
2. Identify the existing frontend framework and build system.
3. Identify any existing backend/API code.
4. Identify existing routes, components, services, assets, and configuration.
5. Read the existing Stage 1/1B documentation.
6. Determine what can be reused.
7. Do NOT blindly replace the project.
8. Do NOT rewrite working Stage 1/1B backend functionality.

The final result must be an implementation that can later be integrated with the user's existing PostgreSQL/PostGIS-backed system and Stage 2 ML system.

---

# 1. CRITICAL ENVIRONMENT CONSTRAINT

The PostgreSQL + PostGIS database is on the USER'S machine.

It is NOT available on your development machine.

Therefore:

### DO NOT

- Install PostgreSQL/PostGIS as a requirement for this Stage 3 implementation.
- Require a local PostgreSQL server.
- Hard-code a database connection.
- Put database credentials in frontend code.
- Rewrite the database schema.
- Create a second database architecture just for the dashboard.
- Make the application fail because PostgreSQL is unavailable.

### DO

- Build an API adapter/service layer.
- Use mock/demo data for development.
- Make the API base URL configurable.
- Keep real API integration replaceable.
- Make the complete dashboard demonstrable without PostgreSQL/PostGIS.
- Document exactly how the user will connect it later.

---

# 2. PRIMARY VISUAL TARGET

The supplied screenshot is the expected dashboard direction.

Build a polished application containing:

- Fire Intelligence branding
- Left sidebar
- Dashboard navigation
- Settings
- Fire classification section
- India-wide map
- Thermal event markers
- Risk legend
- Selected Detection panel
- Risk score
- Prediction + confidence
- Key factors
- Quick Summary
- Dynamic World land-cover donut chart
- Satellite image preview
- Dark mode
- Notification/login shell
- Responsive behavior

Do not make a generic admin dashboard.

The application should visually communicate:

**AI-powered thermal/fire intelligence across India.**

---

# 3. FIRE CLASSIFICATIONS

Support exactly these five UI classifications initially:

1. Industrial Fire
2. Wildfire / Natural Fire
3. Agricultural Fire
4. Persistent Thermal Source
5. Unknown / Other

Keep classifications data-driven.

Do not bury these labels across unrelated components.

---

# 4. MAP

Implement an India-focused interactive map.

Required:

- India view on initial load
- Zoom controls
- Layer control
- Map attribution
- Thermal event markers
- Risk visualization
- Clickable events
- Selected-event state
- Legend

Each event should support:

```text
event_id
latitude
longitude
classification
risk_score
risk_level
confidence
frp
persistence
industrial_context
water_context
land_cover
```

Only render fields that exist.

---

# 5. SELECTED DETECTION PANEL

Clicking a marker must select it.

Display:

### Location

- City/region when available
- State
- Country
- Latitude
- Longitude

### Risk

- Score /100
- Risk level
- Visual severity indicator

### Prediction

- Predicted class
- Confidence

Example UI:

```text
Prediction
Industrial Fire
91% Confidence
```

IMPORTANT:

If the real Stage 2 ML service is not connected, label demo values as demo/mock values.

Never present mock output as a real ML prediction.

---

# 6. KEY FACTORS

Create a reusable factor component.

Potential factors:

- High Thermal Intensity (FRP)
- Industrial Facility Nearby
- Land Cover
- Population Density
- Persistent Anomaly
- Water Proximity
- OSM Industrial Context
- Dynamic World Context

The component must gracefully handle missing values.

---

# 7. QUICK SUMMARY

Implement cards for:

- Total Detections
- Industrial Areas
- Weather Risk
- Low Risk

However, do not fabricate live statistics.

The architecture must allow statistics to come from APIs.

In demo mode, use mock values and visibly indicate demo mode where appropriate.

---

# 8. DYNAMIC WORLD

Implement a Dynamic World land-cover chart.

Support the nine Stage 1B classes:

- Water
- Trees
- Grass
- Flooded vegetation
- Crops
- Shrub & scrub
- Built
- Bare
- Snow & ice

Use a donut/pie visualization.

The chart must accept dynamic percentages.

Do not hard-code the displayed 87% Built example as a permanent value.

---

# 9. SATELLITE PREVIEW

Implement a satellite preview card.

States:

1. Real image available
2. Image URL unavailable
3. Loading
4. Error
5. Demo placeholder

When real metadata exists, display:

- Acquisition date
- Cloud percentage if available

Never label a demo placeholder as a real satellite image.

---

# 10. DARK MODE

Implement a real theme system.

Persist the user's preference if practical.

All components must remain readable in dark mode.

---

# 11. SETTINGS

Create a Settings page/screen.

At minimum:

- Theme
- Demo/real data state
- Configurable API base URL if appropriate
- Basic dashboard preferences

Never expose secrets.

---

# 12. API ARCHITECTURE

Create an abstraction similar to:

```text
src/
├── services/
│   ├── eventsService
│   ├── enrichmentService
│   ├── statisticsService
│   ├── predictionService
│   └── satelliteService
│
├── adapters/
│   ├── mockAdapter
│   └── apiAdapter
│
└── components/
```

Adapt this to the existing repository rather than forcing an exact folder structure.

The UI should never need to know whether data came from mock data or the real backend.

---

# 13. MOCK MODE

This is mandatory because PostgreSQL/PostGIS is unavailable on your machine.

Implement demo data containing:

- Multiple Indian thermal events
- Different fire classifications
- High/medium/low risks
- At least one selected event
- OSM-like contextual fields
- Dynamic World fields
- Satellite placeholder
- ML prediction placeholder

Keep mock data centralized.

Do not scatter fake values throughout UI components.

---

# 14. REAL API ADAPTER

Prepare a real API adapter.

The Stage 1/1B documentation indicates existing backend capabilities around:

- Events
- Enrichment
- Enrichment status
- Enrichment statistics
- Enriched events

Do not invent that an endpoint exists if you have not verified it in the repository.

If the exact response schema differs:

1. Keep the raw API response in the service layer.
2. Map it to a frontend domain model.
3. Keep the mapping isolated.

Do not rewrite the backend merely to match the UI.

---

# 15. STAGE 2 ML ADAPTER

Create a dedicated ML prediction service/adapter.

The expected conceptual shape is:

```json
{
  "event_id": "string",
  "predicted_class": "Industrial Fire",
  "confidence": 0.91,
  "risk_score": 87,
  "risk_level": "critical",
  "model_version": "string",
  "key_factors": []
}
```

This is NOT the final guaranteed Stage 2 schema.

Therefore:

- Make mapping configurable.
- Handle missing fields.
- Keep the service isolated.
- Do not train a model.
- Do not create a fake production ML model.
- Do not assume the final class names beyond the current five UI categories.
- Make the UI ready to consume the final Stage 2 output once supplied by the user.

---

# 16. DATA STATES

Every API-driven component needs:

### Loading

Show an appropriate skeleton/spinner.

### Empty

Explain that no data is available.

### Error

Show a useful error state and recovery action where appropriate.

### Demo

Clearly identify demo/mock information.

### Live

Display live/backend data normally.

Do not silently replace failed API responses with fake live-looking values.

---

# 17. RESPONSIVENESS

Desktop is the primary target.

Also support:

- Laptop
- Tablet
- Narrow browser width

On smaller screens:

- Collapse sidebar
- Convert Selected Detection panel into a drawer/modal
- Stack summary cards
- Keep map usable
- Preserve chart readability

---

# 18. CODE QUALITY

Follow the existing project's conventions.

Requirements:

- Reusable components
- Clear separation of UI/data services
- No unnecessary duplication
- No secrets in frontend
- No hard-coded database credentials
- Environment variables for configurable API URLs
- Proper error handling
- Proper loading states
- Clean TypeScript/types if the project uses TypeScript
- Avoid unnecessary dependencies
- Avoid destructive changes

---

# 19. VISUAL QUALITY CHECK

Compare your implementation against the supplied reference screenshot.

Check:

- Overall spacing
- Sidebar width
- Header
- Map prominence
- Selected panel
- Card proportions
- Typography hierarchy
- Icons
- Rounded corners
- Risk indicators
- Land-cover chart
- Satellite card
- Background
- Dark mode
- Responsive behavior

The result should look like a serious product, not a student CRUD dashboard.

---

# 20. DO NOT OVERBUILD

Do NOT implement now:

- ML training
- ML retraining
- Alert escalation
- Email/SMS notification infrastructure
- PostgreSQL/PostGIS setup
- New GIS ingestion pipelines
- New satellite-processing pipelines
- User authentication backend unless an existing implementation already exists
- Unrequested features that increase integration complexity

Focus on Stage 3.

---

# 21. TESTING

Before handoff:

1. Start the application locally.
2. Verify dashboard loads without PostgreSQL.
3. Verify demo mode.
4. Verify map renders.
5. Verify markers render.
6. Verify marker selection.
7. Verify Selected Detection panel.
8. Verify classification display.
9. Verify risk display.
10. Verify summary cards.
11. Verify Dynamic World chart.
12. Verify satellite placeholder.
13. Verify dark mode.
14. Verify Settings.
15. Test responsive layout.
16. Test loading/error/empty states.
17. Test API adapter configuration.

Fix obvious console/runtime errors.

---

# 22. HANDOFF REQUIREMENT

When the implementation is complete, prepare a clean Stage 3 package.

The user will receive the files as a ZIP.

The user will NOT integrate them immediately.

The intended sequence is:

```text
YOU FINISH STAGE 3
        ↓
CREATE ZIP
        ↓
SEND ZIP TO USER
        ↓
USER FINISHES STAGE 2
        ↓
USER EXTRACTS ZIP
        ↓
USER INTEGRATES STAGE 3
        ↓
CONNECTS EXISTING PostgreSQL/PostGIS BACKEND
        ↓
CONNECTS STAGE 2 ML
        ↓
FINAL SYSTEM TEST
```

Therefore, your handoff must be self-contained.

---

# 23. ZIP CONTENTS

Include all files necessary for the Stage 3 application.

Also include:

```text
README.md
.env.example
```

The README must explain:

- Installation
- Run commands
- Build commands
- Demo mode
- API configuration
- Real backend integration
- Stage 2 ML integration point
- Required environment variables
- Any manual merge/copy instructions
- Known limitations

Do not include:

- `.env` containing secrets
- PostgreSQL credentials
- API keys
- unnecessary build artifacts
- `node_modules`
- Python virtual environments

---

# 24. FINAL ACCEPTANCE CRITERIA

Before declaring Stage 3 complete, verify:

- [ ] Dashboard resembles supplied reference.
- [ ] Sidebar works.
- [ ] Fire classification section works.
- [ ] India map works.
- [ ] Thermal event markers work.
- [ ] Marker selection works.
- [ ] Selected Detection panel works.
- [ ] Risk score works.
- [ ] ML prediction UI exists.
- [ ] Confidence display works.
- [ ] Key factors work.
- [ ] Quick Summary works.
- [ ] Dynamic World chart works.
- [ ] Satellite preview works.
- [ ] Dark mode works.
- [ ] Settings works.
- [ ] Responsive behavior works.
- [ ] Demo mode works without PostgreSQL/PostGIS.
- [ ] API adapter layer works.
- [ ] Stage 2 adapter exists.
- [ ] No secrets are exposed.
- [ ] Existing Stage 1/1B code is preserved.
- [ ] No unnecessary database dependency exists.
- [ ] README is included.
- [ ] `.env.example` is included.
- [ ] ZIP-ready package is prepared.

---

# 25. FINAL OUTPUT FROM YOU

At the end of the implementation, report:

1. What you changed.
2. Which existing files you reused.
3. Which new files you created.
4. How demo mode works.
5. How the real API will be connected later.
6. Where the Stage 2 ML adapter is located.
7. How to run the Stage 3 application.
8. Any limitations.
9. Confirm that PostgreSQL/PostGIS is NOT required for Stage 3 development.
10. Confirm that the complete handoff package is ready to ZIP.

Do not claim the real ML system is integrated until the user provides the final Stage 2 model/API contract.

**Begin by inspecting the repository. Do not start by generating arbitrary new architecture.**
