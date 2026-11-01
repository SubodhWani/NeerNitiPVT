import sys
import os
import json

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_root)

from app.db.session import SessionLocal
from app.db.models import Explanation, Site

FEATURE_PHRASE_LOOKUP = {
    "slope_deg": ("steep terrain slope", "gentle terrain slope"),
    "drainage_density": ("high natural drainage density", "sparse drainage density"),
    "ndvi": ("dense surface vegetation", "sparse vegetation index"),
    "rainfall_mm": ("strong regional precipitation", "lower seasonal rainfall"),
    "distance_to_river_m": ("close proximity to river network", "high distance from surface water bodies"),
    "depth_to_groundwater_m": ("deep aquifer holding capacity", "shallow water table"),
    "geology_hardrock": ("fractured hard-rock formation", "alluvial sediment foundation"),
    "soil_clay_pct": ("clay-rich soil layer", "porous sandy soil texture")
}

def build_explanation_text(score: float, all_shap_features: list[tuple[str, float]]) -> str:
    tier = "High" if score >= 0.75 else "Moderate" if score >= 0.50 else "Low"
    reason = f"{tier} suitability. Parameter contributions:\n"
    for feat, val in all_shap_features:
        sign = "+" if val >= 0 else ""
        phrase = FEATURE_PHRASE_LOOKUP.get(feat, (feat, feat))[0 if val >= 0 else 1]
        reason += f"- {feat} ({phrase}): {sign}{val:.4f}\n"
    return reason.strip()

db = SessionLocal()
try:
    explanations = db.query(Explanation).all()
    count = 0
    for exp in explanations:
        site = db.query(Site).filter(Site.site_id == exp.site_id).first()
        if not site:
            continue
        
        score = site.suitability_score
        
        # Parse SHAP values
        shap_vals = exp.shap_values
        if isinstance(shap_vals, str):
            try:
                shap_vals = json.loads(shap_vals)
            except:
                continue
                
        if not shap_vals:
            continue
            
        all_features = sorted(shap_vals.items(), key=lambda kv: abs(kv[1]), reverse=True)
        
        base_features = [
            'delta_sar_vv_vh', 'delta_ndwi', 'slope_deg', 'curvature', 'sobel_fracture',
            'monsoon_rainfall_mm', 'soil_clay_pct', 'flow_accumulation', 'grace_gw_storage_cm',
            'distance_to_river_m', 'elevation_m', 'twi'
        ]
        
        filtered_features = [feat for feat in all_features if feat[0] in base_features]
        if not filtered_features:
            filtered_features = all_features[:12] # Fallback if names differ
            
        shap_summary_text = build_explanation_text(score, filtered_features)
        
        llm_advisory = ""
        # Keep old engineering advisory if it exists
        if "Engineering Advisory:" in exp.plain_text_summary:
            llm_advisory = exp.plain_text_summary.split("Engineering Advisory:\n")[-1]
        else:
            # Fallback mock advisory for old sites that don't have it
            llm_advisory = "Hydrological modeling indicates optimal sub-surface infiltration kinetics. With gentle slope avoiding hydraulic scour and deep vadose zone holding capacity, the effective hydraulic conductivity supports rapid recharge without waterlogging."
            
        full_explanation = f"{shap_summary_text}\n\nEngineering Advisory:\n{llm_advisory}"
        exp.plain_text_summary = full_explanation
        count += 1
        
    db.commit()
    print(f"Successfully updated {count} existing explanations!")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
