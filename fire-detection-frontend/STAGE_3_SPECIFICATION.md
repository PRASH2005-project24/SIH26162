# SIH26162 — Stage 3 Dashboard & Application Specification

**Version:** 1.0  
**Stage:** Stage 3 — Dashboard / Application  
**Target:** SIH 2026 Thermal Event Intelligence Platform  
**Handoff:** Teammate → User, after Stage 3 implementation

---

## 1. Purpose

Stage 3 is responsible for building the final user-facing application around the already-developed SIH26162 backend capabilities.

The target visual output is the dashboard shown in the supplied reference screenshot:

- Left navigation/sidebar
- India-wide thermal-event map
- Fire/risk classification legend
- Selected detection details panel
- Quick summary cards
- Dynamic World land-cover visualization
- Satellite-image preview area
- Dark-mode control
- Settings/login shell
- Responsive, polished dashboard layout

Stage 3 must be implemented so that it can later be connected to the user's Stage 1/1B backend and Stage 2 ML system.

---

# 2. Critical Environment Constraint

## PostgreSQL/PostGIS is NOT installed on the Stage 3 developer's system.

The user's machine contains the PostgreSQL + PostGIS database and the completed Stage 1/1B backend.

Therefore:

### The Stage 3 developer MUST NOT:

- Require PostgreSQL to be installed locally.
- Require PostGIS locally.
- Rewrite the database schema.
- Create a second independent database implementation.
- Hard-code a local PostgreSQL connection.
- Assume database credentials are available.
- Make the dashboard unusable because the database is unavailable.

### The Stage 3 developer SHOULD:

- Build against API contracts/adapters.
- Use mock/demo data during Stage 3 development.
- Keep API integration configurable through environment variables.
- Create clean service/adapter layers so the real backend can be connected later.
- Make the UI fully demonstrable without PostgreSQL/PostGIS.

The final integration with the user's PostgreSQL/PostGIS environment will happen **after Stage 2 is completed and after the teammate hands over the Stage 3 files**.

---

# 3. Ownership Boundary

## Stage 3 owns

- Dashboard UI
- Frontend application
- Map visualization
- Event markers
- Risk visualization
- Detection detail panel
- Classification UI
- Summary/statistics cards
- Dynamic World visualization
- Satellite preview component
- Settings UI
- Dark mode
- Responsive design
- API service/adapters
- Mock/demo data layer
- Integration-ready ML result display
- Packaging and handoff

## Stage 3 does NOT own

- FIRMS data collection
- PostgreSQL/PostGIS installation
- Database schema redesign
- GIS enrichment implementation
- Dynamic World provider implementation
- ML model training
- ML model evaluation
- ML feature engineering
- Creating fake ML models that are presented as real predictions
- Production alerting system

---

# 4. Expected Dashboard

The supplied reference screenshot is the primary visual target.

The implementation should closely reproduce its information architecture and overall visual quality, while improving responsiveness and technical maintainability where appropriate.

## 4.1 Header

Display:

- Application branding: **Fire Intelligence**
- Subtitle: **AI Powered Fire Detection**
- Current date/time area
- Dark Mode toggle
- Notification icon
- Login/user control

The date/time should be generated dynamically rather than hard-coded.

---

# 5. Left Sidebar

The sidebar should contain:

## Branding

- Fire Intelligence logo/icon
- AI Powered Fire Detection subtitle

## Navigation

- Dashboard
- Settings

## Classification of Fire

Show the following five categories:

1. Industrial Fire
2. Wildfire / Natural Fire
3. Agricultural Fire
4. Persistent Thermal Source
5. Unknown / Other

Each category should have a visually distinct marker/icon.

The classification list must be data-driven so that the UI can later consume model classifications from Stage 2.

---

# 6. Main Map

The map is the most important component.

## Required behavior

Display an India-focused map with:

- Thermal event markers
- Risk-based marker styling
- Map zoom controls
- Layer control
- Map attribution
- Legend

The initial view should cover India.

## Marker information

Each marker should be capable of representing:

- Event ID
- Latitude
- Longitude
- Fire classification
- Risk score
- ML confidence
- FRP
- Persistence state
- Industrial proximity
- Land-cover information

Clicking a marker should select the event and populate the Selected Detection panel.

---

# 7. Risk Legend

The map should include a compact legend similar to the reference:

- High
- Medium
- Low
- Cluster

The exact visual treatment can be refined, but the legend must remain immediately understandable.

---

# 8. Selected Detection Panel

When a detection is selected, show a right-side panel.

It should include:

### Location

Example:

> Pune, Maharashtra, India

Also show:

- Latitude
- Longitude

### Risk

Display:

- Risk score out of 100
- Risk level
- Critical/high/medium/low state

### Prediction

Display:

- Predicted fire class
- ML confidence

Example:

> Industrial Fire — 91% confidence

The displayed prediction must come from the Stage 2 integration when available.

Do not fabricate a prediction and label it as an ML result.

### Key Factors

Display available factors such as:

- Thermal intensity / FRP
- Industrial facility nearby
- Land cover
- Population density
- Persistent anomaly
- OSM context
- Dynamic World context

Only display a factor when the corresponding data is actually available.

---

# 9. Quick Summary

Create a summary card section similar to the screenshot.

Possible cards:

### Total Detections

Number of currently available events.

### Industrial Areas

Number of detections associated with industrial areas.

### Weather Risk

Display only if weather data exists in the available backend/data contract.

### Low Risk

Number of low-risk detections.

The statistics must be calculated from API data when connected.

For demo mode, use clearly marked mock data.

Do not imply that mock statistics are live statistics.

---

# 10. Dynamic World Land Cover

Create a dedicated **Land Cover (Dynamic World)** card.

Display a donut/pie visualization for the available Dynamic World classes.

Support the nine Dynamic World classes already used by Stage 1B:

- Water
- Trees
- Grass
- Flooded vegetation
- Crops
- Shrub & scrub
- Built
- Bare
- Snow & ice

The chart should adapt to the actual returned class distribution.

For a selected detection, prioritize its local land-cover information.

---

# 11. Satellite Image Preview

Create a satellite preview card similar to the reference.

It should support:

- Image preview when an image URL/data source exists
- Placeholder state when no image is available
- Acquisition date when available
- Optional cloud information when available

Do NOT pretend that a placeholder image is a real satellite observation.

---

# 12. Settings

Create a functional Settings page/screen.

At minimum provide:

- Theme preference
- API/backend URL configuration if appropriate
- Demo mode indicator
- Basic dashboard preferences

Do not expose database credentials in the frontend.

---

# 13. Dark Mode

Dark mode should be functional.

The application should:

- Preserve the user's theme preference.
- Update all major dashboard components.
- Maintain readable contrast.
- Ensure maps/charts/panels remain usable.

---

# 14. API Integration Architecture

Use a service/adapter architecture.

Recommended conceptual structure:

```text
Frontend
   │
   ├── Event Service
   ├── Enrichment Service
   ├── Statistics Service
   ├── ML Prediction Service
   └── Satellite/Land-Cover Service
             │
             ▼
       API Adapter Layer
             │
       ┌─────┴─────┐
       ▼           ▼
   Mock/Demo     Real Backend
                 (later)
```

The UI must not directly contain raw database logic.

---

# 15. Existing Stage 1/1B Integration

The existing project documentation states that Stage 1/1B already provides APIs for:

- Thermal events
- FIRMS ingestion
- GIS enrichment
- Enrichment status
- Enrichment statistics
- Enriched-event queries

The Stage 3 implementation should therefore create an integration layer that can consume these APIs once connected to the user's system.

Do not rewrite the existing backend simply to make the frontend work.

---

# 16. Stage 2 ML Integration Contract

Stage 3 must be prepared for the Stage 2 ML output.

The frontend should be capable of receiving a prediction object conceptually containing:

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

This is an integration shape, not permission to invent final Stage 2 fields.

The final Stage 2 schema will be determined after the user completes ML development.

Therefore:

- Keep the ML adapter isolated.
- Make fields configurable/mappable.
- Gracefully handle missing fields.
- Do not hard-code a fake model.
- Do not train a model in Stage 3.

---

# 17. Mock/Demo Mode

Because PostgreSQL/PostGIS is unavailable on the teammate's system, Stage 3 must have a demo mode.

Demo mode should provide:

- Sample India map events
- Sample classifications
- Sample risk scores
- Sample enrichment values
- Sample land-cover distribution
- Sample selected-event details

The UI should visibly indicate that demo data is being used where appropriate.

The mock layer should be replaceable without rewriting the UI.

---

# 18. Responsiveness

The application must work on:

- Desktop
- Laptop
- Tablet
- Smaller browser widths

The desktop screenshot is the primary target.

On smaller screens:

- Sidebar may collapse.
- Selected Detection may become a drawer/modal.
- Cards may stack.
- Map must remain usable.

---

# 19. Visual Quality

Target:

- Clean modern dashboard
- Rounded cards
- Consistent spacing
- Professional typography
- Clear information hierarchy
- Subtle borders/shadows
- High-quality map presentation
- Consistent iconography
- Clear risk states
- No unnecessary visual clutter

The reference screenshot should be treated as the visual direction.

---

# 20. Technical Requirements

Before modifying the project:

1. Inspect the existing repository.
2. Identify the existing frontend technology.
3. Identify existing routes/components.
4. Identify existing backend/API structure.
5. Reuse existing components where sensible.
6. Avoid unnecessary framework migration.
7. Avoid destructive rewrites.
8. Preserve working Stage 1/1B code.

If a frontend already exists, improve/extend it rather than replacing it blindly.

---

# 21. Data Handling Rules

Every data-driven UI element must support:

- Loading state
- Empty state
- Error state
- Demo state
- Real-data state

Never display misleading zeros when data has failed to load.

Never expose backend secrets.

Never place PostgreSQL credentials in frontend code.

---

# 22. Handoff Package

When Stage 3 is complete, the teammate must provide the user with a ZIP containing **all Stage 3 files required to run and integrate the application**.

The ZIP should include:

```text
stage3/
├── frontend/
├── backend/                 # only if Stage 3 creates/changes backend code
├── public/
├── src/
├── assets/
├── mock/
├── services/
├── components/
├── README.md
├── .env.example
├── package.json
└── other required configuration
```

The exact structure should follow the actual project technology rather than forcing these directories if they are inappropriate.

---

# 23. Handoff README

The ZIP must contain a README explaining:

- How to install dependencies
- How to start the application
- How demo mode works
- Required environment variables
- API base URL configuration
- Which APIs are expected from Stage 1/1B
- Which ML fields are expected from Stage 2
- How to switch from mock APIs to real APIs
- Any files that the user must copy/merge
- Any known limitations

---

# 24. Important Handoff Timing

The teammate should NOT wait for the user's PostgreSQL/PostGIS environment to begin Stage 3.

She should complete the application using:

**Mock/demo data + API adapters.**

After the user completes Stage 2:

1. User receives the Stage 3 ZIP.
2. User extracts it.
3. User integrates the Stage 3 files into the main project.
4. User connects the frontend/API layer to the existing PostgreSQL/PostGIS-backed Stage 1/1B backend.
5. User connects the Stage 2 ML prediction interface.
6. Both sides are tested together.

---

# 25. Acceptance Criteria

Stage 3 is considered complete when:

- [ ] Dashboard visually follows the supplied reference.
- [ ] India map renders correctly.
- [ ] Thermal events appear on the map.
- [ ] Markers can be selected.
- [ ] Selected Detection panel works.
- [ ] Fire classifications are displayed.
- [ ] Risk score and confidence are displayed.
- [ ] Quick Summary works.
- [ ] Dynamic World chart works.
- [ ] Satellite preview works with fallback state.
- [ ] Dark mode works.
- [ ] Settings screen works.
- [ ] Responsive behavior works.
- [ ] Demo mode works without PostgreSQL/PostGIS.
- [ ] API adapter layer exists.
- [ ] Stage 2 ML integration point exists.
- [ ] No database credentials are exposed.
- [ ] Existing Stage 1/1B code is not unnecessarily rewritten.
- [ ] Application can be packaged independently.
- [ ] Complete ZIP handoff is produced.
- [ ] Handoff README is included.

---

# 26. Final Principle

**Stage 3 is the presentation and application layer.**

Do not rebuild the scientific/data/ML foundation.

The goal is to turn the existing thermal intelligence pipeline into a polished, usable dashboard that can consume:

**FIRMS → GIS enrichment → persistent thermal sources → Stage 2 ML predictions**

and present the results clearly to the end user.
