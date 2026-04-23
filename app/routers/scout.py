# app/routers/scout.py
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
import logging

from app.models.scout_report import ScoutReportRequest, ScoutReportResponse
from app.services.model_loader import model_loader
from app.services.scout_ai import ScoutAI
from app.services.similarity import SimilarityCalculator

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/report", response_model=ScoutReportResponse, summary="🤖 إنشاء تقرير كشفي ذكي")
async def generate_scout_report(
    request: ScoutReportRequest,
    models: dict = Depends(lambda: model_loader.load_all())
):
    """
    إنشاء تقرير كشفي ذكي باستخدام الذكاء الاصطناعي.
    
    يحلل لاعبين مشابهين ويوصي بالأفضل بناءً على متطلبات فريقك.
    
    ⚠️ يتطلب مفتاح Groq API صالح (يمكن تمريره في الطلب أو وضعه في .env)
    """
    try:
        player_stats_df = models['player_stats_df']
        
        # 1. إيجاد لاعبين مشابهين
        sim_calc = SimilarityCalculator(player_stats_df)
        similar_players = sim_calc.find_similar(request.base_player, limit=10)
        
        if not similar_players:
            raise HTTPException(
                status_code=404,
                detail=f"❌ Could not find similar players for '{request.base_player}'"
            )
        
        # 2. تحضير البيانات للتقرير
        similar_df = pd.DataFrame(similar_players)
        similar_df_str = similar_df.to_string(index=False)
        
        # 3. توليد التقرير بالذكاء الاصطناعي
        api_key = request.groq_api_key or models.get('groq_api_key')
        scout_ai = ScoutAI(api_key=api_key)
        
        report_result = scout_ai.generate_report(
            similar_players_df_str=similar_df_str,
            game_style=request.game_style,
            player_experience=request.player_experience,
            league=request.preferred_league,
            formation=request.ideal_formation,
            skills=request.key_skills
        )
        
        return ScoutReportResponse(
            base_player=request.base_player,
            similar_players_analyzed=len(similar_players),
            report_text=report_result.get('report_text', ''),
            recommended_player=report_result.get('recommended_player'),
            generation_time_ms=report_result.get('generation_time_ms'),
            model_used=report_result.get('model_used', 'llama-3.3-70b-versatile')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Scout report error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"⚠️ Error generating scout report: {str(e)}"
        )