# app/models/injury.py
from pydantic import BaseModel, Field

class InjuryRiskRequest(BaseModel):
    """طلب تقييم خطر إصابة لاعب"""
    player_name: str = Field(..., min_length=2, description="اسم اللاعب")

class InjuryRiskResponse(BaseModel):
    """رد تقييم خطر الإصابة"""
    player: str = Field(description="اسم اللاعب")
    
    # نتيجة التقييم
    injury_risk_pct: float = Field(description="نسبة خطر الإصابة (0-100)", ge=0, le=100)
    risk_label: str = Field(description="تصنيف الخطر", 
                           pattern=r"^(🔴 High Risk|🟡 Medium Risk|🟢 Low Risk)$")
    
    # إحصائيات الإصابات
    last1_injuries: int = Field(description="عدد الإصابات في آخر موسم", ge=0)
    last1_days_missed: int = Field(description="أيام الغياب في آخر موسم", ge=0)
    career_injuries: int = Field(description="إجمالي الإصابات في المسيرة", ge=0)
    career_days_missed: int = Field(description="إجمالي أيام الغياب", ge=0)
    avg_days_per_injury: float = Field(description="متوسط أيام الغياب لكل إصابة", ge=0)
    
    # تفاصيل إضافية
    had_very_serious_injury: bool = Field(description="هل عانى من إصابة خطيرة (+60 يوم)")
    consecutive_injured_seasons: int = Field(description="مواسم متتالية بها إصابات")
    dominant_injury_type: str = Field(description="نوع الإصابة الأكثر شيوعاً")
    
    # هل يوجد بيانات إصابات؟
    has_injury_data: bool = Field(description="هل توجد بيانات إصابات لهذا اللاعب")
    
    # توصية عملية
    recommendation: str = Field(description="نصيحة مبنية على مستوى الخطر")