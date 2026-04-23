# app/services/model_loader.py
import joblib
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

class ModelLoader:
    """كلاس لإدارة تحميل النماذج والبيانات"""
    
    _instance = None
    _models = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_all(self) -> Dict[str, Any]:
        """تحميل كل النماذج والبيانات مرة واحدة"""
        if self._models is not None:
            logger.info("♻️ Returning cached models")
            return self._models
        
        logger.info("📦 Starting model loading...")
        
        # التحقق من الملفات
        if not settings.MODEL_PATH.exists():
            raise FileNotFoundError(f"❌ Models file not found: {settings.MODEL_PATH}")
        
        # 1. تحميل النماذج المحفوظة
        logger.info(f"🤖 Loading models from {settings.MODEL_PATH}")
        models = joblib.load(str(settings.MODEL_PATH))
        
        # 2. تحميل بيانات اللاعبين
        logger.info("📊 Loading player data...")
        predict_df = pd.read_csv(str(settings.PREDICT_DATA_PATH))
        injuries_df = pd.read_csv(str(settings.INJURIES_DATA_PATH))
        player_stats_df = pd.read_csv(str(settings.PLAYER_STATS_PATH))
        
        # 3. معالجة بيانات الإصابات
        logger.info("🏥 Processing injury data...")
        injuries_df['clean_name'] = injuries_df['player_name'].str.extract(r'^(.+?)\s*\(')[0]
        injuries_df['season_year'] = injuries_df['season_name'].apply(
            lambda s: int(str(s).split('/')[0]) + 2000 if '/' in str(s) else int(str(s).split('-')[0]) if '-' in str(s) else int(s)
        )
        injuries_df['injury_type'] = injuries_df['injury_reason'].apply(
            lambda r: 'muscle' if any(x in str(r).lower() for x in ['muscle','hamstring','thigh']) 
                     else 'knee' if any(x in str(r).lower() for x in ['knee','ligament','acl'])
                     else 'ankle' if any(x in str(r).lower() for x in ['ankle','foot'])
                     else 'other'
        )
        
        # 4. إضافة كل شيء للقاموس
        models.update({
            'predict_df': predict_df,
            'injuries_df': injuries_df,
            'player_stats_df': player_stats_df,
        })
        
        self._models = models
        logger.info(f"✅ Loaded {len(models)} keys | Players: {len(predict_df)}")
        return models
    
    def reload(self):
        """إعادة تحميل النماذج (للتطوير)"""
        self._models = None
        return self.load_all()
    
    @property
    def is_loaded(self) -> bool:
        return self._models is not None

# Instance singleton
model_loader = ModelLoader()