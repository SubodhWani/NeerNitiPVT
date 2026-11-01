import sys
import os
import json

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_root)

from app.db.session import SessionLocal
from app.db.models import Explanation, Site

FEATURE_PHRASE_LOOKUP = {
    "slope_deg": ("gentle flat terrain which helps water settle", "steep slopes which makes water run off too fast"),
    "drainage_density": ("high natural drainage networks bringing water", "lack of natural streams nearby"),
    "ndvi": ("good amount of surface vegetation", "barren land with no vegetation"),
    "monsoon_rainfall_mm": ("heavy monsoon rainfall in this area", "low seasonal rainfall"),
    "rainfall_mm": ("heavy rainfall in this area", "low seasonal rainfall"),
    "distance_to_river_m": ("close proximity to river networks", "being very far from any surface water bodies"),
    "depth_to_groundwater_m": ("deep underground space available to store water", "shallow water levels that might cause flooding"),
    "geology_hardrock": ("fractured hard-rock layers", "soft sandy foundations"),
    "soil_clay_pct": ("good clay-rich soil that holds water", "very sandy soil that drains too quickly"),
    "twi": ("natural shape of the land that collects water well", "poor terrain shape for water collection"),
    "elevation_m": ("good low elevation for water flow", "high elevation making it hard for water to reach"),
    "flow_accumulation": ("high natural accumulation of water flow", "low water accumulation"),
    "delta_ndwi": ("strong historical surface water presence", "lack of historical surface water"),
    "delta_sar_vv_vh": ("good soil moisture retention", "poor soil moisture retention"),
    "curvature": ("bowl-shaped land that naturally pools water", "outward curving land that disperses water"),
    "sobel_fracture": ("natural ground fractures that help water seep underground", "solid ground with no cracks for water to enter"),
    "grace_gw_storage_cm": ("favorable regional groundwater storage trends", "declining regional groundwater levels")
}

def generate_simple_explanation(score: float, all_shap_features: list[tuple[str, float]]) -> str:
    positive_feats = [feat for feat, val in all_shap_features if val > 0]
    negative_feats = [feat for feat, val in all_shap_features if val < 0]
    
    # Get top 5 positive and top 2 negative for the explanation
    top_pos = positive_feats[:5]
    top_neg = negative_feats[:2]
    
    tier = "highly recommended" if score >= 0.75 else "moderately recommended" if score >= 0.50 else "not highly recommended"
    
    explanation = f"This location is {tier} for building a water recharge structure. "
    
    if top_pos:
        reasons = [FEATURE_PHRASE_LOOKUP.get(f, (f.replace('_', ' '),))[0] for f in top_pos]
        if len(reasons) > 1:
            reasons_str = ", ".join(reasons[:-1]) + ", and " + reasons[-1]
        else:
            reasons_str = reasons[0]
        explanation += f"The main factors making this a great site are its {reasons_str}. These natural conditions work together perfectly to capture rainwater and allow it to slowly seep into the ground. "
        
    if top_neg:
        concerns = [FEATURE_PHRASE_LOOKUP.get(f, ("", f.replace('_', ' ')))[1] for f in top_neg]
        if len(concerns) > 1:
            concerns_str = ", ".join(concerns[:-1]) + ", and " + concerns[-1]
        else:
            concerns_str = concerns[0]
        explanation += f"However, there is a minor challenge due to its {concerns_str}, but the positive factors strongly outweigh this."
        
    explanation += "\n\nOverall, building a structure here will be highly effective at storing monsoon runoff and raising the local groundwater level without any risk of waterlogging."
    return explanation

db = SessionLocal()
try:
    explanations = db.query(Explanation).all()
    count = 0
    for exp in explanations:
        site = db.query(Site).filter(Site.site_id == exp.site_id).first()
        if not site: continue
        
        score = site.suitability_score
        
        shap_vals = exp.shap_values
        if isinstance(shap_vals, str):
            try:
                shap_vals = json.loads(shap_vals)
            except:
                continue
                
        if not shap_vals: continue
            
        all_features = sorted(shap_vals.items(), key=lambda kv: kv[1], reverse=True) # Sort by value descending
        
        simple_text = generate_simple_explanation(score, all_features)
        
        exp.plain_text_summary = simple_text
        count += 1
        
    db.commit()
    print(f"Successfully updated {count} explanations to simple natural language!")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
