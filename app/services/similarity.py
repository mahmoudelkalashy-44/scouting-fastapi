# app/services/similarity.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimilarityCalculator:
    """كلاس لحساب التشابه بين اللاعبين"""
    
    SELECTED_FEATURES = [
        'Pos', 'Age', 'Int', 'Clr', 'KP', 'PPA', 'CrsPA', 'PrgP', 'Playing Time MP',
        'Performance Gls', 'Performance Ast', 'Performance G+A', 'Performance G-PK',
        'Performance Fls', 'Performance Fld', 'Performance Crs', 'Performance Recov',
        'Expected xG', 'Expected npxG', 'Expected xAG', 'Expected xA', 'Expected A-xAG',
        'Expected G-xG', 'Expected np:G-xG', 'Progression PrgC', 'Progression PrgP',
        'Progression PrgR', 'Tackles Tkl', 'Tackles TklW', 'Tackles Def 3rd',
        'Tackles Mid 3rd', 'Tackles Att 3rd', 'Challenges Att', 'Challenges Tkl%',
        'Challenges Lost', 'Blocks Blocks', 'Blocks Sh', 'Blocks Pass',
        'Standard Sh', 'Standard SoT', 'Standard SoT%', 'Standard Sh/90',
        'Standard Dist', 'Standard FK', 'Performance GA', 'Performance SoTA',
        'Performance Saves', 'Performance Save%', 'Performance CS', 'Performance CS%',
        'Penalty Kicks PKatt', 'Penalty Kicks Save%', 'SCA SCA', 'GCA GCA',
        'Aerial Duels Won', 'Aerial Duels Lost', 'Aerial Duels Won%',
        'Total Cmp', 'Total Att', 'Total TotDist', 'Total PrgDist', '1/3'
    ]
    
    POS_MAPPING = {
        'GK': 1, 'DF,FW': 4, 'MF,FW': 8, 'DF': 2, 'DF,MF': 3, 
        'MF,DF': 5, 'MF': 6, 'FW,DF': 7, 'FW,MF': 9, 'FW': 10
    }
    
    def __init__(self, player_stats_df: pd.DataFrame):
        self.df = player_stats_df.copy()
        self._preprocess()
    
    def _preprocess(self):
        """معالجة مسبقة للبيانات"""
        # حفظ المركز الأصلي للعرض
        self.df['Pos_orig'] = self.df['Pos'].copy()
        
        # تعيين قيم رقمية للمراكز
        self.df['Pos'] = self.df['Pos'].map(self.POS_MAPPING).fillna(0)
        
        # التطبيع
        self.scaler = MinMaxScaler()
        self.df[self.SELECTED_FEATURES] = self.scaler.fit_transform(
            self.df[self.SELECTED_FEATURES].fillna(0)
        )
        
        # حساب مصفوفة التشابه
        self.similarity_matrix = cosine_similarity(self.df[self.SELECTED_FEATURES])
    
    def find_similar(self, player_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """إيجاد لاعبين مشابهين"""
        # البحث عن اللاعب
        mask = self.df['Player'].str.lower() == player_name.lower()
        if not mask.any():
            mask = self.df['Player'].str.contains(player_name, case=False, na=False)
        
        if not mask.any():
            logger.warning(f"❌ Player '{player_name}' not found in stats")
            return []
        
        idx = self.df[mask].index[0]
        
        # حساب التشابه
        similarities = list(enumerate(self.similarity_matrix[idx]))
        sorted_similar = sorted(similarities, key=lambda x: x[1], reverse=True)
        
        # إرجاع النتائج (بدون اللاعب نفسه)
        results = []
        for sim_idx, score in sorted_similar[1:limit+1]:
            player_row = self.df.iloc[sim_idx]
            results.append({
                "player": player_row['Player'],
                "squad": player_row['Squad'],
                "pos": player_row['Pos_orig'],
                "age": int(player_row['Age']) if pd.notna(player_row.get('Age')) and str(player_row['Age']).isdigit() else 0,
                "nation": player_row['Nation'],
                "similarity_score": round(float(score), 4)
            })
        
        return results