# app/services/injury_assessor.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

from app.utils.helpers import final_risk, injury_type, parse_season

logger = logging.getLogger(__name__)

class InjuryAssessor:
    """كلاس لتقييم خطر إصابة اللاعبين"""
    
    def __init__(self, models: Dict[str, Any]):
        self.models = models
        self.predict_df = models['predict_df']
        self.injuries_df = models['injuries_df']
        self.name_map = models.get('name_map', {})
        self.model_injury = models['model_injury']
        self.le_inj = models['le_inj']
        self.features_inj = models['features_inj']
        self.scalers = models.get('scalers', {})
        
    def _build_injury_features(self, player_clean_name: str, up_to_season: Optional[int] = None) -> dict:
        """بناء ميزات الإصابات للاعب معين"""
        pdf = self.injuries_df[self.injuries_df['clean_name'] == player_clean_name].copy()
        if up_to_season:
            pdf = pdf[pdf['season_year'] <= up_to_season]
        
        empty = {
            'career_injuries': 0, 'career_days_missed': 0, 'career_games_missed': 0,
            'last1_injuries': 0, 'last1_days_missed': 0,
            'last2_injuries': 0, 'last2_days_missed': 0,
            'last3_injuries': 0, 'last3_days_missed': 0,
            'muscle_injury_ratio': 0.0, 'knee_injury_ratio': 0.0, 'ankle_injury_ratio': 0.0,
            'avg_days_per_injury': 0.0, 'max_injury_days': 0,
            'had_serious_injury': 0, 'had_very_serious_injury': 0,
            'injury_trend': 0, 'injury_acceleration': 0,
            'seasons_with_injury': 0, 'injury_free_seasons': 0,
            'consecutive_injured_seasons': 0, 'days_missed_per_season': 0.0,
        }
        
        if pdf.empty:
            return empty
        
        career_injuries = len(pdf)
        career_days_missed = int(pdf['days_missed'].sum())
        career_games_missed = int(pdf['games_missed'].sum())
        
        if up_to_season:
            last1 = pdf[pdf['season_year'] == up_to_season]
            last2 = pdf[pdf['season_year'] >= up_to_season - 1]
            last3 = pdf[pdf['season_year'] >= up_to_season - 2]
        else:
            max_s = pdf['season_year'].max()
            last1 = pdf[pdf['season_year'] == max_s]
            last2 = pdf[pdf['season_year'] >= max_s - 1]
            last3 = pdf[pdf['season_year'] >= max_s - 2]
        
        total = len(pdf)
        muscle_ratio = len(pdf[pdf['injury_type'] == 'muscle']) / total if total > 0 else 0
        knee_ratio = len(pdf[pdf['injury_type'] == 'knee']) / total if total > 0 else 0
        ankle_ratio = len(pdf[pdf['injury_type'] == 'ankle']) / total if total > 0 else 0
        avg_days = float(pdf['days_missed'].mean()) if total > 0 else 0
        max_days = int(pdf['days_missed'].max()) if total > 0 else 0
        had_serious = int(max_days >= 30)
        had_very = int(max_days >= 60)
        
        by_season = pdf.groupby('season_year')['days_missed'].sum().reset_index()
        trend = int(by_season['days_missed'].iloc[-1] - by_season['days_missed'].iloc[-2]) if len(by_season) >= 2 else 0
        acceleration = int((by_season['days_missed'].iloc[-1] - by_season['days_missed'].iloc[-2]) - 
                          (by_season['days_missed'].iloc[-2] - by_season['days_missed'].iloc[-3])) if len(by_season) >= 3 else 0
        
        all_seasons_inj = pdf['season_year'].nunique()
        num_seasons = len(by_season)
        injury_free = max(0, num_seasons - all_seasons_inj)
        
        seasons_sorted = sorted(by_season['season_year'].tolist(), reverse=True)
        consec = 0
        for idx, yr in enumerate(seasons_sorted):
            if idx == 0 or yr == seasons_sorted[idx-1] - 1:
                consec += 1
            else:
                break
        
        return {
            'career_injuries': career_injuries, 'career_days_missed': career_days_missed,
            'career_games_missed': career_games_missed,
            'last1_injuries': len(last1), 'last1_days_missed': int(last1['days_missed'].sum()) if len(last1) > 0 else 0,
            'last2_injuries': len(last2), 'last2_days_missed': int(last2['days_missed'].sum()) if len(last2) > 0 else 0,
            'last3_injuries': len(last3), 'last3_days_missed': int(last3['days_missed'].sum()) if len(last3) > 0 else 0,
            'muscle_injury_ratio': round(muscle_ratio, 3), 'knee_injury_ratio': round(knee_ratio, 3),
            'ankle_injury_ratio': round(ankle_ratio, 3), 'avg_days_per_injury': round(avg_days, 1),
            'max_injury_days': max_days, 'had_serious_injury': had_serious,
            'had_very_serious_injury': had_very, 'injury_trend': trend,
            'injury_acceleration': acceleration, 'seasons_with_injury': all_seasons_inj,
            'injury_free_seasons': injury_free, 'consecutive_injured_seasons': consec,
            'days_missed_per_season': round(career_days_missed / max(num_seasons, 1), 1),
        }
    
    def _find_player_match(self, player_name: str) -> Optional[str]:
        """البحث عن تطابق لاسم اللاعب في خريطة الإصابات"""
        for k in self.name_map:
            if k.lower() == player_name.lower():
                return k
        return None
    
    def assess(self, player_name: str) -> Optional[Dict[str, Any]]:
        """تقييم خطر إصابة لاعب"""
        # البحث عن اللاعب في بيانات التنبؤ
        player_data = self.predict_df[
            self.predict_df['player'].str.lower() == player_name.lower()
        ]
        if player_data.empty:
            player_data = self.predict_df[
                self.predict_df['player'].str.contains(player_name, case=False, na=False)
            ]
        if player_data.empty:
            logger.warning(f"❌ Player '{player_name}' not found in predict data")
            return None
        
        p = player_data.iloc[0]
        pos_val = p.get('pos', 'Unknown')
        
        # ترميز المركز
        try:
            pos_enc = self.le_inj.transform([pos_val])[0] if pos_val in self.le_inj.classes_ else 0
        except:
            pos_enc = 0
        
        # البحث عن التطابق في خريطة الإصابات
        matched_key = self._find_player_match(player_name)
        
        # بناء ميزات الإصابات
        if matched_key and matched_key in self.name_map:
            clean_name = self.name_map[matched_key]
            inj_feats = self._build_injury_features(clean_name)
        else:
            inj_feats = self._build_injury_features("____not_found____")
        
        # تجهيز البيانات للتنبؤ
        row_dict = {
            'age': p.get('age', 0),
            'pos_enc_inj': pos_enc,
            'Matches Played': p.get('Matches Played', 0),
            'Avg Mins per Match': p.get('Avg Mins per Match', 0),
            'Progressive Carries': p.get('Progressive Carries', 0),
            'Tackles Won': p.get('Tackles Won', 0),
            'num_seasons': p.get('num_seasons', 1),
            **inj_feats,
        }
        
        X_pred = pd.DataFrame([row_dict])[self.features_inj].fillna(0)
        
        # التطبيع والتنبؤ
        if 'injury' in self.scalers:
            X_pred_scaled = self.scalers['injury'].transform(X_pred)
        else:
            X_pred_scaled = X_pred
        
        prob = self.model_injury.predict(X_pred_scaled)[0][0]
        label, pct = final_risk(
            prob, inj_feats['last1_days_missed'], inj_feats['last1_injuries'],
            inj_feats['career_days_missed'], inj_feats['career_injuries']
        )
        
        # نوع الإصابة السائد
        inj_types = {
            'Muscle': inj_feats['muscle_injury_ratio'],
            'Knee': inj_feats['knee_injury_ratio'],
            'Ankle': inj_feats['ankle_injury_ratio']
        }
        dominant = max(inj_types, key=inj_types.get)
        dominant_pct = round(inj_types[dominant] * 100)
        dominant_txt = f"{dominant} ({dominant_pct}%)" if dominant_pct > 0 else "Mixed"
        
        # توليد التوصية
        if label == "🔴 High Risk":
            recommendation = "⚠️ يوصى بإجراء فحص طبي دقيق قبل التوقيع"
        elif label == "🟡 Medium Risk":
            recommendation = "🟡 مراقبة اللياقة البدنية خلال المعسكر التحضيري"
        else:
            recommendation = "✅ لاعب ذو سجل إصابات منخفض، مناسب للتعاقد"
        
        return {
            "player": p['player'],
            "injury_risk_pct": pct,
            "risk_label": label,
            "last1_injuries": inj_feats['last1_injuries'],
            "last1_days_missed": inj_feats['last1_days_missed'],
            "career_injuries": inj_feats['career_injuries'],
            "career_days_missed": inj_feats['career_days_missed'],
            "avg_days_per_injury": inj_feats['avg_days_per_injury'],
            "had_very_serious_injury": bool(inj_feats['had_very_serious_injury']),
            "consecutive_injured_seasons": inj_feats['consecutive_injured_seasons'],
            "dominant_injury_type": dominant_txt,
            "has_injury_data": inj_feats['career_injuries'] > 0,
            "recommendation": recommendation
        }