import sys
import os
import random
from datetime import datetime, timezone

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_root)

from app.db.session import SessionLocal
from app.db.models import Region, Site, SiteFeature, Explanation
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

db = SessionLocal()
try:
    regions_to_add = ["Varanasi", "Lucknow", "Kanpur Nagar", "Agra"]
    for reg_name in regions_to_add:
        reg = db.query(Region).filter_by(region_name=reg_name).first()
        if not reg:
            continue
            
        base_lat, base_lng = 25.43, 81.84
        if reg.region_name == "Varanasi":
            base_lat, base_lng = 25.3176, 82.9739
        elif reg.region_name == "Lucknow":
            base_lat, base_lng = 26.8467, 80.9462
        elif reg.region_name == "Kanpur Nagar":
            base_lat, base_lng = 26.4499, 80.3319
        elif reg.region_name == "Agra":
            base_lat, base_lng = 27.1767, 78.0081

        for i in range(4):
            lat = base_lat + random.uniform(-0.06, 0.06)
            lng = base_lng + random.uniform(-0.06, 0.06)
            
            score = random.uniform(0.65, 0.95)
            
            site = Site(
                region_id=reg.region_id,
                location=from_shape(Point(lng, lat), srid=4326),
                suitability_score=round(score, 3),
                risk_category="Low",
                model_version_id="neerniti_up_v5.2_latest",
                created_at=datetime.now(timezone.utc)
            )
            db.add(site)
            db.flush()
            
            db.add(SiteFeature(
                site_id=site.site_id,
                slope_deg=random.uniform(0.5, 3.5),
                soil_type="Alluvial Loam",
                land_use="Agricultural",
                rainfall_mm=random.uniform(800, 1100),
                drainage_density=random.uniform(0.1, 0.8),
                geology_type="Quaternary Alluvium",
                depth_to_groundwater_m=random.uniform(5, 20)
            ))
            
            expl_text = "High suitability. Parameter contributions:\n- slope_deg (gentle terrain slope): +0.1234\n- ndvi (dense surface vegetation): +0.0567\n- rainfall_mm (strong regional precipitation): +0.0456\n- distance_to_river_m (close proximity to river network): +0.0890\n- depth_to_groundwater_m (deep aquifer holding capacity): +0.0765\n- geology_hardrock (alluvial sediment foundation): +0.0345\n- soil_clay_pct (porous sandy soil texture): +0.0234\n\nEngineering Advisory:\nHydrological modeling indicates optimal sub-surface infiltration kinetics. With gentle slope avoiding hydraulic scour and deep vadose zone holding capacity, the effective hydraulic conductivity supports rapid recharge without waterlogging."
            
            db.add(Explanation(
                site_id=site.site_id,
                shap_values='{"slope_deg": 0.1234}',
                plain_text_summary=expl_text,
                generated_at=datetime.now(timezone.utc)
            ))
            
    db.commit()
    print("Inserted dummy sites successfully!")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
