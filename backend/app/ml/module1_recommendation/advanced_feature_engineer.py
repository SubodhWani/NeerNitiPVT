import math
import numpy as np

EXPECTED_FEATURES = [
    'surface_gate', 'analytic_physics_prior', 'fuzzy_and_prior', 'idw_coupled_joint_prob', 
    'idw_headroom_prob', 'kriged_headroom_prob', 'waterlogged_risk', 'idw_site_vol_prob', 
    'kriged_site_vol_prob', 'site_required_rise_m', 'rif_eff_recharge_m', 'site_coupled_eff_recharge_m', 
    'site_coupled_eff_regional_m', 'site_rise_surplus_m', 'site_rise_zscore', 'sat_pred_pre_m', 
    'sat_pred_rech_m', 'rk_pre_monsoon_m', 'rk_pre_monsoon_regional', 'idw_pre_monsoon_m', 
    'med_pre_monsoon_m', 'med_pre_monsoon_regional', 'idw_pre_monsoon_std', 'rk_recharge_m', 
    'rk_recharge_regional', 'idw_recharge_m', 'med_recharge_m', 'med_recharge_regional', 
    'q75_recharge_m', 'idw_recharge_std', 'idw_effective_recharge_m', 'local_elevation_anomaly_m', 
    'monsoon_rainfall_mm', 'rainy_days', 'late_rain_mm', 'rain_anomaly_mm', 'rain_intensity_mm_day', 
    'late_rain_fraction', 'effective_monsoon_soak_idx', 'late_rain_retention_idx', 'specific_yield_est', 
    'permeability_ratio_surface', 'permeability_ratio_subsurface', 'clay_vertical_gradient', 
    'sand_vertical_gradient', 'tpi_convergence_diff', 'tpi_local_vs_mid', 'infiltration_capacity_idx', 
    'runoff_capture_idx', 'hand_to_river_ratio', 'stress_to_rain_ratio', 'vadose_storage_proxy', 
    'alluvial_recharge_idx', 'drainage_density_proxy', 'stage_of_extraction', 'elevation_m', 
    'rain_clim_mm', 'slope_deg', 'curvature', 'tpi_250_m', 'tpi_1k_m', 'tpi_5k_m', 
    'soil_clay_0_5_pct', 'soil_clay_30_100_pct', 'soil_sand_0_5_pct', 'soil_sand_30_100_pct', 
    'soil_soc_0_5', 'soil_soc_30_100', 'dry_season_ndvi', 'crop_frac', 'built_frac', 'tree_frac', 
    'log_upstream_area', 'distance_to_river_m', 'hand_m', 'TWI', 'hydro_zone', 'pdf_hydro_zone'
]

def engineer_all_features(gee_metrics: dict, gw_depth_m: float, dist_river_m: float, regime: str) -> dict:
    """
    Maps 11 live GEE features into the 78-feature matrix required by the v5.2 model.
    Approximates spatial interpolations (Kriging/IDW) using local telemetry and physical priors.
    """
    f = {}
    
    # 1. Base GEE Mappings
    f['elevation_m'] = gee_metrics.get('elevation_m', 250.0)
    f['slope_deg'] = gee_metrics.get('slope_deg', 1.8)
    f['curvature'] = gee_metrics.get('curvature', 0.0)
    f['monsoon_rainfall_mm'] = gee_metrics.get('monsoon_rainfall_mm', 980.0)
    f['distance_to_river_m'] = dist_river_m
    f['TWI'] = gee_metrics.get('twi', 5.0)
    
    # 2. Soil & Lithology Approximations
    clay = gee_metrics.get('soil_clay_pct', 22.0)
    f['soil_clay_0_5_pct'] = clay
    f['soil_clay_30_100_pct'] = clay * 1.2  # typically more clay deeper
    f['soil_sand_0_5_pct'] = 100.0 - clay - 15.0 # rough estimate
    f['soil_sand_30_100_pct'] = max(0, f['soil_sand_0_5_pct'] - 5.0)
    f['soil_soc_0_5'] = 1.2
    f['soil_soc_30_100'] = 0.5
    f['clay_vertical_gradient'] = f['soil_clay_30_100_pct'] - f['soil_clay_0_5_pct']
    f['sand_vertical_gradient'] = f['soil_sand_30_100_pct'] - f['soil_sand_0_5_pct']
    
    sy = 0.12 if regime == "alluvial" else 0.02
    f['specific_yield_est'] = sy
    f['permeability_ratio_surface'] = f['soil_sand_0_5_pct'] / (f['soil_clay_0_5_pct'] + 1.0)
    f['permeability_ratio_subsurface'] = f['soil_sand_30_100_pct'] / (f['soil_clay_30_100_pct'] + 1.0)
    
    # 3. Rainfall & Hydrology
    rain = f['monsoon_rainfall_mm']
    f['rain_clim_mm'] = rain * 1.1
    f['rain_anomaly_mm'] = rain - f['rain_clim_mm']
    f['rainy_days'] = max(20, rain / 25.0)
    f['rain_intensity_mm_day'] = rain / f['rainy_days']
    f['late_rain_mm'] = rain * 0.3
    f['late_rain_fraction'] = 0.3
    f['effective_monsoon_soak_idx'] = (rain * f['soil_sand_0_5_pct']) / 1000.0
    f['late_rain_retention_idx'] = f['late_rain_mm'] * (f['soil_clay_0_5_pct'] / 100.0)
    f['runoff_capture_idx'] = gee_metrics.get('flow_accumulation', 1.0) * rain / 1000.0
    f['log_upstream_area'] = math.log10(gee_metrics.get('flow_accumulation', 1.0) * 900 + 1)
    
    # 4. Groundwater Interpolations (Approximated from PostGIS nearest point)
    gw = max(2.0, gw_depth_m)
    f['sat_pred_pre_m'] = gw
    f['sat_pred_rech_m'] = rain * 0.1 / sy
    f['rk_pre_monsoon_m'] = gw
    f['rk_pre_monsoon_regional'] = gw * 1.1
    f['idw_pre_monsoon_m'] = gw
    f['med_pre_monsoon_m'] = gw
    f['med_pre_monsoon_regional'] = gw
    f['idw_pre_monsoon_std'] = 2.5
    f['rk_recharge_m'] = f['sat_pred_rech_m']
    f['rk_recharge_regional'] = f['rk_recharge_m'] * 0.9
    f['idw_recharge_m'] = f['rk_recharge_m']
    f['med_recharge_m'] = f['rk_recharge_m']
    f['med_recharge_regional'] = f['rk_recharge_m']
    f['q75_recharge_m'] = f['rk_recharge_m'] * 0.8
    f['idw_recharge_std'] = 1.0
    f['idw_effective_recharge_m'] = f['idw_recharge_m'] * 0.8
    
    # 5. Suitability Priors & Probabilities (Simulating the Kriged outputs)
    headroom = gw - 3.0 # required to be safe from waterlogging
    f['kriged_headroom_prob'] = min(1.0, max(0.0, headroom / 10.0))
    f['idw_headroom_prob'] = f['kriged_headroom_prob']
    f['waterlogged_risk'] = 1.0 - f['idw_headroom_prob']
    
    f['kriged_site_vol_prob'] = min(1.0, max(0.0, (rain * 0.2) / 200.0))
    f['idw_site_vol_prob'] = f['kriged_site_vol_prob']
    f['idw_coupled_joint_prob'] = f['idw_headroom_prob'] * f['idw_site_vol_prob']
    
    f['surface_gate'] = 1.0 if f['slope_deg'] < 10.0 else 0.0
    f['analytic_physics_prior'] = f['idw_coupled_joint_prob'] * f['surface_gate']
    f['fuzzy_and_prior'] = min(f['idw_headroom_prob'], f['idw_site_vol_prob'])
    
    # 6. Topo & Morphometrics
    f['local_elevation_anomaly_m'] = -1.5 # assuming valleys are better
    f['tpi_250_m'] = -0.5
    f['tpi_1k_m'] = -1.0
    f['tpi_5k_m'] = -2.0
    f['tpi_convergence_diff'] = f['tpi_250_m'] - f['tpi_5k_m']
    f['tpi_local_vs_mid'] = f['tpi_250_m'] - f['tpi_1k_m']
    f['hand_m'] = max(0.0, f['elevation_m'] - 200.0)
    f['hand_to_river_ratio'] = f['hand_m'] / (dist_river_m + 1.0)
    
    # 7. Land Cover & Indices
    f['dry_season_ndvi'] = gee_metrics.get('delta_ndwi', 0.1) * 2.0
    f['crop_frac'] = 0.6 if regime == "alluvial" else 0.3
    f['built_frac'] = 0.1
    f['tree_frac'] = 0.1
    
    # 8. Hydro-Dynamics
    f['infiltration_capacity_idx'] = f['soil_sand_0_5_pct'] / (f['slope_deg'] + 1.0)
    f['vadose_storage_proxy'] = gw * sy
    f['alluvial_recharge_idx'] = f['vadose_storage_proxy'] if regime == "alluvial" else 0.0
    f['flow_accumulation'] = gee_metrics.get('flow_accumulation', 1.0)
    f['drainage_density_proxy'] = f['flow_accumulation'] / 100.0
    f['stage_of_extraction'] = 75.0 # safe
    f['stress_to_rain_ratio'] = f['stage_of_extraction'] / max(1.0, rain)
    f['site_required_rise_m'] = 2.0
    f['rif_eff_recharge_m'] = f['idw_effective_recharge_m'] * 0.9
    f['site_coupled_eff_recharge_m'] = f['rif_eff_recharge_m']
    f['site_coupled_eff_regional_m'] = f['rif_eff_recharge_m'] * 1.1
    f['site_rise_surplus_m'] = f['site_coupled_eff_recharge_m'] - f['site_required_rise_m']
    f['site_rise_zscore'] = f['site_rise_surplus_m'] / 0.5
    f['hydro_zone'] = 1 if regime == "alluvial" else 2
    f['pdf_hydro_zone'] = 0.8
    
    return {k: float(f.get(k, 0.0)) for k in EXPECTED_FEATURES}
