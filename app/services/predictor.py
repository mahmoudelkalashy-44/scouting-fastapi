# app/services/predictor.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

from app.utils.helpers import age_phase_func

logger = logging.getLogger(__name__)

class PlayerPredictor:
    """كلاس للتنبؤ بأداء اللاعبين"""
    
    def __init__(self, models: Dict[str, Any]):
        self.models = models
        self.predict_df = models['predict_df']
        self.le = models['le']
        self.scalers = models.get('scalers', {})
        
    def _find_player(self, player_name: str) -> Optional[pd.Series]:
        """البحث عن لاعب في البيانات"""
        # بحث دقيق
        player_data = self.predict_df[
            self.predict_df['player'].str.lower() == player_name.lower()
        ]
        if not player_data.empty:
            return player_data.iloc[0].copy()
        
        # بحث تقريبي
        player_data = self.predict_df[
            self.predict_df['player'].str.contains(player_name, case=False, na=False)
        ]
        if not player_data.empty:
            return player_data.iloc[0].copy()
        
        return None
    
    def _get_reliability(self, num_seasons: int) -> str:
        """تحديد مستوى موثوقية التنبؤ"""
        if num_seasons >= 5:
            return "🟢 High"
        elif num_seasons >= 3:
            return "🟡 Medium"
        else:
            return "🔴 Low"
    
    def _prepare_features(self, p: pd.Series, pos: str, features: list, 
                          median_vals: pd.Series, scaler_name: Optional[str] = None) -> tuple:
        """تجهيز الميزات للتنبؤ"""
        # إضافة القيم التاريخية إذا موجودة
        if pos == 'GK':
            for col in ['avg_saves','avg_cs','avg_ga','std_saves','saves_per_match',
                       'cs_per_match','ga_per_match','saves_trend','cs_trend','ga_trend']:
                p[col] = p.get(col, 0)
        elif pos in ['DF', 'DF,MF', 'DF,FW']:
            for col in ['avg_tackles','avg_interceptions','avg_clearances','avg_aerial_pct',
                       'avg_blocks','std_tackles','std_interceptions','std_clearances',
                       'tackles_trend','intercept_trend','clearances_trend',
                       'aerials_trend','blocks_trend']:
                p[col] = p.get(col, 0)
        elif pos in ['MF', 'MF,DF', 'MF,FW']:
            for col in ['avg_key_passes_mf','avg_prog_passes','avg_sca','avg_gca',
                       'std_key_passes','std_prog_passes','std_sca','kp_trend',
                       'progp_trend','sca_trend','gca_trend','goals_trend',
                       'assists_trend','xG_trend']:
                p[col] = p.get(col, 0)
        else:  # FW
            p['pos_encoded'] = self.le.transform([p['pos']])[0] if p['pos'] in self.le.classes_ else -1
            for col in ['goals_trend','assists_trend','xG_trend']:
                p[col] = p.get(col, 0)
        
        # إنشاء DataFrame للتنبؤ
        X = pd.DataFrame([p[features]], columns=features).fillna(median_vals)
        
        # التطبيع إذا لزم
        if scaler_name and scaler_name in self.scalers:
            X_scaled = self.scalers[scaler_name].transform(X)
            return X_scaled, True
        return X, False
    
    def predict(self, player_name: str, metric: str) -> Optional[Dict[str, Any]]:
        """التنبؤ بأداء لاعب لمقياس محدد"""
        # البحث عن اللاعب
        p = self._find_player(player_name)
        if p is None:
            logger.warning(f"❌ Player '{player_name}' not found")
            return None
        
        pos = str(p['pos'])
        n = int(p.get('num_seasons', 1))
        reliability = self._get_reliability(n)
        p['age_phase'] = age_phase_func(p['age'])
        
        # تحديد النموذج والميزات حسب المركز والمقياس
        actual_val = 0.0
        features = []
        median_vals = None
        scaler_name = None
        model = None
        pos_type = None
        
        # ── حراس المرمى ──
        if pos == 'GK':
            pos_type = 'gk'
            if metric == 'saves':
                model, actual_val = self.models['model_gk_saves'], float(p.get('Saves', 0))
            elif metric == 'clean_sheets':
                model, actual_val = self.models['model_gk_cs'], float(p.get('Clean Sheets', 0))
            elif metric == 'goals_against':
                model, actual_val = self.models['model_gk_ga'], float(p.get('Goals Against', 0))
            features = self.models['features_gk']
            median_vals = self.models['gk_train_medians']
            
        # ── مدافعين ──
        elif pos in ['DF', 'DF,MF', 'DF,FW']:
            pos_type = 'df'
            if metric == 'tackles':
                model, actual_val = self.models['model_df_tackles'], float(p.get('Tackles Won', 0))
            elif metric == 'interceptions':
                model, actual_val = self.models['model_df_intercept'], float(p.get('Interceptions', 0))
            elif metric == 'clearances':
                model, actual_val = self.models['model_df_clearances'], float(p.get('Clearances', 0))
                scaler_name = 'df'  # LSTM needs scaling
            elif metric == 'aerial_pct':
                model, actual_val = self.models['model_df_aerials'], float(p.get('% Aerial Duels won', 0))
            elif metric == 'blocks':
                model, actual_val = self.models['model_df_blocks'], float(p.get('Shots blocked', 0))
            features = self.models['features_df']
            median_vals = self.models['df_train_medians']
            
        # ── وسط ──
        elif pos in ['MF', 'MF,DF', 'MF,FW']:
            pos_type = 'mf'
            if metric == 'goals':
                model, actual_val = self.models['model_mf_goals'], float(p.get('Goals', 0))
                scaler_name = 'mf'  # GRU needs scaling
            elif metric == 'assists':
                model, actual_val = self.models['model_mf_assists'], float(p.get('Assists', 0))
            elif metric == 'key_passes':
                model, actual_val = self.models['model_mf_kp'], float(p.get('Key passes', 0))
                scaler_name = 'mf'
            elif metric == 'progressive_passes':
                model, actual_val = self.models['model_mf_progp'], float(p.get('Progressive Passes', 0))
            elif metric == 'sca_p90':
                model, actual_val = self.models['model_mf_sca'], float(p.get('Shot creating actions p 90', 0))
                scaler_name = 'mf'
            elif metric == 'gca_p90':
                model, actual_val = self.models['model_mf_gca'], float(p.get('Goal creating actions p 90', 0))
                scaler_name = 'mf'
            features = self.models['features_mf']
            median_vals = self.models['mf_train_medians']
            
        # ── مهاجمين ──
        else:  # FW
            pos_type = 'fw'
            if metric == 'goals':
                model, actual_val = self.models['model_goals'], float(p.get('Goals', 0))
                scaler_name = 'field'  # GRU needs scaling
            elif metric == 'assists':
                model, actual_val = self.models['model_assists'], float(p.get('Assists', 0))
                scaler_name = 'field'
            features = self.models['features_field']
            median_vals = self.models['field_train_medians']
        
        if model is None or not features:
            logger.warning(f"⚠️ Metric '{metric}' not supported for position '{pos}'")
            return None
        
        # تجهيز البيانات والتنبؤ
        X, needs_scaling = self._prepare_features(p, pos, features, median_vals, scaler_name)
        
        if needs_scaling:
            pred_val = model.predict(X)[0][0]  # Deep learning models return nested array
        else:
            pred_val = model.predict(X)[0]  # Traditional models return scalar
        
        pred_val = max(0, round(float(pred_val), 1))
        delta = round(pred_val - actual_val, 1)
        
        # رسالة تحذيرية لو الموثوقية منخفضة
        message = None
        if n < 3:
            message = f"⚠️ Low reliability: Only {n} season(s) of data available"
        
        return {
            "player": p['player'],
            "squad": p['squad'],
            "pos": p['pos'],
            "age": int(p['age']),
            "pos_type": pos_type,
            "actual_value": actual_val,
            "predicted_value": pred_val,
            "delta": delta,
            "reliability": reliability,
            "num_seasons": n,
            "message": message
        }