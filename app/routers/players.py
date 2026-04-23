# app/routers/players.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging
import pandas as pd

from app.models.player import (
    PlayerSearchRequest, PlayerSearchResponse, PlayerInfo, 
    SimilarPlayerResponse, PlayerStats
)
from app.services.model_loader import model_loader
from app.services.similarity import SimilarityCalculator

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/search", response_model=PlayerSearchResponse, summary="🔍 البحث عن لاعبين")
async def search_players(
    request: PlayerSearchRequest,
    models: dict = Depends(lambda: model_loader.load_all())
):
    """
    البحث عن لاعبين باسمهم وإرجاع معلوماتهم الأساسية + 10 لاعبين مشابهين.
    
    - **query**: اسم اللاعب للبحث
    - **limit**: عدد النتائج المطلوبة (1-50)
    """
    try:
        player_stats_df = models['player_stats_df']
        
        # البحث عن اللاعبين
        query_lower = request.query.lower()
        results_mask = player_stats_df['Player'].str.contains(
            query_lower, case=False, na=False
        )
        
        if not results_mask.any():
            raise HTTPException(
                status_code=404,
                detail=f"❌ No players found matching '{request.query}'"
            )
        
        results_df = player_stats_df[results_mask].head(request.limit)
        
        # بناء قائمة النتائج
        results = []
        for _, row in results_df.iterrows():
            results.append(PlayerInfo(
                player=row['Player'],
                squad=row['Squad'],
                comp=row['Comp'],
                pos=row['Pos'],
                age=int(row['Age']),
                nation=row['Nation'],
                born=str(row['Born']) if pd.notna(row.get('Born')) else None
            ))
        
        # حساب اللاعبين المشابهين للاعب الأول (لو في نتيجة واحدة)
        similar_players = None
        if len(results) == 1:
            try:
                sim_calc = SimilarityCalculator(player_stats_df)
                similar = sim_calc.find_similar(request.query, limit=10)
                similar_players = [SimilarPlayerResponse(**s) for s in similar]
            except Exception as e:
                logger.warning(f"⚠️ Could not calculate similar players: {e}")
        
        return PlayerSearchResponse(
            query=request.query,
            results=results,
            similar_players=similar_players
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="⚠️ Error searching for players"
        )

@router.get("/{player_name}/stats", response_model=PlayerStats, summary="📊 إحصائيات لاعب")
async def get_player_stats(
    player_name: str,
    models: dict = Depends(lambda: model_loader.load_all())
):
    """
    إرجاع الإحصائيات التفصيلية للاعب حسب مركزه.
    
    - **player_name**: اسم اللاعب
    """
    try:
        predict_df = models['predict_df']
        
        # البحث عن اللاعب
        player_data = predict_df[
            predict_df['player'].str.lower() == player_name.lower()
        ]
        if player_data.empty:
            player_data = predict_df[
                predict_df['player'].str.contains(player_name, case=False, na=False)
            ]
        
        if player_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"❌ Player '{player_name}' not found"
            )
        
        p = player_data.iloc[0]
        pos = str(p['pos'])
        
        # بناء الإحصائيات حسب المركز
        stats = PlayerStats(matches_played=int(p.get('Matches Played', 0)))
        
        if pos == 'GK':
            stats.saves = float(p.get('Saves', 0))
            stats.clean_sheets = float(p.get('Clean Sheets', 0))
            stats.goals_against = float(p.get('Goals Against', 0))
        elif pos in ['DF', 'DF,MF', 'DF,FW']:
            stats.tackles_won = float(p.get('Tackles Won', 0))
            stats.interceptions = float(p.get('Interceptions', 0))
            stats.clearances = float(p.get('Clearances', 0))
            stats.aerial_pct = float(p.get('% Aerial Duels won', 0))
            stats.blocks = float(p.get('Shots blocked', 0))
        elif pos in ['MF', 'MF,DF', 'MF,FW']:
            stats.goals = float(p.get('Goals', 0))
            stats.assists = float(p.get('Assists', 0))
            stats.key_passes = float(p.get('Key passes', 0))
            stats.progressive_passes = float(p.get('Progressive Passes', 0))
            stats.sca_p90 = float(p.get('Shot creating actions p 90', 0))
            stats.gca_p90 = float(p.get('Goal creating actions p 90', 0))
        else:  # FW
            stats.goals = float(p.get('Goals', 0))
            stats.assists = float(p.get('Assists', 0))
            stats.expected_goals = float(p.get('Expected Goals', 0))
            stats.key_passes = float(p.get('Key passes', 0))
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Stats error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="⚠️ Error fetching player stats"
        )