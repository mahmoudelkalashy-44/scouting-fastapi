# app/models/player.py
from pydantic import BaseModel, Field
from typing import Optional, List

class PlayerSearchRequest(BaseModel):
    """طلب البحث عن لاعب"""
    query: str = Field(..., min_length=2, max_length=100, description="اسم اللاعب للبحث")
    limit: int = Field(default=10, ge=1, le=50, description="عدد النتائج المطلوبة")

class PlayerInfo(BaseModel):
    """معلومات لاعب أساسية"""
    player: str = Field(description="اسم اللاعب")
    squad: str = Field(description="الفريق الحالي")
    comp: str = Field(description="الدوري")
    pos: str = Field(description="المركز")
    age: int = Field(description="العمر")
    nation: str = Field(description="الجنسية")
    born: Optional[str] = Field(default=None, description="تاريخ الميلاد")

class PlayerStats(BaseModel):
    """إحصائيات لاعب حسب المركز"""
    # عامة
    matches_played: Optional[int] = Field(default=None)
    
    # للمهاجمين
    goals: Optional[float] = Field(default=None)
    assists: Optional[float] = Field(default=None)
    expected_goals: Optional[float] = Field(default=None)
    key_passes: Optional[float] = Field(default=None)
    progressive_passes: Optional[float] = Field(default=None)
    sca_p90: Optional[float] = Field(default=None)
    gca_p90: Optional[float] = Field(default=None)
    
    # للمدافعين
    tackles_won: Optional[float] = Field(default=None)
    interceptions: Optional[float] = Field(default=None)
    clearances: Optional[float] = Field(default=None)
    aerial_pct: Optional[float] = Field(default=None)
    blocks: Optional[float] = Field(default=None)
    
    # للحراس
    saves: Optional[float] = Field(default=None)
    clean_sheets: Optional[float] = Field(default=None)
    goals_against: Optional[float] = Field(default=None)

class SimilarPlayerResponse(BaseModel):
    """رد لاعب مشابه"""
    player: str
    squad: str
    pos: str
    age: int
    nation: str
    similarity_score: float = Field(description="درجة التشابه (0-1)")

class PlayerSearchResponse(BaseModel):
    """رد البحث عن اللاعبين"""
    query: str
    results: List[PlayerInfo]
    similar_players: Optional[List[SimilarPlayerResponse]] = None