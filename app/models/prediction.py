# app/models/prediction.py
from pydantic import BaseModel, Field
from typing import Optional, Literal

MetricType = Literal[
    "goals", "assists", "tackles", "interceptions", "clearances", 
    "aerial_pct", "blocks", "saves", "clean_sheets", "goals_against",
    "key_passes", "progressive_passes", "sca_p90", "gca_p90"
]

class PredictionRequest(BaseModel):
    """طلب التنبؤ بأداء لاعب"""
    player_name: str = Field(..., min_length=2, description="اسم اللاعب")
    metric: MetricType = Field(default="goals", description="المقياس المطلوب للتنبؤ")

class PredictionResponse(BaseModel):
    """رد التنبؤ بأداء اللاعب"""
    player: str = Field(description="اسم اللاعب")
    squad: str = Field(description="الفريق")
    pos: str = Field(description="المركز")
    age: int = Field(description="العمر")
    pos_type: Literal["fw", "mf", "df", "gk"] = Field(description="نوع المركز")
    
    # البيانات الفعلية
    actual_value: float = Field(description="قيمة المقياس في 2023/24")
    
    # التنبؤ
    predicted_value: float = Field(description="القيمة المتوقعة في 2024/25")
    delta: float = Field(description="الفرق بين المتوقع والفعلي")
    
    # جودة التنبؤ
    reliability: Literal["🟢 High", "🟡 Medium", "🔴 Low"] = Field(
        description="مستوى الثقة في التنبؤ"
    )
    num_seasons: int = Field(description="عدد المواسم المستخدمة في التحليل")
    
    # رسالة إضافية
    message: Optional[str] = Field(default=None, description="ملاحظة إضافية")

class MultiMetricPredictionRequest(BaseModel):
    """طلب التنبؤ بعدة مقاييس دفعة واحدة"""
    player_name: str = Field(..., min_length=2, description="اسم اللاعب")
    metrics: list[MetricType] = Field(..., min_length=1, description="قائمة المقاييس المطلوبة")

class MultiMetricPredictionResponse(BaseModel):
    """رد التنبؤ بعدة مقاييس"""
    player: str
    predictions: dict[str, PredictionResponse]