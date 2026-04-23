# app/routers/injuries.py
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.models.injury import InjuryRiskRequest, InjuryRiskResponse
from app.services.model_loader import model_loader
from app.services.injury_assessor import InjuryAssessor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/risk", response_model=InjuryRiskResponse, summary="🏥 تقييم خطر الإصابة")
async def assess_injury_risk(
    request: InjuryRiskRequest,
    models: dict = Depends(lambda: model_loader.load_all())
):
    """
    تقييم احتمالية إصابة اللاعب في الموسم القادم.
    
    يستخدم نموذج هجين (LSTM + قواعد مجال الخبرة) مدرب على +7,000 موسم-لاعب.
    
    يرجع:
    - نسبة خطر الإصابة (0-100%)
    - تصنيف الخطر (🔴 High / 🟡 Medium / 🟢 Low)
    - إحصائيات الإصابات السابقة
    - توصية عملية مبنية على مستوى الخطر
    """
    try:
        assessor = InjuryAssessor(models)
        result = assessor.assess(request.player_name)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"❌ Could not assess injury risk for player '{request.player_name}'"
            )
        
        return InjuryRiskResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Injury risk error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="⚠️ Error assessing injury risk"
        )