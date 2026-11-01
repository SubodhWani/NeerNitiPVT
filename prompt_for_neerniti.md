# NeerNiti Project Reconstruction Prompt - Ultimate Detailed Edition

*Provide the text below to your LLM to start building NeerNiti from scratch.*

***

**System Role:** You are an expert AI software engineer, data scientist, and geospatial developer. Your task is to build a complex, cloud-native, end-to-end artificial intelligence and geospatial decision-support system called **NeerNiti** (Satellite Telemetry and Deep Learning Platform for Sustainable Regional Groundwater Management).

---

### Step-by-Step Implementation Guide

Follow these highly specific, fine-grained requirements to build the architecture:

#### Phase 1: Project Setup & Infrastructure
1. **Directory Structure**: Create a monolithic repo with exactly `backend/` and `frontend/` directories.
2. **Database (Docker)**: Provide a `docker-compose.yml` for PostgreSQL 15 + PostGIS 3.3.
3. **Backend Packages (`backend/requirements.txt`)**: 
   `fastapi==0.115.12`, `uvicorn[standard]==0.34.2`, `pydantic==2.12.0`, `sqlalchemy==2.0.44`, `geoalchemy2==0.20.0`, `psycopg2-binary==2.9.12`, `alembic==1.17.0`, `shapely==2.1.2`, `python-socketio==5.16.4`, `catboost==1.2.8`, `xgboost==3.2.0`, `shap==0.51.0`, `tensorflow==2.21.0`, `earthengine-api==1.7.43`.
4. **Frontend Packages (`frontend/package.json`)**:
   `next: 14.2.35`, `deck.gl: ^9.0.0`, `react-map-gl: ^7.1.7`, `maplibre-gl: ^4.1.0`, `zustand: ^4.5.2`, `tailwindcss: ^3.4.1`, `recharts: ^2.12.3`, `socket.io-client: ^4.7.5`.

#### Phase 2: Backend REST API (FastAPI)
1. **App Initialization Hook**: Create `backend/main.py`. The FastAPI `lifespan` hook must initialize the ML engine (authenticate GEE, load models, initialize TreeExplainer). Integrate `python-socketio` as an ASGI app (`socketio.ASGIApp`). Implement global exception handlers for `ee.EEException` and `StarletteHTTPException`.
2. **Pydantic Schemas (`backend/app/models/schemas.py`)**:
   - Wrap all responses in an `ApiResponse[T]` containing `data` (Generic) and `error` (`ApiError` with `message`, `code`, `details`).
   - Define GeoJSON FeatureCollections strictly following RFC 7946. Ex: `SiteFeatureCollection` (contains `features: list[SiteFeature]`).
   - `SiteProperties`: Needs fields `recommendation_id`, `final_suitability_score`, `structure_type`, `risk_category`, `explanation_text`, `sub_scores: SubScores` (slope_score, ndvi_score, water_level_score).
   - `ExplanationDetail`: Needs `site_id`, `shap_values` (dict), `top_contributions` (list), `plain_text_summary` (str).
   - `SiteRecommendRequest`: Needs `region_id`, `polygon_geojson`, `min_suitability_score` (default 0.60), `risk_filter`, `top_n`.
3. **API Endpoints (`backend/app/api/v1/endpoints.py`)**:
   - `GET /api/v1/regions`: Returns `RegionFeatureCollection`.
   - `POST /api/v1/sites/recommend`: Enforce a hard threshold of `min_suitability_score >= 0.60`. It evaluates a Shapely spatial intersection and returns `SiteFeatureCollection`. Calculate structure type: if `slope_deg > 3.0` then "Check Dam", else "Percolation Tank".
   - Create dependencies `def get_db(): yield SessionLocal()`.
   - Implement `geometry_to_geojson_dict(spatial_column)` using `shapely.wkb.loads`.
4. **SQLAlchemy Models (`backend/app/models/domain.py`)**:
   - Use `geoalchemy2` for spatial storage. For `RechargeRecommendation`, the column is `location = Column(Geometry(geometry_type='POINT', srid=4326))`.

#### Phase 3: Machine Learning & Algorithms
1. **Module 1: Recommender (`custom_model.py`)**:
   - Implement `FactorizedPhysicsStackingEnsemble(BaseEstimator, ClassifierMixin)`. 
   - **Stage 1 (Subsurface Regressors)**: Train out-of-fold `CatBoostRegressor` (depth 4, lr 0.03) and `LGBMRegressor` (depth 4, num_leaves 15, lr 0.03) to predict Depth (pre_m) and Rise (rech_m). Combine them (0.60 CB + 0.40 LGBM). 
   - **Stage 2 (Meta Stacking)**: Create a `StackingClassifier` with base estimators: `CatBoostClassifier` (seed 42), `XGBClassifier` (360 estimators, depth 4, lr 0.025, reg_lambda 12.0), `LGBMClassifier` (360 estimators, depth 4), `RandomForestClassifier` (320 estimators, class_weight='balanced_subsample'), and `ExtraTreesClassifier`. Final estimator must be `LogisticRegression` with `penalty='l2'`.
2. **Module 2: Explainable AI (`module2_explainability`)**:
   - Hook `shap.TreeExplainer` into the CatBoost estimator. Generate plain-English driver statements for panchayat heads (e.g., "High slope permeability...").
3. **Module 3: Verification Engine**:
   - Create a TensorFlow `Bidirectional(LSTM)` forecasting pipeline trained on historical telemetry to predict the post-construction water level.
4. **Module 4: Risk Screening**:
   - Apply a Shapely `buffer(500)` filter to drop sites situated within 500 meters of known contamination zones.

#### Phase 4: Frontend Web GIS (Next.js)
1. **Zustand Store (`frontend/src/store/map-store.ts`)**:
   - Define exact state parameters: 
     `latitude` (25.4358), `longitude` (81.8463), `zoom` (10), `selectedRegionId`, `selectedDistrictName` ("Prayagraj"), `renderEngine` ("deckgl" | "leaflet"), `lowPerformanceMode` (bool).
     `showRegions`, `showWells`, `showRecommendations`, `showStructures` (all default true).
     `riskFilter` ("All" | "Low" | "Medium" | "High"), `minSuitabilityScore` (min 60).
     `siteDetailOpen`, `selectedSite`, `sidebarOpen`, `alertCount`.
2. **Map Render Engine**: Implement a dual rendering strategy using `react-map-gl` base and `deck.gl/react` overlays.
   - Use `GeoJsonLayer` for region borders and `HexagonLayer`/`IconLayer` for site coordinates.
3. **WebSockets (`socket.io-client`)**: Listen to the `/` namespace for backend broadcasts incrementing the `alertCount` state to display real-time toast notifications (e.g., "Data Ingestion Completed", "Verification Log Updated").
4. **UI Layout**: Build a responsive Tailwind CSS dashboard featuring Recharts curves comparing `Actual vs. Predicted` water levels and displaying the SHAP Civic Reasoning text cards.

**Strict Output Constraints:**
- Python code must feature full `typing` and docstrings.
- React components must be fully typed (TypeScript) Functional Components.
- Explicitly output the backend/frontend environment setup scripts and the Docker initiation command.
