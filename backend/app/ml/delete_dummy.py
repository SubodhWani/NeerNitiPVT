import sys
import os

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_root)

from app.db.session import SessionLocal
from app.db.models import Site

db = SessionLocal()
try:
    sites = db.query(Site).all()
    count = 0
    for s in sites:
        if s.explanation and s.explanation.shap_values == '{"slope_deg": 0.1234}':
            db.delete(s)
            count += 1
    db.commit()
    print(f"Deleted {count} dummy sites.")
except Exception as e:
    db.rollback()
    print("Error:", e)
finally:
    db.close()
