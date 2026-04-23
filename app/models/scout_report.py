# app/models/scout_report.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

GameStyleType = Literal[
    "Tiki-Taka", "Counter-Attack", "High Press", "Direct Play",
    "Pragmatic Possession", "Reactive", "Physical and Defensive",
    "Positional Play", "Catenaccio", "Counter Attacking", "Long Ball"
]

PlayerExperienceType = Literal["Veteran", "Experienced", "Young", "Promising"]

LeagueType = Literal["Serie A", "Ligue 1", "Premier League", "Bundesliga", "La Liga"]

FormationType = Literal[
    "4-3-1-2", "4-3-3", "3-5-2", "4-4-2", "3-4-3", 
    "5-3-2", "4-2-3-1", "4-3-2-1", "3-4-1-2", "3-4-2-1"
]

PlayerSkillType = Literal[
    "Key Passing", "Dribbling", "Speed", "Shooting", "Defending", "Aerial Ability",
    "Tackling", "Vision", "Long Passing", "Agility", "Strength", "Ball Control",
    "Positioning", "Finishing", "Crossing", "Marking", "Work Rate", "Stamina",
    "Free Kicks", "Leadership", "Penalty Saves", "Reactiveness", "Shot Stopping",
    "Off the Ball Movement", "Teamwork", "Creativity", "Game Intelligence"
]

class ScoutReportRequest(BaseModel):
    """طلب إنشاء تقرير كشفي"""
    base_player: str = Field(..., description="اللاعب الأساسي للمقارنة")
    game_style: GameStyleType = Field(description="أسلوب اللعب المطلوب")
    player_experience: PlayerExperienceType = Field(description="نوع الخبرة المطلوب")
    preferred_league: LeagueType = Field(description="الدوري المفضل")
    ideal_formation: FormationType = Field(description="التشكيلة المثالية")
    key_skills: List[PlayerSkillType] = Field(..., min_length=1, description="المهارات المطلوبة")
    groq_api_key: Optional[str] = Field(default=None, description="مفتاح Groq API (اختياري)")

class ScoutReportResponse(BaseModel):
    """رد التقرير الكشفي"""
    base_player: str = Field(description="اللاعب الأساسي")
    similar_players_analyzed: int = Field(description="عدد اللاعبين الذين تم تحليلهم")
    
    # التقرير النصي
    report_text: str = Field(description="التقرير الكشفي المولد")
    
    # اللاعب الموصى به
    recommended_player: Optional[str] = Field(default=None, description="اسم اللاعب الموصى به")
    
    # معلومات إضافية
    generation_time_ms: Optional[float] = Field(default=None, description="وقت التوليد بالميلي ثانية")
    model_used: str = Field(default="llama-3.3-70b-versatile", description="النموذج المستخدم")