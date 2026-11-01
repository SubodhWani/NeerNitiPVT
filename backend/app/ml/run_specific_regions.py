import sys
import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from shapely.geometry import Point
from geoalchemy2.shape import from_shape

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_root)

from app.db.session import SessionLocal
from app.db.models import Region, Site, SiteFeature, Explanation
from app.ml.module1_gee_extractor import get_live_gee_features
from app.ml.module4_risk_screening.buffer_analysis import ProximityAnalyzer
from app.ml.spatial_queries import query_distance_to_river_osm, query_nearest_groundwater_level
from app.ml.feature_engineering import engineer_all_features
from app.ml.llm_advisor import OpenRouterAdvisor
from app.ml.custom_model import NeerNitiModel
import shap

EXPECTED_FEATURES = [
    'delta_sar_vv_vh', 'delta_ndwi', 'slope_deg', 'curvature', 'sobel_fracture',
    'monsoon_rainfall_mm', 'soil_clay_pct', 'flow_accumulation', 'grace_gw_storage_cm',
    'distance_to_river_m', 'elevation_m', 'twi',
    'sar_ndwi_interaction', 'slope_flow_interaction', 'rain_gw_interaction', 'clay_slope_interaction',
    'dist_twi_interaction', 'elev_slope_interaction', 'sar_sq', 'ndwi_sq', 'slope_sq', 'rain_sq',
    'clay_sq', 'twi_sq', 'log_dist_river', 'log_flow_acc', 'log_elev', 'log_rain', 'sin_slope',
    'cos_slope', 'sar_ndwi_slope', 'rain_gw_clay', 'twi_flow_dist', 'elev_slope_curv',
    'sar_rain_interaction', 'ndwi_flow_interaction', 'slope_dist_interaction', 'clay_gw_interaction',
    'twi_rain_interaction', 'elev_dist_interaction', 'curv_flow_interaction', 'sar_clay_interaction',
    'ndwi_rain_interaction', 'slope_gw_interaction', 'rain_dist_interaction', 'clay_flow_interaction',
    'twi_gw_interaction', 'elev_rain_interaction', 'curv_dist_interaction', 'sar_flow_interaction',
    'ndwi_gw_interaction', 'slope_rain_interaction', 'clay_dist_interaction', 'twi_slope_interaction',
    'elev_gw_interaction', 'curv_rain_interaction', 'sar_dist_interaction', 'ndwi_slope_interaction',
    'rain_flow_interaction', 'clay_rain_interaction', 'twi_dist_interaction', 'elev_flow_interaction',
    'curv_gw_interaction', 'sar_gw_interaction', 'ndwi_dist_interaction', 'slope_curv_interaction',
    'rain_curv_interaction', 'clay_curv_interaction', 'twi_curv_interaction', 'elev_curv_interaction',
    'sar_curv_interaction', 'ndwi_curv_interaction', 'pca_1', 'pca_2', 'pca_3', 'cluster_id',
    'anomaly_score', 'geology_hardrock'
]

FEATURE_PHRASE_LOOKUP_EXT = {
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

def build_explanation_text(score: float, all_shap_features: list[tuple[str, float]]) -> str:
    positive_feats = [feat for feat, val in all_shap_features if val > 0]
    negative_feats = [feat for feat, val in all_shap_features if val < 0]
    
    top_pos = positive_feats[:5]
    top_neg = negative_feats[:2]
    
    tier = "highly recommended" if score >= 0.75 else "moderately recommended"
    
    explanation = f"This location is {tier} for building a water recharge structure. "
    
    if top_pos:
        reasons = [FEATURE_PHRASE_LOOKUP_EXT.get(f, (f.replace('_', ' '),))[0] for f in top_pos]
        if len(reasons) > 1:
            reasons_str = ", ".join(reasons[:-1]) + ", and " + reasons[-1]
        else:
            reasons_str = reasons[0]
        explanation += f"The main factors making this a great site are its {reasons_str}. These natural conditions work together perfectly to capture rainwater and allow it to slowly seep into the ground. "
        
    if top_neg:
        concerns = [FEATURE_PHRASE_LOOKUP_EXT.get(f, ("", f.replace('_', ' ')))[1] for f in top_neg]
        if len(concerns) > 1:
            concerns_str = ", ".join(concerns[:-1]) + ", and " + concerns[-1]
        else:
            concerns_str = concerns[0]
        explanation += f"However, there is a minor challenge due to its {concerns_str}, but the positive factors strongly outweigh this."
        
    return explanation

def run_specific_inference():
    db = SessionLocal()
    try:
        llm_advisor = OpenRouterAdvisor()
        model_wrapper = NeerNitiModel(module_name="site_recommendation")
        latest_pkl = os.path.join(os.path.dirname(__file__), "weights", "neerniti_up_v5.2_latest.pkl")
        
        import joblib
        data = joblib.load(latest_pkl)
        model = data.get("model", data)
        version_id = "neerniti_up_v5.2_latest"
        
        try:
            base_xgb = model.named_estimators_['xgb'].calibrated_classifiers_[0].estimator
            explainer = shap.TreeExplainer(base_xgb)
        except:
            explainer = None
            
        osm_analyzer = ProximityAnalyzer()

        target_regions = ["Lucknow", "Kanpur Nagar", "Agra"]
        regions = db.query(Region).filter(Region.region_name.in_(target_regions)).all()
        
        rng = np.random.default_rng(200)

        for reg in regions:
            regime = "alluvial"
            if reg.region_name == "Lucknow":
                base_lat, base_lng = 26.8467, 80.9462
            elif reg.region_name == "Kanpur Nagar":
                base_lat, base_lng = 26.4499, 80.3319
            elif reg.region_name == "Agra":
                base_lat, base_lng = 27.1767, 78.0081
            
            print(f"\n[INFO] Processing region: {reg.region_name} (Searching for safe >0.60 sites)")
            
            valid_sites_found = 0
            attempts = 0
            
            while valid_sites_found < 3 and attempts < 10:
                attempts += 1
                lat = float(base_lat + rng.uniform(-0.1, 0.1))
                lng = float(base_lng + rng.uniform(-0.1, 0.1))
                location_point = from_shape(Point(lng, lat), srid=4326)
                
                print(f"   [Attempt {attempts}] Sampling at [{lat:.4f}, {lng:.4f}]...")
                
                gee_metrics = get_live_gee_features(lat, lng, regime)
                osm_risk = osm_analyzer.compute_proximity(Point(lng, lat), district_name=reg.region_name)
                dist_river_m = query_distance_to_river_osm(lat, lng)
                gw_depth_m = query_nearest_groundwater_level(db, lat, lng, True)
                
                gee_metrics["depth_to_water_m"] = gw_depth_m
                gee_metrics["distance_to_river_m"] = dist_river_m 
                raw_feats = gee_metrics
                
                feat_78 = engineer_all_features(raw_feats, gw_depth_m, dist_river_m, regime)
                combined_feats = {**feat_78, **raw_feats}

                df_feat = pd.DataFrame([combined_feats])[EXPECTED_FEATURES]
                score = float(model.predict_proba(df_feat)[0, 1])
                
                db_risk_category = osm_risk.risk_category.replace(" Risk", "") if osm_risk.risk_category else "Medium"
                
                if db_risk_category == "High":
                    score -= 0.40
                elif db_risk_category == "Medium":
                    score -= 0.15
                    
                score = max(0.0, min(1.0, score))
                
                if score < 0.60:
                    print(f"      [Reject] Score {score:.2f} too low (Risk: {db_risk_category}). Searching again...")
                    continue
                    
                print(f"      [Accept] Safe site found! Score {score:.2f} (Risk: {db_risk_category})")
                
                if explainer:
                    shap_vals = explainer.shap_values(df_feat)
                    if isinstance(shap_vals, list):
                        shap_vals = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]
                    shap_row = shap_vals[0]
                else:
                    shap_row = [0.0] * len(EXPECTED_FEATURES)

                all_features = sorted(zip(EXPECTED_FEATURES, shap_row), key=lambda kv: abs(kv[1]), reverse=True)
                
                base_features = [
                    'delta_sar_vv_vh', 'delta_ndwi', 'slope_deg', 'curvature', 'sobel_fracture',
                    'monsoon_rainfall_mm', 'soil_clay_pct', 'flow_accumulation', 'grace_gw_storage_cm',
                    'distance_to_river_m', 'elevation_m', 'twi'
                ]
                filtered_features = [feat for feat in all_features if feat[0] in base_features or feat[0] in combined_feats]
                shap_summary_text = build_explanation_text(score, filtered_features[:12])
                
                shap_dict = {k: float(v) for k, v in zip(EXPECTED_FEATURES, shap_row)}
                
                site = Site(
                    region_id=reg.region_id,
                    location=location_point,
                    suitability_score=round(score, 3),
                    risk_category=db_risk_category,
                    model_version_id=version_id,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(site)
                db.flush()

                feat_record = SiteFeature(
                    site_id=site.site_id,
                    slope_deg=raw_feats["slope_deg"],
                    soil_type="Alluvial Loam",
                    land_use="Agricultural",
                    rainfall_mm=raw_feats["monsoon_rainfall_mm"],
                    drainage_density=raw_feats["flow_accumulation"],
                    geology_type="Quaternary Alluvium",
                    depth_to_groundwater_m=raw_feats["depth_to_water_m"]
                )
                db.add(feat_record)

                expl_record = Explanation(
                    site_id=site.site_id,
                    shap_values=shap_dict,
                    plain_text_summary=shap_summary_text,
                    generated_at=datetime.now(timezone.utc)
                )
                db.add(expl_record)
                db.commit() # Commit each valid site immediately
                
                valid_sites_found += 1

    except Exception as e:
        print(f"[ERROR] Script failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_specific_inference()
