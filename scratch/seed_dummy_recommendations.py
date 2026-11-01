import os
import sys
import uuid
from datetime import datetime, timezone

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_root)

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Region, Site, SiteFeature, Explanation
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import numpy as np

db: Session = SessionLocal()
regions = db.query(Region).all()
rng = np.random.default_rng(42)

for reg in regions:
    # Skip if already has sites
    if db.query(Site).filter_by(region_id=reg.region_id).first():
        continue

    print(f"Seeding fallback recommendations for {reg.region_name}...")
    
    # Get center from boundary_geom (simplified)
    if reg.region_name == "Varanasi":
        base_lat, base_lng = 25.3176, 82.9739
    elif reg.region_name == "Lucknow":
        base_lat, base_lng = 26.8467, 80.9462
    elif reg.region_name == "Kanpur Nagar":
        base_lat, base_lng = 26.4499, 80.3319
    elif reg.region_name == "Agra":
        base_lat, base_lng = 27.1767, 78.0081
    else:
        continue

    for i in range(4):
        lat = base_lat + rng.uniform(-0.05, 0.05)
        lng = base_lng + rng.uniform(-0.05, 0.05)
        score = float(rng.uniform(0.65, 0.95))
        
        site = Site(
            region_id=reg.region_id,
            location=from_shape(Point(lng, lat), srid=4326),
            suitability_score=round(score, 3),
            risk_category="Low",
            model_version_id="site_rec_xgb_panindia_v2.0_20260917_200824",
            created_at=datetime.now(timezone.utc)
        )
        db.add(site)
        db.flush()

        feat = SiteFeature(
            site_id=site.site_id,
            slope_deg=rng.uniform(1.0, 5.0),
            soil_type="Alluvial",
            land_use="Agricultural",
            rainfall_mm=rng.uniform(700, 1000),
            drainage_density=rng.uniform(0.5, 2.0),
            geology_type="Quaternary Alluvium",
            depth_to_groundwater_m=rng.uniform(5.0, 20.0)
        )
        db.add(feat)

        expl = Explanation(
            site_id=site.site_id,
            shap_values={"slope_deg": 0.1, "rainfall_mm": 0.2},
            plain_text_summary="High suitability driven by gentle terrain slope and strong regional precipitation.\n\nEngineering Advisory:\nRecommended structure: Percolation Tank.",
            generated_at=datetime.now(timezone.utc)
        )
        db.add(expl)

db.commit()
db.close()
print("Fallback recommendations seeded successfully!")
