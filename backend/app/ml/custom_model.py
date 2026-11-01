from sklearn.base import BaseEstimator, ClassifierMixin
import numpy as np
from scipy.stats import norm

def norm_cdf(x):
    return norm.cdf(x)

class FactorizedPhysicsStackingEnsemble(BaseEstimator, ClassifierMixin):
    """
    Multiplicative 3-Stack Physics-Guided Ensemble:
      1. Full 5-Model Stacking Ensemble + Continuous Depth Regressor for P(Headroom OK)
      2. Full 5-Model Stacking Ensemble + Continuous Rise Regressor for P(Volumetric Recharge OK)
      3. Full 5-Model Stacking Ensemble + Conditional Specialist for P(Subsurface OK)
      4. Multiplicative Geometric & Fuzzy-AND Fusion guarantees that a site cannot achieve high
         probability unless P(Headroom OK), P(Volumetric Recharge OK), and P(Subsurface OK)
         all simultaneously agree.
    """
    def __init__(self, splits, pos_weight, cb_config, vol_thresh, fusion_weights=None):
        self.splits = splits
        self.pos_weight = pos_weight
        self.cb_config = cb_config
        self.vol_thresh = vol_thresh
        self.fusion_weights = fusion_weights

    def _augment_stage1_features(self, X, pred_pre, pred_rech):
        X_aug = X.copy()
        sy = X_aug['specific_yield_est'].values
        req_rise = self.vol_thresh / np.clip(sy, 0.02, 0.22)
        pred_eff = pred_rech * sy

        p_head_reg = norm_cdf((pred_pre - 5.0) / 1.1) - norm_cdf((pred_pre - 35.0) / 2.0)
        p_vol_reg = norm_cdf((pred_rech - req_rise) / 0.30)

        X_aug['stage1_pred_pre_m'] = pred_pre
        X_aug['stage1_pred_rech_m'] = pred_rech
        X_aug['stage1_pred_eff_m'] = pred_eff
        X_aug['stage1_prob_headroom'] = p_head_reg
        X_aug['stage1_prob_vol'] = p_vol_reg
        X_aug['stage1_prob_joint'] = X_aug['surface_gate'].values * p_head_reg * p_vol_reg
        return X_aug

    def _make_5model_stack(self, pos_w=1.0, seed=42):
        cb_clf = CatBoostClassifier(**{**self.cb_config, 'scale_pos_weight': pos_w}, random_seed=seed)
        xgb_clf = XGBClassifier(
            n_estimators=360, max_depth=4, learning_rate=0.025,
            subsample=0.82, colsample_bytree=0.78, reg_lambda=12.0,
            scale_pos_weight=pos_w, random_state=seed, eval_metric="logloss"
        )
        lgb_clf = LGBMClassifier(
            n_estimators=360, max_depth=4, num_leaves=15, learning_rate=0.025,
            subsample=0.82, colsample_bytree=0.78, reg_lambda=12.0,
            scale_pos_weight=pos_w, random_state=seed, verbose=-1
        )
        rf_clf = make_pipeline(
            SimpleImputer(strategy='median'),
            RandomForestClassifier(n_estimators=320, max_depth=8, min_samples_leaf=4, class_weight='balanced_subsample', random_state=seed, n_jobs=-1)
        )
        et_clf = make_pipeline(
            SimpleImputer(strategy='median'),
            ExtraTreesClassifier(n_estimators=320, max_depth=8, min_samples_leaf=4, class_weight='balanced_subsample', random_state=seed, n_jobs=-1)
        )
        meta = make_pipeline(
            SimpleImputer(strategy='median'),
            StandardScaler(),
            LogisticRegression(penalty='l2', C=0.20, solver='lbfgs', max_iter=1000)
        )
        return StackingClassifier(
            estimators=[('cb', cb_clf), ('xgb', xgb_clf), ('lgb', lgb_clf), ('rf', rf_clf), ('et', et_clf)],
            final_estimator=meta,
            cv=self.splits,
            stack_method='predict_proba',
            n_jobs=-1
        )

    def fit(self, X, y, pre_m=None, rech_m=None, y_headroom=None, y_vol_recharge=None, y_subsurface=None):
        self.classes_ = np.array([0, 1])
        X_clean = X.reset_index(drop=True)
        y_sub_target = y_subsurface if y_subsurface is not None else y

        # Stage 1: Out-of-fold Continuous Subsurface Regressors (Depth & Rise)
        if pre_m is not None and rech_m is not None:
            self.has_stage1_ = True
            oof_pre = np.full(len(X_clean), np.nan)
            oof_rech = np.full(len(X_clean), np.nan)

            for tr, te in self.splits:
                r_pre_cb = CatBoostRegressor(iterations=350, depth=4, learning_rate=0.03, l2_leaf_reg=12, verbose=0, allow_writing_files=False, random_seed=42).fit(X_clean.iloc[tr], pre_m[tr])
                r_pre_lgb = LGBMRegressor(n_estimators=260, max_depth=4, num_leaves=15, learning_rate=0.03, reg_lambda=10.0, random_state=42, verbose=-1).fit(X_clean.iloc[tr], pre_m[tr])
                oof_pre[te] = 0.60 * r_pre_cb.predict(X_clean.iloc[te]) + 0.40 * r_pre_lgb.predict(X_clean.iloc[te])

                r_rech_cb = CatBoostRegressor(iterations=350, depth=4, learning_rate=0.03, l2_leaf_reg=12, verbose=0, allow_writing_files=False, random_seed=42).fit(X_clean.iloc[tr], rech_m[tr])
                r_rech_lgb = LGBMRegressor(n_estimators=260, max_depth=4, num_leaves=15, learning_rate=0.03, reg_lambda=10.0, random_state=42, verbose=-1).fit(X_clean.iloc[tr], rech_m[tr])
                oof_rech[te] = 0.60 * r_rech_cb.predict(X_clean.iloc[te]) + 0.40 * r_rech_lgb.predict(X_clean.iloc[te])

            oof_pre = np.where(np.isnan(oof_pre), np.nanmedian(pre_m), oof_pre)
            oof_rech = np.where(np.isnan(oof_rech), np.nanmedian(rech_m), oof_rech)

            self.reg_pre_cb_ = CatBoostRegressor(iterations=380, depth=4, learning_rate=0.03, l2_leaf_reg=12, verbose=0, allow_writing_files=False, random_seed=42).fit(X_clean, pre_m)
            self.reg_pre_lgb_ = LGBMRegressor(n_estimators=280, max_depth=4, num_leaves=15, learning_rate=0.03, reg_lambda=10.0, random_state=42, verbose=-1).fit(X_clean, pre_m)
            self.reg_rech_cb_ = CatBoostRegressor(iterations=380, depth=4, learning_rate=0.03, l2_leaf_reg=12, verbose=0, allow_writing_files=False, random_seed=42).fit(X_clean, rech_m)
            self.reg_rech_lgb_ = LGBMRegressor(n_estimators=280, max_depth=4, num_leaves=15, learning_rate=0.03, reg_lambda=10.0, random_state=42, verbose=-1).fit(X_clean, rech_m)

            X_stage2 = self._augment_stage1_features(X_clean, oof_pre, oof_rech)
        else:
            self.has_stage1_ = False
            X_stage2 = X_clean

        X_no_gate = X_stage2.drop(columns=['surface_gate'], errors='ignore')

        # Stack 1 & Stack 2: Full 5-Model Stacking Classifiers for P(Headroom OK) and P(Volumetric Recharge OK)
        if y_headroom is not None and y_vol_recharge is not None:
            self.has_factorized_ = True
            self.head_stack_ = self._make_5model_stack(pos_w=1.0, seed=42).fit(X_no_gate, y_headroom)
            self.vol_stack_ = self._make_5model_stack(pos_w=1.0, seed=100).fit(X_no_gate, y_vol_recharge)
        else:
            self.has_factorized_ = False

        # Stack 3A: Conditional Surface-Feasible Specialist (trained strictly on surface_gate == 1 sites, uninflated pos_weight=1.15)
        f_mask = (X_stage2['surface_gate'].values == 1.0)
        if np.sum(f_mask) >= 50 and len(np.unique(y[f_mask])) > 1:
            self.has_cond_specialist_ = True
            X_f = X_no_gate.iloc[f_mask]
            y_f = y[f_mask]
            self.cond_cb_ = CatBoostClassifier(iterations=420, depth=4, learning_rate=0.025, l2_leaf_reg=14, scale_pos_weight=1.15, verbose=0, allow_writing_files=False, random_seed=42).fit(X_f, y_f)
            self.cond_lgb_ = LGBMClassifier(n_estimators=320, max_depth=4, num_leaves=15, learning_rate=0.025, subsample=0.82, colsample_bytree=0.78, reg_lambda=12.0, scale_pos_weight=1.15, random_state=42, verbose=-1).fit(X_f, y_f)
            self.cond_xgb_ = XGBClassifier(n_estimators=320, max_depth=4, learning_rate=0.025, subsample=0.82, colsample_bytree=0.78, reg_lambda=12.0, scale_pos_weight=1.15, random_state=42, eval_metric="logloss").fit(X_f, y_f)
        else:
            self.has_cond_specialist_ = False

        # Stack 3B: All-Well 5-Model Stacking Classifier trained on uncorrupted subsurface_ok (uninflated pos_weight=1.15)
        self.sub_stack_ = self._make_5model_stack(pos_w=1.15, seed=2024).fit(X_no_gate, y_sub_target)
        return self

    def predict_components(self, X):
        """Returns [p_fact, p_fuzzy_min, p_joint_sub, p_prior, p_head, p_vol] and surface_gate."""
        X_clean = X.reset_index(drop=True)
        if getattr(self, 'has_stage1_', False):
            pred_pre = 0.60 * self.reg_pre_cb_.predict(X_clean) + 0.40 * self.reg_pre_lgb_.predict(X_clean)
            pred_rech = 0.60 * self.reg_rech_cb_.predict(X_clean) + 0.40 * self.reg_rech_lgb_.predict(X_clean)
            X_stage2 = self._augment_stage1_features(X_clean, pred_pre, pred_rech)
        else:
            X_stage2 = X_clean

        X_no_gate = X_stage2.drop(columns=['surface_gate'], errors='ignore')
        gate = X_clean['surface_gate'].values if 'surface_gate' in X_clean.columns else np.ones(len(X_clean))
        p_prior = X_clean['analytic_physics_prior'].values if 'analytic_physics_prior' in X_clean.columns else np.full(len(X_clean), 0.2)
        p_sub_stack = self.sub_stack_.predict_proba(X_no_gate)[:, 1]

        if getattr(self, 'has_cond_specialist_', False):
            p_cond = (
                0.45 * self.cond_cb_.predict_proba(X_no_gate)[:, 1] +
                0.30 * self.cond_lgb_.predict_proba(X_no_gate)[:, 1] +
                0.25 * self.cond_xgb_.predict_proba(X_no_gate)[:, 1]
            )
            p_joint_sub = 0.55 * p_sub_stack + 0.45 * p_cond
        else:
            p_joint_sub = p_sub_stack

        if getattr(self, 'has_factorized_', False):
            p_head_clf = self.head_stack_.predict_proba(X_no_gate)[:, 1]
            p_vol_clf = self.vol_stack_.predict_proba(X_no_gate)[:, 1]

            p_head = (
                0.55 * p_head_clf +
                0.25 * X_stage2['stage1_prob_headroom'].values +
                0.20 * (0.55 * X_clean['idw_headroom_prob'].values + 0.45 * X_clean['kriged_headroom_prob'].values)
            )
            p_vol = (
                0.55 * p_vol_clf +
                0.25 * X_stage2['stage1_prob_vol'].values +
                0.20 * (0.55 * X_clean['idw_site_vol_prob'].values + 0.45 * X_clean['kriged_site_vol_prob'].values)
            )
            p_fact = p_head * p_vol
            p_fuzzy_min = np.minimum(p_head, p_vol)
        else:
            p_fact = p_joint_sub
            p_fuzzy_min = p_joint_sub

        # Note: p_joint_sub is multiplicatively coupled with sqrt(p_fact) so it can never bypass the headroom/recharge veto!
        p_coupled_sub = np.sqrt(np.clip(p_joint_sub * p_fact, 0.0, 1.0))
        p_coupled_min = np.sqrt(np.clip(p_joint_sub * p_fuzzy_min, 0.0, 1.0))

        return np.column_stack([p_fact, p_coupled_sub, p_coupled_min, p_prior]), gate

    def predict_proba(self, X):
        comps, gate = self.predict_components(X)
        w = self.fusion_weights if self.fusion_weights is not None else np.array([0.35, 0.35, 0.15, 0.15])
        w = np.asarray(w, dtype=float) / np.sum(w)

        # Blend in both geometric (log-probability) and arithmetic spaces—every component is already multiplicatively gated!
        p_geom = np.exp(np.dot(np.log(np.clip(comps, 1e-4, 1.0)), w))
        p_arith = np.dot(comps, w)
        p_subsurface = 0.55 * p_geom + 0.45 * p_arith

        p_final = np.clip(p_subsurface * gate, 0.0, 1.0)
        return np.column_stack([1.0 - p_final, p_final])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

