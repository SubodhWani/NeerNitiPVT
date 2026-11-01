import os
import sys

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_root)

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Region

regions_to_add = [
    {"name": "Varanasi", "lat": 25.3176, "lng": 82.9739},
    {"name": "Lucknow", "lat": 26.8467, "lng": 80.9462},
    {"name": "Kanpur Nagar", "lat": 26.4499, "lng": 80.3319},
    {"name": "Agra", "lat": 27.1767, "lng": 78.0081}
]

db: Session = SessionLocal()

for r in regions_to_add:
    existing = db.query(Region).filter_by(region_name=r["name"]).first()
    if not existing:
        # Create a rough bounding box
        lat = r["lat"]
        lng = r["lng"]
        w = lng - 0.2
        e = lng + 0.2
        n = lat + 0.2
        s = lat - 0.2
        poly_wkt = f"POLYGON(({w} {s}, {e} {s}, {e} {n}, {w} {n}, {w} {s}))"
        
        reg = Region(
            region_name=r["name"],
            region_type="district",
            state="Uttar Pradesh",
            boundary_geom=poly_wkt
        )
        db.add(reg)

db.commit()
db.close()
print("Added missing regions successfully!")
