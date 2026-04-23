# app/config.py
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # مسارات الملفات
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # ملفات البيانات
    MODEL_PATH: Path = DATA_DIR / "all_models_optimized.joblib"
    PREDICT_DATA_PATH: Path = DATA_DIR / "predict_data_enhanced.csv"
    INJURIES_DATA_PATH: Path = DATA_DIR / "injuries_data.csv"
    PLAYER_STATS_PATH: Path = DATA_DIR / "football-player-stats-2023.csv"
    
    # إعدادات التطبيق
    API_TITLE: str = "⚽ Player Scouting Recommendation System"
    API_DESCRIPTION: str = "AI-Based Football Transfer Decision Support System - Using Best Models (GRU/LSTM/XGBoost/RF)"
    API_VERSION: str = "2.0.0"
    
    # إعدادات الـ API الخارجية
    GROQ_API_KEY: str = ""  # يوضع في ملف .env
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # إعدادات البحث
    FUZZY_MATCH_THRESHOLD: int = 90
    SIMILAR_PLAYERS_COUNT: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()