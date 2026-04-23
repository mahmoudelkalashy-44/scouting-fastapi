# app/routers/predictions.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import logging

from app.models.prediction import (
    PredictionRequest, PredictionResponse, 
    MultiMetricPredictionRequest, MultiMetricPredictionResponse
)
from app.services.model_loader import model_loader
from app.services.predictor import PlayerPredictor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/single", response_model=PredictionResponse, summary="🔮 تنبؤ بمقياس واحد")
async def predict_single_metric(
    request: PredictionRequest,
    models: dict = Depends(lambda: model_loader.load_all())
):
    """
    التنبؤ بأداء لاعب لمقياس محدد في الموسم القادم.
    
    - **player_name**: اسم اللاعب
    - **metric**: المقياس المطلوب (goals, assists, tackles, ...)
    
    النظام هيختار النموذج المناسب أوتوماتيك بناءً على مركز اللاعب:
    - GK: Random Forest (Saves, Clean Sheets, Goals Against)
    - DF: XGBoost/LSTM (Tackles, Interceptions, Clearances...)
    - MF: GRU/Gradient Boosting (Goals, Assists, Key Passes...)
    - FW: GRU (Goals, Assists)
    """
    try:
        predictor = PlayerPredictor(models)
        result = predictor.predict(request.player_name, request.metric)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"❌ Could not predict '{request.metric}' for player '{request.player_name}'"
            )
        
        return PredictionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="⚠️ Error generating prediction"
        )

@router.post("/multi", response_model=MultiMetricPredictionResponse, summary="📈 تنبؤ بعدة مقاييس")
async def predict_multi_metrics(
    request: MultiMetricPredictionRequest,
    models: dict = Depends(lambda: model_loader.load_all())
):
    """
    التنبؤ بأداء لاعب لعدة مقاييس دفعة واحدة.
    
    مفيد لعرض لوحة تحكم شاملة لأداء اللاعب المتوقع.
    """
    try:
        predictor = PlayerPredictor(models)
        predictions = {}
        
        for metric in request.metrics:
            result = predictor.predict(request.player_name, metric)
            if result:
                predictions[metric] = PredictionResponse(**result)
        
        if not predictions:
            raise HTTPException(
                status_code=404,
                detail=f"❌ Could not predict any metrics for player '{request.player_name}'"
            )
        
        # أخذ بيانات اللاعب من أول نتيجة
        first_result = list(predictions.values())[0]
        
        return MultiMetricPredictionResponse(
            player=first_result.player,
            predictions=predictions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Multi-prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="⚠️ Error generating multi-metric predictions"
        )