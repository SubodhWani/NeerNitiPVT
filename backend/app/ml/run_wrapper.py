import sys
import os

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_root)

from unittest.mock import patch
from app.db.session import SessionLocal
from app.db.models import Region

db = SessionLocal()
regions = db.query(Region).filter(Region.region_name.in_(["Lucknow", "Kanpur Nagar", "Agra"])).all()
db.close()

def mock_get_all():
    return regions

# We patch db.query(Region).all() with our own list
with patch('app.ml.run_multidistrict_inference.SessionLocal') as mock_session:
    # Wait, run_multidistrict_inference creates its own SessionLocal and queries it
    pass

import app.ml.run_multidistrict_inference
# Better way: replace the db.query(Region).all() line temporarily, run it, then revert it.

