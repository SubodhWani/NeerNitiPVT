import sys
import os

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_root)

from app.db.session import SessionLocal
from app.db.models import Region, Site
from app.ml.run_multidistrict_inference import run_inference

db = SessionLocal()
varanasi = db.query(Region).filter_by(region_name="Varanasi").first()
print("Varanasi region:", varanasi.region_id if varanasi else "None")

# Run inference only for Varanasi by modifying the regions list temporarily
from unittest.mock import patch
def mock_get_regions():
    return [varanasi] if varanasi else []

with patch('app.ml.run_multidistrict_inference.SessionLocal') as mock_session:
    # Just run it directly, wait, run_inference queries db directly.
    pass

